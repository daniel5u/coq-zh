using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using HarmonyLib;
using Qud.UI;
using XRL;
using XRL.Language;
using XRL.Messages;
using XRL.UI;

/// <summary>
/// Runtime localisation of text that the game builds in C# without going through the
/// string tables (mutation level texts, effect details, ...), plus removal of stray
/// English articles ("the"/"a"/"an") that end up directly in front of Chinese text.
///
/// Data: runtime_strings.tsv in the mod folder, one "English<TAB>Chinese" pair per line.
///   '#'  in a template matches any number / dice expression (25, -3, 1.5, 1d6, 2d3+2);
///        in the Chinese side the numbers are re-inserted in order ('#') or by index ('#1', '#2').
///   {0}, {1} ... match arbitrary text and are re-inserted by index.
/// Matching is done line by line ('\n'), after an exact whole-string lookup.
/// </summary>
public static class ZhRuntime
{
    private const string NumPattern = @"[+-]?\d+(?:\.\d+)?(?:d\d+(?:[+-]\d+)?)?";
    private static readonly Regex NumRx = new Regex(@"(?<![A-Za-z#])" + NumPattern, RegexOptions.Compiled);
    private static readonly Regex AsciiLetter = new Regex("[A-Za-z]", RegexOptions.Compiled);
    private static readonly Regex LeafMarkup = new Regex(@"\{\{[^|{}]+\|[^{}]*\}\}", RegexOptions.Compiled);
    private static readonly Regex Cjk = new Regex(@"[㐀-鿿]", RegexOptions.Compiled);
    // Mutation stat arguments and the character-summary body fallback bypass
    // localization tables. Translate visible nouns without changing blueprint IDs.
    private static readonly Regex DisplayNoun = new Regex(
        @"(?<![A-Za-z0-9_])(?:beak|horns|humanoid)(?![A-Za-z0-9_])", RegexOptions.Compiled | RegexOptions.IgnoreCase);
    private static readonly Regex StrayArticle = new Regex(
        @"(?<![A-Za-z])(?:[Tt]he|[Aa]n?|[Ss]ome)\s+(?=(?:\{\{[^|{}]*\||&[A-Za-z]|\^[A-Za-z])*[㐀-鿿])",
        RegexOptions.Compiled);

    private static Dictionary<string, string> exact;
    private static Dictionary<string, string> normalized;
    private static List<KeyValuePair<Regex, string>> templates;
    private static readonly Dictionary<string, string> cache = new Dictionary<string, string>(4096);
    private static bool loaded;

    public static bool Active => LanguageLoader.ActiveLanguage == "zh";

    private static void Load()
    {
        loaded = true;
        exact = new Dictionary<string, string>(StringComparer.Ordinal);
        normalized = new Dictionary<string, string>(StringComparer.Ordinal);
        templates = new List<KeyValuePair<Regex, string>>();
        var specificity = new Dictionary<Regex, int>();
        var numericCaptures = new Dictionary<Regex, int>();
        try
        {
            ModInfo mod = ModManager.GetMod("QudZH");
            string path = mod == null ? null : Path.Combine(mod.Path, "runtime_strings.tsv");
            if (path == null || !File.Exists(path)) return;
            foreach (string raw in File.ReadAllLines(path, Encoding.UTF8))
            {
                if (raw.Length == 0 || raw[0] == '﻿' && raw.Length == 1) continue;
                int tab = raw.IndexOf('\t');
                if (tab <= 0) continue;
                string en = Unescape(raw.Substring(0, tab).TrimStart('﻿'));
                string zh = Unescape(raw.Substring(tab + 1));
                if (en.IndexOf('{') >= 0 && Regex.IsMatch(en, @"\{\d+\}"))
                {
                    string literal = Regex.Replace(en, @"\{\{[^|{}]*\||\}\}|[&^][A-Za-z]", "");
                    literal = Regex.Replace(literal, @"\{\d+\}|#", "");
                    // A capture-only pattern matches its own input again when
                    // captures are translated recursively. It has no meaning
                    // that can safely identify a display message either.
                    if (!AsciiLetter.IsMatch(literal)) continue;
                    Regex pattern = BuildRegex(en);
                    templates.Add(new KeyValuePair<Regex, string>(pattern, zh));
                    specificity[pattern] = Regex.Replace(en, @"\{\d+\}|#", "").Length;
                    numericCaptures[pattern] = en.Length - en.Replace("#", "").Length;
                }
                else if (en.IndexOf('#') >= 0)
                {
                    normalized[en] = zh;
                }
                else
                {
                    exact[en] = zh;
                }
            }
            // A generic capture must not swallow a longer, known phrase (e.g.
            // "Your X is Y" versus "Your base X is Y, modified to Z").
            templates.Sort((a, b) =>
            {
                int fixedText = specificity[b.Key].CompareTo(specificity[a.Key]);
                if (fixedText != 0) return fixedText;
                // A numeric capture is narrower than arbitrary text. List.Sort
                // is unstable, so equal templates must also have a fixed order.
                int numbers = numericCaptures[b.Key].CompareTo(numericCaptures[a.Key]);
                return numbers != 0 ? numbers : StringComparer.Ordinal.Compare(a.Key.ToString(), b.Key.ToString());
            });
        }
        catch (Exception ex)
        {
            MetricsManager.LogError("QudZH runtime_strings load failed", ex);
        }
    }

