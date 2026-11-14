# Runtime localization coverage audit — 2026-11-14

The English in the reported screenshots is outside the official localization tables. Full ExampleLanguage translation coverage does not measure coverage of all visible game text. This audit adds 67 source-backed runtime rows in `work/runtime/ui_audit.tsv`; it does not claim exhaustive translation of hard-coded C# text.

## Confirmed causes

1. The Escape menu is partly localized upstream. `research/decompiled/XRL.Core/XRLCore.cs:1036–1063` localizes Quit Without Saving / Abandon Character through `Strings._S`, but directly constructs the other options from English literals. This explains why the same popup displays Chinese Cancel/Quit and English Set Checkpoint/Options. `&K` prefixes mark disabled options; they are formatting, not part of the translatable label.
2. `research/decompiled/XRL.World/Quest.cs:195–210` constructs quest notices by concatenating English sentence fragments with an already localized quest title. `research/decompiled/XRL.World.Conversations.Parts/ReceiveItem.cs:122` and `WaterRitualNephilimPacify.cs:53` do the same with item names. Exact English→Chinese table entries cannot match these dynamic strings. `{0}`/`{1}` templates must retain the rendered title/item markup.
3. Presentation hooks alone are too late for some paths. `research/decompiled/XRL.UI/Popup.cs:673–685` dispatches to ShowBlock or directly to MessageQueue when suppressed. `ShowFail` intentionally disables log recording. `PickOption` decorates labels with hotkeys and color markup before drawing; matching the whole decorated string fails against a plain label. Hook popup arguments before decoration, preserve option order/hotkeys/default selection and input-control strings.
4. `research/decompiled/XRL.Messages/MessageQueue.cs:112–160` has static string/char AddPlayerMessage overloads and instance Add(string)/Add(MessageEntry). The instance MessageEntry path is the common storage boundary and applies Markup.Transform before persisting text. Only hooking AddPlayerMessage(string,string,bool) misses direct Add callers. Translation should happen before storage so both the modern log and legacy log receive localized text.

## Added template coverage

The 67 added rows cover:

- Escape labels, checkpoint restrictions, quit/save confirmations, travel/stair prompts, nearby hostiles, examination restrictions, concise/verbose messages (`XRLCore.cs`).
- Quest received/completed/failed/step-failed notices and received items (`Quest.cs`, `ReceiveItem.cs`, `WaterRitualNephilimPacify.cs`).
- Keybinding deletion/default reset/save prompts (`XRL.UI/KeyMappingUI.cs`, `OptionsUI.cs`).
- Skill point/XP awards, gain-mutation notices, insufficient ritual liquid/skill points, infection notices (`XRL.World.Conversations.Parts/*`, `XRL.UI/StatusScreen.cs`).
- Journal deletion/renaming, recipe forgetting, equipment/ability restrictions, location discovery, tombstone/error feedback (`XRL.UI/JournalScreen.cs`, `EquipmentScreen.cs`, `AbilityManager.cs`, `ConversationUI.cs`, `GameSummaryUI.cs`).

Every row is supported by the inspected installed game's decompiled source. Numeric placeholders and arbitrary-text placeholders have been checked for preservation. Some entries are existing upstream-localized phrases included as runtime fallbacks, not newly discovered omissions in the official tables.

## Remaining risks and priorities

A conservative source scan finds **426 literal call sites in 136 C# files** matching `Popup.Show/ShowFail/ShowYesNo/ShowYesNoCancel` or `MessageQueue.AddPlayerMessage` with a literal first argument. This is an audit candidate count, not an untranslated-string count: some are debug text, some pass through newer localization elsewhere, some overlap, and many additional paths are not matched by this scan.

Priority next steps are to inspect common inventory/equipment actions and combat/event messages, then terminal screens and generated dialogue. Whole English paragraphs remain template-dependent; a generic UI hook cannot translate arbitrary unknown English. Generated names, grammar tokens and stat arguments need context-specific translation rather than unrestricted word replacement.

Do not localize action identifiers, blueprint IDs, hotkey characters, sound IDs, paths, or confirmation input tokens. Only visible text should change. Historical messages already stored in an existing save may remain English unless translated during display or explicitly migrated; new-message hooks do not rewrite old saves.

Validation should exercise real shipped TSV entries, decorated/disabled option labels, mixed Chinese item/quest names, names containing numeric characters, nested markup, Popup synchronous/asynchronous paths, direct log Add calls, inactive-language behavior and preservation of menu/input control semantics. Running-game confirmation is still necessary to verify Harmony patch activation and on-screen behavior.

## Implemented and verified

`ZhPopupPatches.cs` now intercepts visible Popup arguments before rendering, clones option lists, and leaves sound IDs, hotkeys and confirmation/input strings intact. A prefix on `MessageQueue.Add(MessageEntry)` covers the common storage boundary. Postfixes on `GetLines`/`GetLinesList` translate historical message copies on read; they do not rewrite save data. Other consumers reading raw saved message arrays may still show historical English.

The matcher now preserves console colors and nested whole-message markup, supports multiline templates, and prevents a one-line wildcard from swallowing adjacent log messages. The shipped bank contains 664 templates, with zero rejected during assembly. All 73 helper/runtime checks pass, including the exact screenshot menu, quest/reward phrases, numeric names, reordered step captures, historical log prefixes and unchanged control inputs. All runtime scripts compile against the installed game assemblies with zero errors (existing assembly-reference warning MSB3277 suppressed for the concise build). Live Harmony activation and final game rendering have not been observed in this pass.
