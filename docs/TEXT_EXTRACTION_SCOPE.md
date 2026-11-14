# Scope of a full-game text catalogue

Inspected the installed macOS `lang-experimental` game data and decompiled `Assembly-CSharp.dll` on 2026-11-14. A broad static catalogue is feasible; a finite list of every possible rendered sentence is not. Catalogue completeness, review completeness, translation completeness and runtime-hook coverage are separate measurements.

## Sources to inventory

| Source | What to extract | Boundary |
|---|---|---|
| `Base/ExampleLanguage` | Official marked units, IDs, XML context and placeholders | Defines the existing official coverage denominator, not all game text. |
| Remaining `Base/**/*.xml` | Attribute and element-text values with parent/tag/property context | Includes `Commands.xml`, `Bodies.xml`, `HiddenConversations.xml`, `ObjectBlueprints`, `Worlds.xml` and `Colors.xml`, beyond the language templates. |
| `Base/**/*.rpm` | Parse as XML and inspect string properties | `XRL.EditorFormats.Map/MapFile.cs:255–257` loads these through `XmlTextReader`. All 273 installed files parse; this snapshot has no string `<property>` elements. Its 216,754 object `Name` attributes are blueprint references; coordinates and 96 integer properties are not prose. Do not silently treat this extension as binary. |
| `HistorySpice.jsonc`, `Naming.xml`, pronoun/gender data | Phrase banks, name components and grammar parameters | Preserve path keys and generator syntax; generated output combinations are unbounded. |
| `LibraryCorpus.json`, `LibraryCorpus.json.raw.txt`, `Corpus/*.txt` | Corpus text and source excerpts | These drive generated books/other text. Translating fragments alone does not make the English generator produce grammatical Chinese. The three source excerpts are currently Meteorology, Machinery of the Universe and Thought-Forms. |
| Decompiled `Assembly-CSharp.dll` | Every string literal/interpolation plus enclosing expression, assignment/call, argument position, file and line | Do not rely only on regexes matching `Popup.Show`. Concatenated fragments and strings passed through variables need data-flow review. Retain all raw literals, then classify candidates. |
| Unity serialized assets outside `StreamingAssets/Base` | TextAssets and string fields in UI prefabs/scenes where supported by a Unity-aware reader | `Data/resources.assets`, `sharedassets0.assets`, `globalgamemanagers.assets` and `level0` exist in this installation. A Base/AST scan does not inspect their serialized contents. Binary `strings` output is a candidate aid, not a structured or complete extraction. |
| Runtime observations | Unmatched visible text, source route, formatting and variable samples | Required for assembled sentences, fallback names, rare branches and asset-driven UI; absence from a play session does not prove absence from the game. |

Plain `.txt` files are mixed-purpose: `Mods.csproj.template.txt`, `Display.txt`, `BuildingTiles.txt` and corpus excerpts must not all be promoted directly into translation batches. `DefaultKeymap.json` and `RewiredKeymap.bin` contain input/control data; inspect visible labels separately from bindings and IDs.

## Candidate classification

High-confidence C# sinks include visible `Message`, `Title`, `Intro`, `Prompt` and `Options` arguments on `Popup` methods; `MessageQueue.AddPlayerMessage`, `Add(string)` and `Add(MessageEntry.Text)`; `UITextSkin.text`; menu description/title assignments; mutation `GetDescription`, `GetLevelText`, `GetCreateCharacterDisplayName`; and legacy text-console `ScreenBuffer.WriteAt`/`Write`. `XRL.UI/StatusScreen.cs:130,134,378–410` directly writes English labels/fragments, demonstrating why popup-only extraction is insufficient. `TextBuilder.Append` is context-dependent, not inherently user-visible.

Useful XML candidate attributes include `DisplayName`, `DisplayText`, `Description`, `Short`, `Title`, `Text`, `Message`, `DescriptionPrefix`, `BearerDescription`, `Unit` and `HelpText`, plus `<text>`, `<choice>`, `<page>` and `<p>` content. Their tag/part/property context remains necessary. For example, `Commands.xml` has visible `DisplayText="Move northwest"` beside the internal `ID="CmdMoveNW"`; `Bodies.xml` has the visible `DescriptionPrefix="Worn on"` beside internal part types. `Colors.xml` uses color `Name` as a visible picker label when `ShowInPicker="true"`, even though many other `Name` attributes are identifiers.