    private static string Unescape(string s) => s.Replace("\\n", "\n").Replace("\\t", "\t");

    private static Regex BuildRegex(string en)
    {
        var sb = new StringBuilder("^");
        int i = 0;
        while (i < en.Length)
        {
            char c = en[i];
            if (c == '#')
            {
                sb.Append('(').Append(NumPattern).Append(')');
                i++;
                continue;
            }
            if (c == '{')
            {
                int close = en.IndexOf('}', i);
                if (close > i && int.TryParse(en.Substring(i + 1, close - i - 1), out int idx))
                {
                    sb.Append("(?<t").Append(idx).Append('>')
                        .Append(en.IndexOf('\n') >= 0 ? @"[\s\S]+?" : ".+?").Append(')');
                    i = close + 1;
                    continue;
                }
            }
            sb.Append(Regex.Escape(c.ToString()));
            i++;
        }
        sb.Append('$');
        return new Regex(sb.ToString(), RegexOptions.Compiled);
    }

    /// <summary>Main entry: localise a whole display string.</summary>
    public static string Localize(string s)
    {
        if (s == null || s.Length == 0 || !Active) return s;
        if (!AsciiLetter.IsMatch(s)) return s;
        if (cache.TryGetValue(s, out string hit)) return hit;
        if (!loaded) Load();
        string result = Translate(s);
        // Nested UI rows contain complete colored labels (item counts, mutation
        // notes). Translate each leaf as display text, preserving markup IDs.
        if (result.IndexOf("{{", StringComparison.Ordinal) >= 0)
            result = LeafMarkup.Replace(result, m => Translate(m.Value));
        result = LocalizeDisplayNouns(result);
        if (Cjk.IsMatch(result)) result = StrayArticle.Replace(result, "");
        if (cache.Count > 20000) cache.Clear();
        cache[s] = result;
        return result;
    }

    private static string LocalizeDisplayNouns(string text)
    {
        // Restrict fallback to labels and already localized text. Whole English
        // sentences still go through the template bank, avoiding partial prose.
        string plain = Regex.Replace(text, @"\{\{[^|{}]*\||\}\}|&[A-Za-z]|\^[A-Za-z]", "");
        if (!DisplayNoun.IsMatch(plain)) return text;
        if (!Cjk.IsMatch(plain) && !Regex.IsMatch(plain.Trim(), @"^(?:beak|horns|humanoid)(?:\s*\[[^\]]+\])?$", RegexOptions.IgnoreCase)) return text;
        // Preserve markup identifiers; only translate visible text segments.
        return Regex.Replace(text, @"\{\{[^|{}]*\||&[A-Za-z]|\^[A-Za-z]|(?<![A-Za-z0-9_])(?:beak|horns|humanoid)(?![A-Za-z0-9_])", m =>
            m.Value.Equals("beak", StringComparison.OrdinalIgnoreCase) ? "喙" :
            m.Value.Equals("horns", StringComparison.OrdinalIgnoreCase) ? "角" :
            m.Value.Equals("humanoid", StringComparison.OrdinalIgnoreCase) ? "人形" : m.Value,
            RegexOptions.IgnoreCase);
    }

    private static string Translate(string s)
    {
        if (exact.TryGetValue(s, out string whole)) return whole;
        string chunk = TranslateLine(s);
        if (chunk != s) return chunk;
        if (s.IndexOf('\n') < 0) return s;
        string[] lines = s.Split('\n');
        bool changed = false;
        for (int i = 0; i < lines.Length; i++)
        {
            string t = TranslateLine(lines[i]);
            if (!ReferenceEquals(t, lines[i])) { lines[i] = t; changed = true; }
        }
        return changed ? string.Join("\n", lines) : s;
    }

