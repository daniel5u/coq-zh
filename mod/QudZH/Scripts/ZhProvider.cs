using System;
using System.Collections.Generic;
using System.Globalization;
using ConsoleLib.Console;
using XRL.Language;
using XRL.World;

[LanguageProvider("zh")]
public sealed class ZhProvider : TranslatorBase
{
    public override void NextPossibleLineBreakIndex(ReadOnlySpan<char> span, int startIndex, out int breakBeforeIndex, out bool replaceIfBroken)
    {
        breakBeforeIndex = ZhText.FindNextLineBreak(span, startIndex, out replaceIfBroken);
    }

    public override string MakeAndList(IReadOnlyList<string> list, MakeAndListParams p = default(MakeAndListParams)) => ZhText.JoinAnd(list);
    public override string MakeOrList(IReadOnlyList<string> list, MakeOrListParams p = default(MakeOrListParams)) => ZhText.JoinOr(list);
    public override string MakeCommaList(IReadOnlyList<string> list) => ZhText.JoinComma(list);

    public override void ExtractArticle(ref string name, out string article)
    {
        article = string.Empty;
        if (string.IsNullOrEmpty(name)) return;
        string[] prefixes = { "the ", "a ", "an ", "some " };
        foreach (string prefix in prefixes)
        {
            if (name.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
            {
                name = name.Substring(prefix.Length);
                return;
            }
        }
    }

    public override void ExtractAndSetDefiniteArticle(GameObject obj, string name)
    {
        ExtractArticle(ref name, out _);
        obj.GiveProperName(name, Force: true);
        obj.SetStringProperty("IndefiniteArticle", string.Empty);
        obj.SetStringProperty("DefiniteArticle", string.Empty);
        obj.SetStringProperty("OverrideIArticle", string.Empty);
        obj.SetStringProperty("Gender", "nonspecific");
        obj.SetGender("nonspecific");
    }

    public override string DefiniteArticle(DefiniteArticleParams p) => string.Empty;
    public override string IndefiniteArticle(IndefiniteArticleParams p) => string.Empty;
    public override void AddArticle(AddArticleParams p) { }

    public override string Cardinal(long num) => ZhText.Cardinal(num);
    public override string CardinalNo(long num) => ZhText.CardinalNo(num);
    public override string Ordinal(long num) => ZhText.Ordinal(num);
    public override string OrdinalWithDigits(long num) => ZhText.OrdinalWithDigits(num);
    public override string Multiplicative(long num) => ZhText.Multiplicative(num);

    public override CultureInfo GetCultureInfo() => CultureInfo.GetCultureInfo("zh-CN");
    public override bool IsWordCharacter(char c) => ZhText.IsCjk(c) || base.IsWordCharacter(c);

    public override string GameObjectDisplayName(GameObject go, out bool adjunctNounActive, GameObjectDisplayNameParams p)
    {
        string name = base.GameObjectDisplayName(go, out adjunctNounActive, p);
        return ZhText.RemoveCjkWordSpaces(name);
    }
}
