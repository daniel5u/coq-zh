using System;
using HarmonyLib;
using XRL.World.Conversations;
using XRL.World.Conversations.Parts;

// Water ritual status is appended after the translated dialogue has been built.
// Localize that complete panel while its multiline markup is still intact.
[HarmonyPatch(typeof(WaterRitual), nameof(WaterRitual.HandleEvent),
    new Type[] { typeof(DisplayTextEvent) })]
public static class ZhWaterRitualStatusPatch
{
    private const string Separator = "\n\n{{C|-----}}\n";

    [HarmonyPrefix]
    public static void Prefix(DisplayTextEvent E, out int __state)
    {
        __state = ZhRuntime.Active ? E.Text.Length : -1;
    }

    [HarmonyPostfix]
    public static void Postfix(DisplayTextEvent E, int __state)
    {
        if (__state < 0 || !ZhRuntime.Active || E.Text.Length <= __state) return;
        string appended = E.Text.ToString(__state, E.Text.Length - __state);
        if (!appended.StartsWith(Separator, StringComparison.Ordinal)) return;
        string panel = appended.Substring(Separator.Length);
        string translated = ZhRuntime.Localize(panel);
        if (translated != panel)
            E.Text.Remove(__state, E.Text.Length - __state).Append(Separator).Append(translated);
    }
}

// GetTag is a display-only return value. Translate it before Choice.GetDisplayText
// joins it to dialogue; never alter the choice ID, target, cost or availability.
[HarmonyPatch(typeof(Choice), nameof(Choice.GetTag))]
public static class ZhWaterRitualTagPatch
{
    [HarmonyPostfix]
    public static void Postfix(ref string __result)
    {
        if (ZhRuntime.Active) __result = ZhRuntime.Localize(__result);
    }
}