    private static string TranslateLine(string line)
    {
        if (line.Length == 0 || !AsciiLetter.IsMatch(line)) return line;
        string trimmed = line.Trim();
        string lead = line.Substring(0, line.IndexOf(trimmed, StringComparison.Ordinal));
        if (exact.TryGetValue(trimmed, out string ex)) return lead + ex;
        // Historical log readers prepend a marker and console color codes.
        Match logPrefix = Regex.Match(trimmed, @"^(?:[&^][A-Za-z])*[>#](?:[&^][A-Za-z]|\s)+");
        if (logPrefix.Success)
            return lead + logPrefix.Value + TranslateLine(trimmed.Substring(logPrefix.Length));
        // Menu disabled colors and message-log colors are presentation wrappers,
        // not part of the English lookup key. Keep them around translated text.
        Match colors = Regex.Match(trimmed, @"^(?:[&^][A-Za-z])+");
        if (colors.Success)
            return lead + colors.Value + TranslateLine(trimmed.Substring(colors.Length));
        if (trimmed.StartsWith("{{", StringComparison.Ordinal))
        {
            int pipe = trimmed.IndexOf('|');
            int depth = 0, end = -1;
            for (int i = 0; i < trimmed.Length - 1; i++)
            {
                if (trimmed[i] == '{' && trimmed[i + 1] == '{') { depth++; i++; }
                else if (trimmed[i] == '}' && trimmed[i + 1] == '}')
                { if (--depth == 0) { end = i + 2; break; } i++; }
            }
            if (pipe >= 2 && end == trimmed.Length)
            {
                string inner = trimmed.Substring(pipe + 1, trimmed.Length - pipe - 3);
                string translated = TranslateLine(inner);
                if (translated != inner)
                    return lead + trimmed.Substring(0, pipe + 1) + translated + "}}";
                // Some source templates include their own wrapper. If the
                // unwrapped text is unknown, still try the full template below.
            }
        }
        var nums = new List<string>();
        string key = NumRx.Replace(trimmed, m => { nums.Add(m.Value); return "#"; });
        if (nums.Count > 0 && normalized.TryGetValue(key, out string tpl)) return lead + FillNumbers(tpl, nums);
        foreach (var kv in templates)
        {
            Match m = kv.Key.Match(trimmed);
            if (!m.Success) continue;
            var caps = new List<string>();
            for (int g = 1; g < m.Groups.Count; g++)
            {
                if (!int.TryParse(m.Groups[g].Name, out _)) continue; // unnamed numeric groups only
                caps.Add(m.Groups[g].Value);
            }
            string zh = FillNumbers(kv.Value, caps);
            zh = Regex.Replace(zh, @"\{(\d+)\}", t =>
            {
                Group grp = m.Groups["t" + t.Groups[1].Value];
                return grp.Success ? TranslateLine(grp.Value) : t.Value;
            });
            return lead + zh;
        }
        return line;
    }

    private static string FillNumbers(string tpl, List<string> nums)
    {
        int next = 0;
        return Regex.Replace(tpl, @"#(\d)?", m =>
        {
            if (m.Groups[1].Success)
            {
                int i = m.Groups[1].Value[0] - '1';
                return i >= 0 && i < nums.Count ? nums[i] : m.Value;
            }
            return next < nums.Count ? nums[next++] : m.Value;
        });
    }
}

[HarmonyPatch]
public static class ZhRuntimePatches
{
    [HarmonyPatch(typeof(UITextSkin), nameof(UITextSkin.Apply))]
    [HarmonyPrefix]
    private static void UITextSkinApply(UITextSkin __instance)
    {
        if (!ZhRuntime.Active || __instance.text == null) return;
        __instance.text = ZhRuntime.Localize(__instance.text);
    }

    [HarmonyPatch(typeof(RTF), nameof(RTF.FormatToRTF), new Type[] { typeof(string), typeof(string), typeof(int), typeof(bool) })]
    [HarmonyPrefix]
    private static void FormatToRTF(ref string s)
    {
        if (ZhRuntime.Active) s = ZhRuntime.Localize(s);
    }

    [HarmonyPatch(typeof(MessageQueue), nameof(MessageQueue.AddPlayerMessage), new Type[] { typeof(string), typeof(string), typeof(bool) })]
    [HarmonyPrefix]
    private static void AddPlayerMessage(ref string Message)
    {
        if (ZhRuntime.Active) Message = ZhRuntime.Localize(Message);
    }
}

/// <summary>Translate tooltip parameter text (HUD buttons etc.) and log any tooltip that stays English, once.</summary>
[HarmonyPatch]
public static class ZhTooltipPatches
{
    private static readonly System.Collections.Generic.HashSet<string> logged = new System.Collections.Generic.HashSet<string>();

    [HarmonyPatch(typeof(ModelShark.TooltipManager), nameof(ModelShark.TooltipManager.SetTextAndSize))]
    [HarmonyPrefix]
    private static void SetTextAndSize(ModelShark.TooltipTrigger trigger)
    {
        if (!ZhRuntime.Active || trigger == null || trigger.parameterizedTextFields == null) return;
        foreach (var field in trigger.parameterizedTextFields)
        {
            if (field == null || string.IsNullOrEmpty(field.value)) continue;
            string zh = ZhRuntime.Localize(field.value);
            field.value = zh;
            if (System.Text.RegularExpressions.Regex.IsMatch(zh, "^[\\x00-\\x7F]*[A-Za-z]{3}[\\x00-\\x7F]*$") && zh.Length < 80 && logged.Add(zh))
                UnityEngine.Debug.Log("QudZH untranslated tooltip: " + zh);
        }
    }
}
