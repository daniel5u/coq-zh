# QudZH runtime scripts

The game compiles these `.cs` files as part of the scripting mod and applies
Harmony patches declared with `[HarmonyPatch]` when it loads the mod assembly.
The inspected loader adds the managed game assemblies to Roslyn's references,
then calls `Harmony.PatchAll(Assembly)` for scripting mods that contain Harmony
attributes.

## Files

- `ZhText.cs` contains game-independent formatting logic: CJK classification,
  safe line-break selection, Simplified Chinese number words, list separators,
  and conservative removal of spaces between adjacent CJK name fragments.
- `ZhProvider.cs` registers `[LanguageProvider("zh")] ZhProvider`. It keeps the
  base description and display-name flow, disables English articles, uses
  Chinese list and number formats, sets `zh-CN`, and supplies CJK-aware wrapping.
- `ZhRuntime.cs` translates hard-coded mutation/effect descriptions from
  `runtime_strings.tsv` at the UI/message boundary. It also removes stray English
  articles immediately before Chinese text, including color markup.
- `ZhPopupPatches.cs` translates visible popup arguments before classic/modern
  rendering, preserves menu indices/hotkeys/input values, and translates log
  entries before storage. Historical log readers translate returned text without
  rewriting saved messages. Color wrappers remain intact during lookup.
- `ZhEquipmentPatches.cs` sends trade category labels through the inventory
  category translator, without changing the category IDs used by grouping and
  drag/drop. It translates equipment descriptions at `GetCardinalDescription`,
  including English descriptions stored in existing saves. The generated
  `anatomy_labels.tsv` reuses the reviewed anatomy catalogue; laterality, limb
  numbers, colors and primary-hand markers remain meaningful.
- `ZhWaterRitualPatches.cs` translates the appended reputation panel and choice
  tags before they are joined to dialogue. Runtime templates also cover ritual
  reward messages. Choice IDs, costs, eligibility and reputation values are not
  changed.
- `ZhGrammarPatches.cs` adds Harmony prefixes for pluralization, third-person
  conjugation, possessives, and `GameObject.GetVerb`. The prefixes only change
  a call when `zh` is active and the input contains CJK; English behavior
  continues through the original methods. CJK letters have no upper/lower case,
  so the game's normal capitalization helpers leave them unchanged.

The number forms use `零` for cardinal zero and `无` for `CardinalNo(0)` (the
base provider's “no items” semantic). Ordinals use `第` plus the Chinese
cardinal form. Multiplicatives use `一次`, `两次`, and `<number>次`.

## Local verification projects

`research/zhbuild/zhbuild.csproj` compiles all runtime scripts against every
managed game DLL, including `Assembly-CSharp.dll` and `0Harmony.dll`.
`research/zhchecks/zhchecks.csproj` is a small console check suite that compiles
the pure helpers and production runtime translator without game assemblies.
`RuntimeStubs.cs` supplies only the external API boundary for these checks. The
checks load the shipped TSV as well as exercising popup/log argument handling.
Run with:

```sh
dotnet build research/zhbuild/zhbuild.csproj
DOTNET_ROLL_FORWARD=Major dotnet run --project research/zhchecks/zhchecks.csproj
```

Shader display names are localized at `IMarkupShader.GetDisplayName`; IDs and palette state remain untouched, and inactive languages return their original labels.