Retain identifiers in the raw catalogue so reviewers can recognize fallback labels, but exclude them from automatic translation. Important traps are blueprint IDs, event/command IDs, part/type names, class names, file/resource/sound paths, keybinding names, regexes, XML attribute names, debug strings, save schema keys and exact confirmation inputs. `Strings._S`/`_T` often take both a lookup ID and an English default; keep those roles distinct. A proper name can be user-visible while also acting as an ID; translating its display field is safer than changing its key.

For dynamic expressions preserve the complete source expression and replace only nonliteral spans with stable placeholders. Do not translate isolated fragments without reconstructing their grammar. Maintain every `=variable=`, markup/control token and generator path; some verb/noun token parameters are translatable while the token names are not. Deduplicate by source plus context where meaning or control semantics differs.

## Honest coverage reporting

Report raw extracted values and files, classified user-visible candidates, already-localized defaults, existing TM/runtime matches, unreviewed candidates, extraction errors and explicitly uninspected asset formats separately. A new raw catalogue does not establish a new translated percentage until candidates have been reviewed. Runtime observation should supplement static extraction; it cannot replace it or establish exhaustive coverage.

## Implemented static catalogue

Run `python3 tools/extract_catalogue.py` (.NET 11 SDK required here). `--game-base`, `--code-dir` and `--out` override input/output locations. The command changes no game or translation files. Generated source corpora stay in git-ignored `work/text_catalogue/`.

The installed snapshot produced 97,152 string-expression records from 5,548 C# files, with zero syntax errors. Records include literals, interpolations and proposed concatenation templates; these are not unique user-visible phrases. The data scan read 334 supported files beyond ExampleLanguage, including all 273 RPM maps, with zero remaining parse gaps. It supports JSONC comments/trailing commas and preserves numeric control-character entities accepted by the game XML reader.

`official_units.jsonl` preserves 31,416 existing source units including HistorySpice. `code_strings.jsonl` and `data_strings.jsonl` retain source locations and context. `review_candidates.jsonl` groups 15,441 unique candidates without exact matches in TM/runtime data; template-covered strings and false positives remain possible. Corpus text and probable identifiers stay in the raw catalogue but are excluded from that ordinary prose queue. A language string's presence in TM does not prove its runtime path is localized.

`summary.json` records counts, parse gaps and exclusions. Other file formats (including images/binaries), Unity serialized text and runtime observations remain outside this extractor. Re-run after source/game updates; the catalogue is a snapshot, not a claim of complete rendered-text coverage.

Validation: `python3 tools/test_extract_catalogue.py` passes three regression checks for C# comments/escaped/verbatim/interpolated/concatenated strings, localization-key classification, mixed XML text/control entities, and JSONC URLs/quoted comment markers/trailing commas.

## Reviewed XML catalogue integration

`tools/catalogue_overlays.py` writes only explicitly approved `install_xml` records, with `Lang="zh"` and `LoadPriority="-1100"`. Source evidence: `DataManager.CacheFile` filters Lang against ActiveLanguage; `DataFile.CompareTo` loads lower priorities later; object blueprints support Load=Merge; commands and skills merge by ID/Name. Output permits only named display-text attributes on known element chains. It preserves internal keys, never copies bindings/control/stat fields, rejects stale source text, and leaves already translated fields intact. The ordinary build calls this generator after official language files are rebuilt.

The first integrated XML batch adds11 Commands.xml labels; five other approved texts were already localized and therefore generated no override. Actual game rendering is unverified until restart. `python3 tools/test_catalogue_overlays.py` checks control-field preservation, duplicate-Chinese avoidance, active-language guards, and rejection of stale source snapshots.

Anatomy variants are now supported by Description/DescriptionPrefix-only patches keyed by unchanged Type and VariantOf (Anatomies.LoadBodyPartTypeVariantNode/LoadBodyPartInfo). Collection nodes have no fake Name key. Food.Message and Impaler.Message are explicitly verified display fields; other unknown Message attributes remain disallowed. Shader labels now use a postfix on IMarkupShader.GetDisplayName. The original display property, shader ID, type and palette remain unchanged; only the returned visible string is localized. The XML generator never copies palettes.

`tools/anatomy_catalogue.py` also inventories implicit anatomy descriptions: 169 Type values become visible descriptions when no Description is supplied (BodyPartType constructor and Anatomies variant loader). They are queued as synthetic Description targets, with Type and VariantOf preserved. The overlay builder verifies that the description is still absent and Type matches before accepting the fallback source; explicit changed text is rejected. Only reviewed batches of these labels count as translated.
