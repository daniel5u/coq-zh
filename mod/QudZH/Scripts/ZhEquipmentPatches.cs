using System;
using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;
using HarmonyLib;
using Qud.UI;
using XRL;
using XRL.Language;
using XRL.UI.Framework;
using XRL.World.Anatomy;

// Category identifiers also control grouping, drag/drop and tutorial IDs. Only
// replace the rendered label, using the same localized lookup as inventory.
[HarmonyPatch(typeof(TradeLine), nameof(TradeLine.setData))]
public static class ZhTradeCategoryPatch
{
    [HarmonyPostfix]
    public static void Postfix(TradeLine __instance, FrameworkDataElement data)
    {
        if (!ZhRuntime.Active || !(data is TradeLineData row) || row.type != TradeLineDataType.Category) return;
        Strings._T("TradeLine Category and Collapse", "=collapsed.collapsed= =category=")
            .SetArgument("collapsed", row.collapsed)
            .SetArgument("category", XRL.World.Parts.Physics.Categories.GetDisplayName(row.category))
            .SetUITextSkin(__instance.categoryText);
    }
}

// Descriptions are serialized in saves and laterality is assembled in English.
// Translate the display getter, never the stored Name/Description/Type fields.
[HarmonyPatch(typeof(BodyPart), nameof(BodyPart.GetCardinalDescription))]
public static class ZhEquipmentDescriptionPatch
{
    [HarmonyPostfix]
    public static void Postfix(ref string __result)
    {
        if (ZhRuntime.Active) __result = ZhAnatomyLabels.Localize(__result);
    }
}

public static class ZhAnatomyLabels
{
    private static Dictionary<string, string> labels;
    private static readonly string[] prefixes = {
        "Worn across ", "Worn about ", "Worn on ", "Worn as ",
        "Inner ", "Outer ", "Upper ", "Lower ", "Right ", "Left ", "Inside ", "Outside ",
        "Mid-Fore", "Mid-Hind", "Fore", "Hind", "Mid"
    };
    private static readonly string[] translations = {
        "横披于", "套于", "穿戴于", "用作", "内层", "外层", "上", "下", "右", "左", "内侧", "外侧",
        "中前", "中后", "前", "后", "中"
    };

    private static void Load()
    {
        labels = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        try
        {
            ModInfo mod = ModManager.GetMod("QudZH");
            if (mod == null) return;
            foreach (string row in File.ReadAllLines(Path.Combine(mod.Path, "anatomy_labels.tsv")))
            {
                int tab = row.IndexOf('\t');
                if (tab > 0) labels[row.Substring(0, tab)] = row.Substring(tab + 1);
            }
        }
        catch (Exception ex) { MetricsManager.LogError("QudZH anatomy labels load failed", ex); }
    }

    private static string Label(string text)
    {
        if (labels.TryGetValue(text, out string zh)) return zh;
        for (int i = 0; i < prefixes.Length; i++)
        {
            if (!text.StartsWith(prefixes[i], StringComparison.OrdinalIgnoreCase)) continue;
            string rest = text.Substring(prefixes[i].Length).TrimStart();
            string translated = Label(rest);
            if (translated != rest || Regex.IsMatch(rest, @"[㐀-鿿]")) return translations[i] + translated;
        }
        return text;
    }

    public static string Localize(string text)
    {
        if (!ZhRuntime.Active || string.IsNullOrEmpty(text)) return text;
        if (labels == null) Load();
        // Preserve shader identifiers, color escapes, padding and duplicate-limb
        // numbers. Only visible runs in this anatomy-specific getter are mapped.
        return Regex.Replace(text, @"\{\{[^|{}]+\||\}\}|[&^][A-Za-z]|[^{}&^]+", m =>
        {
            if (m.Value.StartsWith("{{") || m.Value == "}}" || m.Value[0] == '&' || m.Value[0] == '^') return m.Value;
            Match parts = Regex.Match(m.Value, @"^(\s*)(.*?)(\s+\(\d+\))?(\s*)$");
            return parts.Groups[1].Value + Label(parts.Groups[2].Value) + parts.Groups[3].Value + parts.Groups[4].Value;
        });
    }
}
