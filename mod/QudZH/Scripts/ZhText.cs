using System;
using System.Collections.Generic;
using System.Text;

/// <summary>Pure Simplified Chinese formatting helpers shared by the provider and checks.</summary>
public static class ZhText
{
    private static readonly char[] Digits = { '零', '一', '二', '三', '四', '五', '六', '七', '八', '九' };
    private static readonly string[] GroupUnits = { "", "万", "亿", "兆", "京" };
    private static readonly string[] SmallUnits = { "", "十", "百", "千" };

    public static bool IsCjk(char c)
    {
        return (c >= '\u2E80' && c <= '\u2FFF') || (c >= '\u3000' && c <= '\u30FF') ||
               (c >= '\u3100' && c <= '\u312F') || (c >= '\u31A0' && c <= '\u31BF') ||
               (c >= '\u31F0' && c <= '\u31FF') || (c >= '\u3400' && c <= '\u4DBF') ||
               (c >= '\u4E00' && c <= '\u9FFF') || (c >= '\uF900' && c <= '\uFAFF') ||
               (c >= '\uFF01' && c <= '\uFF60') || (c >= '\uFFE0' && c <= '\uFFE6') ||
               (c >= '\uAC00' && c <= '\uD7AF') || (c >= '\u1100' && c <= '\u11FF');
    }

    public static bool ContainsCjk(string text)
    {
        if (string.IsNullOrEmpty(text)) return false;
        for (int i = 0; i < text.Length; i++) if (IsCjk(text[i])) return true;
        return false;
    }

    public static bool IsOpeningPunctuation(char c) => "（「『“‘（([{〈《【〔〖〘〚".IndexOf(c) >= 0;
    public static bool IsClosingPunctuation(char c) => "，。！？；：、）」』”’…—」』】〕〉》〗〙〛)]}".IndexOf(c) >= 0;

    /// <summary>Returns the next safe wrap boundary. -1 means no further break is available.</summary>
    public static int FindNextLineBreak(ReadOnlySpan<char> span, int startIndex, out bool replaceIfBroken)
    {
        replaceIfBroken = false;
        int i = Math.Max(0, startIndex);
        bool first = true;
        while (i < span.Length)
        {
            char c = span[i];

            // Match the base provider's spaces and explicit newline behavior.
            if (!first && (c == ' ' || c == '\n'))
            {
                replaceIfBroken = c == ' ';
                return i;
            }

            // A markup expression is one unbreakable control sequence, including nested braces.
            if (c == '{' && i + 1 < span.Length && span[i + 1] == '{')
            {
                int end = FindMarkupEnd(span, i);
                if (end < 0) return -1;
                i = end;
                first = false;
                continue;
            }

            // Terminal foreground/background codes are two-character controls.
            if ((c == '&' || c == '^') && i + 1 < span.Length)
            {
                i += 2;
                first = false;
                continue;
            }

            // A boundary is reported before the next character. Do not strand closing
            // punctuation or start a line with a continuation after opening punctuation.
            if (i > startIndex && IsCjk(span[i - 1]) && IsCjk(c) &&
                !IsClosingPunctuation(c) && !IsOpeningPunctuation(span[i - 1]))
            {
                return i;
            }
            first = false;
            i++;
        }
        return -1;
    }

    private static int FindMarkupEnd(ReadOnlySpan<char> span, int start)
    {
        int depth = 0;
        for (int i = start; i + 1 < span.Length; i++)
        {
            if (span[i] == '{' && span[i + 1] == '{') { depth++; i++; }
            else if (span[i] == '}' && span[i + 1] == '}')
            {
                depth--; i++;
                if (depth == 0) return i + 1;
            }
        }
        return -1;
    }

