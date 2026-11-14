using System.Collections.Generic;
using System.Globalization;
using XRL.Language;
using XRL.World;

// Build this class into an assembly loaded by the mod. LanguageLoader scans
// ModManager.ActiveTypes for LanguageProviderAttribute matching the active code.
[LanguageProvider("zh")]
public sealed class ZhProvider : TranslatorBase
{
    public override CultureInfo GetCultureInfo() => CultureInfo.GetCultureInfo("zh-CN");

    // Chinese does not inflect English-style a/an/the. This also means item
    // names need not carry articles. Review callers that treat empty as a cue.
    public override string DefiniteArticle(DefiniteArticleParams p) => string.Empty;
    public override string IndefiniteArticle(IndefiniteArticleParams p) => string.Empty;

    // Keep supplied translated names intact; there is no article token to peel.
    public override void ExtractArticle(ref string name, out string article)
    {
        article = string.Empty;
    }

    // No English third-person singular grammar is needed for Chinese message
    // templates that use these Translator APIs. GameObject.GetVerb itself is
    // separate and still needs call-site rewrites or a Harmony patch.
    public override string MakeCommaList(IReadOnlyList<string> list) => Join(list, "、");
    public override string MakeAndList(IReadOnlyList<string> list,
        Translator.Provider.MakeAndListParams p = default(Translator.Provider.MakeAndListParams))
        => Join(list, "、");
    public override string MakeOrList(IReadOnlyList<string> list,
        Translator.Provider.MakeOrListParams p = default(Translator.Provider.MakeOrListParams))
        => Join(list, "或");

    private static string Join(IReadOnlyList<string> list, string separator)
    {
        if (list == null || list.Count == 0) return string.Empty;
        if (list.Count == 1) return list[0];
        var result = new System.Text.StringBuilder();
        for (int i = 0; i < list.Count; i++)
        {
            if (i > 0) result.Append(separator);
            result.Append(list[i]);
        }
        return result.ToString();
    }
}
