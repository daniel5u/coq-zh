using System;
using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using XRL.UI;
using XRL.Messages;
using Qud.API;
using XRL.World.Effects;

// Translate before classic-console rendering and before popups copy text to the
// log. Modern UI render hooks alone cannot cover either of these boundaries.
[HarmonyPatch]
public static class ZhPopupPatches
{
    [HarmonyTargetMethods]
    public static IEnumerable<MethodBase> Targets()
    {
        foreach (MethodInfo method in typeof(Popup).GetMethods(BindingFlags.Public | BindingFlags.Static))
        {
            foreach (ParameterInfo p in method.GetParameters())
                if (IsDisplayText(p) || IsOptions(p)) { yield return method; break; }
        }
    }

    private static bool IsDisplayText(ParameterInfo p)
    {
        if (p.ParameterType != typeof(string)) return false;
        return p.Name == "Message" || p.Name == "Title" || p.Name == "Intro" || p.Name == "Prompt";
    }

    private static bool IsOptions(ParameterInfo p) => p.Name == "Options" &&
        typeof(IReadOnlyList<string>).IsAssignableFrom(p.ParameterType) &&
        (p.ParameterType.IsAssignableFrom(typeof(string[])) || p.ParameterType.IsAssignableFrom(typeof(List<string>)));

    [HarmonyPrefix]
    public static void LocalizeArguments(MethodBase __originalMethod, object[] __args)
    {
        if (!ZhRuntime.Active) return;
        ParameterInfo[] parameters = __originalMethod.GetParameters();
        for (int i = 0; i < parameters.Length; i++)
        {
            if (IsDisplayText(parameters[i]) && __args[i] is string text)
                __args[i] = ZhRuntime.Localize(text);
            else if (IsOptions(parameters[i]) && __args[i] is IReadOnlyList<string> options)
            {
                // Never mutate a shared caller-owned list or its selection order.
                var translated = new string[options.Count];
                for (int j = 0; j < options.Count; j++) translated[j] = ZhRuntime.Localize(options[j]);
                __args[i] = parameters[i].ParameterType.IsAssignableFrom(typeof(string[])) ?
                    (object)translated : new List<string>(translated);
            }
        }
    }
}

[HarmonyPatch(typeof(MessageQueue), nameof(MessageQueue.GetLines), new Type[] { typeof(int), typeof(int) })]
public static class ZhLogTextPatch
{
    [HarmonyPostfix]
    public static void Postfix(ref string __result)
    {
        if (ZhRuntime.Active) __result = ZhRuntime.Localize(__result);
    }
}

[HarmonyPatch(typeof(MessageQueue), nameof(MessageQueue.GetLinesList), new Type[] { typeof(int), typeof(int) })]
public static class ZhLogLinesPatch
{
    [HarmonyPostfix]
    public static void Postfix(ref List<string> __result)
    {
        if (!ZhRuntime.Active || __result == null) return;
        var lines = new List<string>(__result.Count);
        foreach (string line in __result) lines.Add(ZhRuntime.Localize(line));
        __result = lines;
    }
}

[HarmonyPatch(typeof(MessageQueue), nameof(MessageQueue.Add), new Type[] { typeof(MessageEntry) })]
public static class ZhStoredMessagePatch
{
    [HarmonyPrefix]
    public static void Prefix(ref MessageEntry Message)
    {
        if (ZhRuntime.Active) Message.Text = ZhRuntime.Localize(Message.Text);
    }
}

[HarmonyPatch(typeof(ConsoleLib.Console.IMarkupShader), nameof(ConsoleLib.Console.IMarkupShader.GetDisplayName))]
public static class ZhShaderNamePatch
{
    [HarmonyPostfix]
    public static void Postfix(ref string __result)
    {
        // Never modify the shader's identifier, palette, type or saved state.
        if (ZhRuntime.Active) __result = ZhRuntime.Localize(__result);
    }
}

// Localize the full journal template before HistoricStringExpander replaces
// =name= and other historical tokens. Leave category/secret/aggregation IDs alone.
[HarmonyPatch(typeof(JournalAPI), nameof(JournalAPI.AddAccomplishment))]
public static class ZhJournalTextPatch
{
    [HarmonyPrefix]
    public static void Prefix(ref string text, ref string muralText, ref string gospelText)
    {
        if (!ZhRuntime.Active) return;
        text = ZhRuntime.Localize(text);
        muralText = ZhRuntime.Localize(muralText);
        gospelText = ZhRuntime.Localize(gospelText);
    }
}

[HarmonyPatch(typeof(Unpiloted), nameof(Unpiloted.GetDetails))]
public static class ZhUnpilotedDetailsPatch
{
    [HarmonyPostfix]
    public static void Postfix(Unpiloted __instance, ref string __result)
    {
        if (!ZhRuntime.Active) return;
        int penalty = __instance.SpeedPenaltyPercent;
        if (!__instance.CanTakeAction)
            __result = "无法采取行动。";
        else if (penalty > 0 && penalty % 100 == 0)
            __result = "此生物执行非移动动作时，耗时为通常的" +
                (penalty == 100 ? "两" : ZhText.Cardinal(penalty / 100 + 1)) + "倍。";
        else if (penalty == 0)
            __result = "此生物执行非移动动作的行动消耗不变。";
        else
            __result = "此生物执行非移动动作的行动消耗" +
                penalty.ToString("+0;-0", System.Globalization.CultureInfo.InvariantCulture) + "%。";
    }
}

[HarmonyPatch(typeof(ConsoleLib.Console.ScreenBuffer), nameof(ConsoleLib.Console.ScreenBuffer.Write),
    new Type[] { typeof(string), typeof(bool), typeof(bool), typeof(bool), typeof(List<string>), typeof(int) })]
public static class ZhConsoleTextPatch
{
    [HarmonyPrefix]
    public static void Prefix(ref string s)
    {
        // Translate complete text before markup is expanded into console cells.
        // Tile/renderable overloads and all positioning/selection data stay intact.
        if (ZhRuntime.Active) s = ZhRuntime.Localize(s);
    }
}