    public static string Cardinal(long value)
    {
        if (value == 0) return "零";
        bool negative = value < 0;
        ulong n = negative ? (ulong)(-(value + 1)) + 1UL : (ulong)value;
        var groups = new List<int>(5);
        while (n > 0) { groups.Add((int)(n % 10000)); n /= 10000; }
        var result = new StringBuilder();
        if (negative) result.Append('负');
        bool pendingZero = false;
        for (int g = groups.Count - 1; g >= 0; g--)
        {
            int group = groups[g];
            if (group == 0) { if (result.Length > (negative ? 1 : 0)) pendingZero = true; continue; }
            if (result.Length > (negative ? 1 : 0) && (pendingZero || group < 1000)) result.Append('零');
            pendingZero = false;
            AppendGroup(result, group, result.Length <= (negative ? 1 : 0));
            result.Append(GroupUnits[g]);
        }
        return result.ToString();
    }

    private static void AppendGroup(StringBuilder result, int value, bool omitLeadingOneForTen)
    {
        omitLeadingOneForTen = omitLeadingOneForTen && value >= 10 && value < 20;
        int divisor = 1000;
        bool zero = false;
        bool emitted = false;
        while (divisor > 0)
        {
            int digit = value / divisor;
            value %= divisor;
            if (digit == 0) { if (emitted && value > 0) zero = true; }
            else
            {
                if (zero) result.Append('零');
                zero = false;
                if (!(omitLeadingOneForTen && digit == 1 && divisor == 10)) result.Append(Digits[digit]);
                result.Append(SmallUnits[(int)Math.Log10(divisor)]);
                emitted = true;
            }
            divisor /= 10;
        }
    }

    public static string CardinalNo(long value) => value == 0 ? "无" : Cardinal(value);
    public static string Ordinal(long value) => "第" + Cardinal(value);
    public static string OrdinalWithDigits(long value) => "第" + Cardinal(value);
    public static string Multiplicative(long value)
    {
        if (value == 0) return "零次";
        if (value == 1) return "一次";
        if (value == 2) return "两次";
        return Cardinal(value) + "次";
    }

    public static string JoinComma(IReadOnlyList<string> items) => Join(items, "、");
    public static string JoinAnd(IReadOnlyList<string> items)
    {
        if (items == null || items.Count == 0) return string.Empty;
        if (items.Count == 1) return items[0];
        if (items.Count == 2) return items[0] + "和" + items[1];
        return JoinRange(items, items.Count - 1, "、") + "和" + items[items.Count - 1];
    }
    public static string JoinOr(IReadOnlyList<string> items)
    {
        if (items == null || items.Count == 0) return string.Empty;
        if (items.Count == 1) return items[0];
        return JoinRange(items, items.Count - 1, "、") + "或" + items[items.Count - 1];
    }
    private static string Join(IReadOnlyList<string> items, string separator) => JoinRange(items, items == null ? 0 : items.Count, separator);
    private static string JoinRange(IReadOnlyList<string> items, int count, string separator)
    {
        if (items == null || count == 0) return string.Empty;
        var result = new StringBuilder();
        for (int i = 0; i < count; i++) { if (i > 0) result.Append(separator); result.Append(items[i]); }
        return result.ToString();
    }

    /// <summary>Drop accidental spaces between adjacent CJK text while preserving formatting controls.</summary>
    public static string RemoveCjkWordSpaces(string text)
    {
        if (string.IsNullOrEmpty(text)) return text;
        var result = new StringBuilder(text.Length);
        for (int i = 0; i < text.Length; i++)
        {
            if (text[i] == '{' && i + 1 < text.Length && text[i + 1] == '{')
            {
                int end = text.IndexOf("}}", i + 2, StringComparison.Ordinal);
                if (end >= 0) { result.Append(text, i, end + 2 - i); i = end + 1; continue; }
            }
            if ((text[i] == '&' || text[i] == '^') && i + 1 < text.Length)
            {
                result.Append(text[i]).Append(text[++i]);
                continue;
            }
            if (text[i] == ' ' && result.Length > 0 && i + 1 < text.Length && IsCjk(result[result.Length - 1]) && IsCjk(text[i + 1])) continue;
            result.Append(text[i]);
        }
        return result.ToString();
    }
}
