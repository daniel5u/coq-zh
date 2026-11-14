using System;
using System.Text;
using XRL.World.Conversations;

// Boundary-only stubs: tests execute the production translator and Harmony callbacks.
namespace XRL.World.Conversations
{
    public class Choice { public string GetTag() => null; }
    public class DisplayTextEvent { public TextBuffer Text = new TextBuffer(); }
    public class TextBuffer
    {
        private readonly StringBuilder text = new StringBuilder();
        public int Length => text.Length;
        public TextBuffer Append(string s) { text.Append(s); return this; }
        public TextBuffer Remove(int start, int length) { text.Remove(start, length); return this; }
        public string ToString(int start, int length) => text.ToString(start, length);
        public override string ToString() => text.ToString();
    }
}
namespace XRL.World.Conversations.Parts
{
    public class WaterRitual { public bool HandleEvent(DisplayTextEvent E) => true; }
}

static class WaterRitualChecks
{
    static int checks;
    static void Equal(string expected, string actual, string label)
    {
        checks++;
        if (expected != actual) throw new Exception(label + "\nExpected: " + expected + "\nActual: " + actual);
    }
    static void Tag(string source, string expected)
    {
        string actual = source;
        ZhWaterRitualTagPatch.Postfix(ref actual);
        Equal(expected, actual, source);
    }
    public static int Run()
    {
        Tag("{{g|[begin water ritual; {{C|1}} dram of {{B|水}}]}}", "{{g|[开始水礼；{{C|1}}打兰{{B|水}}]}}");
        Tag("{{K|[begin water ritual; {{r|1}} dram of 水]}}", "{{K|[开始水礼；{{r|1}}打兰水]}}");
        Tag("{{g|[{{C|-50}} reputation]}}", "{{g|[{{C|-50}}声望]}}");
        Tag("{{g|[{{C|+50{{c|+25}}}} reputation]}}", "{{g|[{{C|+50{{c|+25}}}}声望]}}");
        Tag("{{g|[learn {{W|短刃}}: {{C|-100}} reputation, {{C|-25}} SP]}}", "{{g|[学习{{W|短刃}}：{{C|-100}}声望，{{C|-25}}技能点数]}}");
        Tag("{{g|[learn to cook {{W|炖汤}}: {{C|-50}} reputation]}}", "{{g|[学习烹制{{W|炖汤}}：{{C|-50}}声望]}}");
        Tag("{{g|[gain {{C|100}} {{W|skill points}}: {{C|-50}} reputation]}}", "{{g|[获得{{C|100}}点{{W|技能点数}}：{{C|-50}}声望]}}");
        Tag("{{g|[gain {{M|念力}}: {{C|-100}} reputation]}}", "{{g|[获得{{M|念力}}：{{C|-100}}声望]}}");
        Tag("{{g|[become infected with 菌皮: {{C|-50}} reputation]}}", "{{g|[感染菌皮：{{C|-50}}声望]}}");
        Tag(null, null);
        Tag("{{g|[未变更]}}", "{{g|[未变更]}}");
        const string englishPanel = "\n\n{{C|-----}}\n{{y|Your reputation with {{C|约帕}} is {{C|-50}}.\n长老 can award an additional {{C|200}} reputation.}}";
        const string chinesePanel = "\n\n{{C|-----}}\n{{y|你在{{C|约帕}}眼中的声望为{{C|-50}}。\n长老还能给予你{{C|200}}点声望。}}";
        var e = new DisplayTextEvent();
        e.Text.Append("既有对话 {{R|不改动}}");
        ZhWaterRitualStatusPatch.Prefix(e, out int start);
        e.Text.Append(englishPanel);
        ZhWaterRitualStatusPatch.Postfix(e, start);
        Equal("既有对话 {{R|不改动}}" + chinesePanel, e.Text.ToString(), "panel preserves original dialogue and markup");
        Equal("因为他们敬慕长老，你在{{C|约帕}}眼中的声望提升了{{G|100}}点，现为{{g|300}}。", ZhRuntime.Localize("Because they admire 长老, your reputation with {{C|约帕}} increased by {{G|100}} to {{g|300}}."), "reputation cause and signed total");
        Equal("你如今受到{{C|约帕}}的{{G|爱戴}}。", ZhRuntime.Localize("You are now {{G|loved}} by {{C|约帕}}."), "reputation tier");
        Equal("{{y|你在长老眼中的声望为{{C|0}}。\n他还能给予你{{C|0}}点声望。}}", ZhRuntime.Localize("{{y|Your reputation with 长老 is {{C|0}}.\n他 can award an additional {{C|0}} reputation.}}"), "hidden faction name and pronoun panel");
        e = new DisplayTextEvent();
        e.Text.Append("原有对话");
        ZhWaterRitualStatusPatch.Prefix(e, out start);
        e.Text.Append("另一模组的内容");
        ZhWaterRitualStatusPatch.Postfix(e, start);
        Equal("原有对话另一模组的内容", e.Text.ToString(), "unknown appended layout preserved");
        XRL.Language.LanguageLoader.ActiveLanguage = "en";
        Tag("{{g|[{{C|-50}} reputation]}}", "{{g|[{{C|-50}} reputation]}}");
        e = new DisplayTextEvent();
        e.Text.Append("Existing dialogue");
        ZhWaterRitualStatusPatch.Prefix(e, out start);
        e.Text.Append(englishPanel);
        ZhWaterRitualStatusPatch.Postfix(e, start);
        Equal("Existing dialogue" + englishPanel, e.Text.ToString(), "inactive language unchanged");
        XRL.Language.LanguageLoader.ActiveLanguage = "zh";
        return checks;
    }
}
