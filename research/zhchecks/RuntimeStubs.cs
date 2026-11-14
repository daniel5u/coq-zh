// Minimal external API stubs let checks execute the production runtime translator.
using System;
namespace ModelShark {
 public class TooltipManager { public void SetTextAndSize(TooltipTrigger trigger) {} }
 public class TooltipTrigger { public TooltipField[] parameterizedTextFields; }
 public class TooltipField { public string value; }
}
namespace UnityEngine { public static class Debug { public static void Log(string message) {} } }
namespace HarmonyLib {
 [AttributeUsage(AttributeTargets.Class | AttributeTargets.Method, AllowMultiple = true)]
 public class HarmonyPatch : Attribute {
  public HarmonyPatch() {} public HarmonyPatch(Type type, string method) {}
  public HarmonyPatch(Type type, string method, Type[] arguments) {}
 }
 [AttributeUsage(AttributeTargets.Method)] public class HarmonyPrefix : Attribute {}
 [AttributeUsage(AttributeTargets.Method)] public class HarmonyPostfix : Attribute {}
 [AttributeUsage(AttributeTargets.Method)] public class HarmonyTargetMethods : Attribute {}
}
namespace XRL.Language { public static class LanguageLoader { public static string ActiveLanguage = "zh"; } }
namespace ConsoleLib.Console {
 public abstract class IMarkupShader { public virtual string GetDisplayName() => ""; }
 public class ScreenBuffer { public ScreenBuffer Write(string s, bool processMarkup = true, bool HFlip = false, bool VFlip = false, System.Collections.Generic.List<string> imposters = null, int maxCharsWritten = -1) => this; }
}
namespace XRL {
 public class ModInfo { public string Path; }
 public static class ModManager { public static ModInfo GetMod(string name) => new ModInfo { Path = AppContext.BaseDirectory }; }
 public static class MetricsManager { public static void LogError(string text, Exception ex) { throw ex; } }
}
namespace XRL.UI {
 public class UITextSkin { public string text; public void Apply() {} }
 public static class Popup {
  public static void PickOption(string Title, string Intro, string Sound, System.Collections.Generic.IReadOnlyList<string> Options, System.Collections.Generic.IReadOnlyList<char> Hotkeys) {}
  public static void AskString(string Message, string Default, string WantsSpecificPrompt) {}
 }
}
namespace XRL.UI.Framework { public class FrameworkDataElement {} }
namespace XRL.World.Anatomy { public class BodyPart { public string GetCardinalDescription() => ""; } }
namespace XRL.World.Parts {
 public class Physics { public static class Categories {
  public static string GetDisplayName(string name) => name == "Food" ? "食物" : name == "Grenades" ? "手榴弹" : name;
 } }
}
namespace XRL.Language {
 public static class Strings { public static LabelTemplate _T(string context, string text) => new LabelTemplate(); }
 public class LabelTemplate {
  private bool collapsed; private string category;
  public LabelTemplate SetArgument(string key, object value) { if (key == "collapsed") collapsed = (bool)value; else category = (string)value; return this; }
  public void SetUITextSkin(XRL.UI.UITextSkin skin) { skin.text = (collapsed ? "+ " : "- ") + category; }
 }
}
namespace Qud.UI {
 public enum TradeLineDataType { Category, Item }
 public class TradeLineData : XRL.UI.Framework.FrameworkDataElement { public TradeLineDataType type; public bool collapsed; public string category; }
 public class TradeLine { public XRL.UI.UITextSkin categoryText = new XRL.UI.UITextSkin(); public void setData(XRL.UI.Framework.FrameworkDataElement data) {} }
}
namespace Qud.UI { public static class RTF { public static string FormatToRTF(string s, string color, int size, bool strip) => s; } }
namespace Qud.API { public static class JournalAPI { public static void AddAccomplishment(string text, string muralText = null, string gospelText = null) {} } }
namespace XRL.World.Effects { public class Unpiloted { public int SpeedPenaltyPercent; public bool CanTakeAction = true; public string GetDetails() => ""; } }
namespace XRL.Messages {
 public struct MessageEntry { public string Text; }
 public class MessageQueue {
  public static void AddPlayerMessage(string message, string color, bool popup) {}
  public void Add(MessageEntry Message) {}
  public string GetLines(int start, int count) => "";
  public System.Collections.Generic.List<string> GetLinesList(int start, int count) => null;
 }
}
