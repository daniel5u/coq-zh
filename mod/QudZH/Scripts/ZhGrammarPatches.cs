using System;
using HarmonyLib;
using XRL.Language;
using XRL.World;

/// <summary>Removes English inflection only for CJK text while zh is selected.</summary>
[HarmonyPatch]
public static class ZhGrammarPatches
{
    private static bool IsChinese(string value) =>
        LanguageLoader.ActiveLanguage == "zh" && ZhText.ContainsCjk(value);

    [HarmonyPatch(typeof(Grammar), nameof(Grammar.Pluralize), new Type[] { typeof(string) })]
    [HarmonyPrefix]
    private static bool PluralizePrefix(string word, ref string __result)
    {
        if (!IsChinese(word)) return true;
        __result = word;
        return false;
    }

    [HarmonyPatch(typeof(Grammar), nameof(Grammar.ThirdPerson), new Type[] { typeof(string), typeof(bool) })]
    [HarmonyPrefix]
    private static bool ThirdPersonPrefix(string word, bool PrependSpace, ref string __result)
    {
        if (!IsChinese(word)) return true;
        __result = word; // Chinese: no space between subject and verb
        return false;
    }

    [HarmonyPatch(typeof(Grammar), nameof(Grammar.MakePossessive), new Type[] { typeof(string) })]
    [HarmonyPrefix]
    private static bool MakePossessivePrefix(string word, ref string __result)
    {
        if (!IsChinese(word)) return true;
        __result = word + "的";
        return false;
    }

    [HarmonyPatch(typeof(GameObject), nameof(GameObject.GetVerb), new Type[]
    {
        typeof(string), typeof(bool), typeof(bool), typeof(bool), typeof(bool), typeof(bool)
    })]
    [HarmonyPrefix]
    private static bool GetVerbPrefix(GameObject __instance, string Verb, bool PrependSpace,
        ref string __result)
    {
        if (!IsChinese(Verb)) return true;
        __result = Verb; // Chinese: no space between subject and verb
        return false;
    }
}
