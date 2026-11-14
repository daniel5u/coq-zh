# Caves of Qud language engine research

**Install inspected:** Steam `lang-experimental` build, CoreVersion `2.0.212.32`, macOS app. Read-only against the game and workshop install. ILSpy project output is retained in `research/decompiled/`; the decompiler executable and local tool files are in `research/tools/`. ILSpy 11.2 targets .NET 10; it ran here on the installed .NET 11 with `DOTNET_ROLL_FORWARD=Major` and `DOTNET_ROOT=/opt/homebrew/opt/dotnet/libexec`.

Paths below are relative to `research/decompiled/` unless an installed-game path is stated.

## 1. Mod shape, selection, merging, and fallback

A working data-only language mod follows the existing Chinese mod's pattern: mod root has `manifest.json`, `Languages.xml`, then language-overlay XML files with ordinary game root names and `Lang="zh"`. The existing mod's `Languages.xml` is:

```xml
<languages Encoding="utf-8">
  <lang Code="zh" DisplayName="简体中文" FontFamily="Source Han Mono SC" />
</languages>
```

`LanguageLoader.HandleLangNode` (`XRL.Language/LanguageLoader.cs`) reads **only** `Code` (required), `DisplayName`, and `FontFamily`. There are no other recognized `<lang>` attributes in this build. Its default language entry is `en` / `English`. `ActiveLanguage` reads option `Language` while in game, otherwise reports `en`; `ActiveFont` resolves the configured font family or game's default. `LanguageLoader.LoadLanguages` enumerates every XML stream with root `languages`, registers entries, clears the provider, then scans `ModManager.ActiveTypes` for a `[LanguageProvider("<active code>")]` class and instantiates it.

File matching is by XML root and root `Lang`, **not filename**. `DataManager.CacheFile` (`XRL/DataManager.cs`) ignores XML files whose root `Lang` is neither absent nor exactly the active language; no `Lang` means shared/default data. Thus `Strings.xml`, `Items.xml`, etc. can overlay by root type with `Lang="zh"`; keeping the base filename is conventional and makes file ownership clear. `DataManager.SortXMLRoots` and `DataFile.CompareTo` put base files before mods; mods are then ordered by mod load order, `LoadPriority` (default `-1000` for language-tagged XML and `0` for untagged XML), then path.

The root XML names and translatable fields come from the matching `ExampleLanguage/*.example.xml` templates. Copy the `▶`-marked values into a matching root such as `<objects Lang="zh" Encoding="utf-8">`. `Load="Merge"` is **loader-specific**, not a global “merge this XML tree” instruction: each loader decides whether it merges/replaces/removes and which keyed node it merges. For example, object overlays use `<object Name="..." Load="Merge">`, world overlays use keyed world/cell/zone nodes, and `PopulationManager` defaults its `Load` to `Merge`; strings instead overlay dictionaries by keys and do not need `Load="Merge"`.

`StringsLoader.HandleStringNode` (`XRL.Language/StringsLoader.cs`) uses `(Context, ID)` as the context-table key and separately inserts the first occurrence for each `ID` into the global fallback table. `Strings.TryGetString` (`Strings.cs`) checks exact `Context+ID`, then ID-only; when neither exists, it returns `ID` itself. Since IDs normally are the source English text (see `_S(context, "English text")`), a missing translation displays English. Context matters where duplicate source IDs occur; use the `Context` from the example file. An ID-only translation also acts as a cross-context fallback. Context-specific translations win over ID-only.

Each `<string>` accepts `Context`, `ID` (required), optional `OrderAdjust`, and either a `Value` attribute **or** inner text. `Value` wins if present and the parser consumes/discards inner content; otherwise `GetTextNode()` is used. For inner text, `GetTextNode()` calls `ProcessedValue`, which runs `TextBuilder.Unindent()`: it trims outer whitespace, removes common indentation from lines, and normalizes CRLF to LF. Deliberate internal newlines and blank lines remain; leading/trailing newlines are trimmed. The `Value` attribute path is read as an attribute and skips `GetTextNode`, so its value is not passed through this unindent step. XML entity decoding happens before the loader receives text. `&#xA;` becomes an LF; when it is in an XML attribute, use a character reference because literal XML attribute whitespace is normalized by XML parsing.

`Strings.Conversations` entries are special only at source extraction/load time. The example file documents that the conversation loader strips leading/trailing whitespace and unindents each line; `IConversationElement.Prepare` chooses one `~`-separated option with `GetRandomSubstring('~', Trim: true)`, then trims the selected text. Use `&#xA;` for deliberate multiline text. For regular `<strings>` inner text, outer whitespace is trimmed and indentation is normalized by `GetTextNode`; for XML data fields parsed through general loaders, follow the specific loader's text/attribute handling.

The game doesn't have a generic translation catalog merge or a separate always-loaded English catalog. Fallback to English is implemented because the untranslated string ID is returned as the source. This works for `_S` and `_T` strings, not for arbitrary raw literals.

## 2. Grammar placeholders and language providers

### Template syntax

`GameText.Process` (`XRL/GameText.cs`) scans `=...=` placeholders. It parses target/key before `.`, optional parameter segments after `:`, and arguments after `#`; `|` chains nested replacers. `VariableReplacers.LoadReplacers` discovers `[VariableReplacer]` methods by reflection. Common targets are `subject`, `object`, `player`, `pronouns` (subject alias), `objpronouns`, and named `.SetArgument()` aliases. Capitalized first keys use replacer metadata to return a capitalized variant.

Examples:

- `=subject.T=` is the subject target's translated display name with capitalization. `=subject.t=` is the same name in the normal case. These are GameObject name replacers, not a Chinese-specific grammatical form.
- `=object.an=` calls the indefinite article/name logic and returns article plus object name in English (e.g. `a sword`); `=object.a.name=` is another common form. `=object.the.name=` uses definite article.
- `=verb:stare=` calls `GameObject.GetVerb("stare")`; `=verb:stare:afterpronoun=` sets the pseudoplural-after-pronoun flag before the same call. The object form is `=subject.verb:stare=`. In this build a singular non-player subject gets `Grammar.ThirdPerson("stare")` -> `stares`; plural/player subjects get `stare`. `afterpronoun` suppresses third-person conjugation for pseudoplural pronoun sets.
- `=pronouns.subjective=`, `.objective`, `.possessive`, `.substantivePossessive`, `.reflexive` (also aliases `they`, `them`, `their`, etc.) read `GameObject.GetPronounProvider()`. Casing comes from the replacer/capitalization marker. `=player.formalAddressTerm=` gets the active player's pronoun provider's `FormalAddressTerm`, not a universal phrase; its counterpart is `=pronouns.formalAddressTerm=`.
- `=name=` is the generic `toString` replacer (usually a GameObject display name when the target argument is an object; type-specific replacers exist). Explicit variable arguments set with `.SetArgument("name", ...)` resolve the named argument instead.
- `~` in conversation/dialog text separates random alternatives, selected at runtime. It is not a grammatical inflection marker. Avoid using it as ordinary punctuation in these strings unless intended as a variant separator.
- `xtagTextFragments` are per-object keyed phrase banks, e.g. `<xtagTextFragments Skin="chitin" Activity="roaming around idly" />`; `=subject.fragment:Skin=`, `=subject.fragment:Activity=`, or `=subject.fragment:Skin:paper=` retrieves the corresponding fragment (with optional fallback). They are meaningful text and should be translated. Other systems use comma-separated fragment lists and select a member.
- In books, `[[A.]]` and `[[...]]` are book markup/header delimiters, not a template token. `BookUI.HandlePageNode` transforms markup then strips `[[` and `]]` for display; for corpus generation it removes bracketed headers. Keep the delimiters and translate their interior as appropriate; preserve any letter labels referenced elsewhere.
- `{{color|...}}`, `&` terminal color codes, etc. are formatting markup processed by `Markup`; preserve the delimiters and usually translate only visible content. `GameText` avoids interpreting variable syntax inside formatting contexts and removes color wrappers only when asked.

### Is English grammar auto-injected for `zh`?

Yes, unless a mod supplies a provider or changes individual content/call sites. There is no automatic “Chinese mode” in the replacers. `Translator.SetProvider(null)` runs on language load; with no matching attributed mod class, APIs lazily fall back to `TranslatorEnglish` / `TranslatorBase` behavior. `GameObject.GetVerb` itself applies `Grammar.ThirdPerson` in `GameObject.cs`, separately from `Translator.Provider`, and article placeholders call the provider's English article methods by default. Thus `=verb:stare=` can still produce English conjugation, and `=object.an=` can still prepend `a/an` unless the translation rewrites the placeholder/message or a provider/Harmony patch handles it.

A provider can remove article output and supplies many grammatical services. But it **cannot by itself** change every direct `GameObject.GetVerb` call or every explicit raw English fragment. Chinese translation strategy should avoid English-specific tokens in translated templates where possible, override provider APIs for shared behavior, and patch/correct unavoidable runtime assembly selectively.

### Provider selection and complete virtual contract

`LanguageProviderAttribute.cs` defines `[LanguageProvider(string Lang)]`. `LanguageLoader.LoadLanguages()` chooses the last active type in load order whose attribute `Lang == ActiveLanguage`, via `Activator.CreateInstance`. Compile the provider into a DLL loaded by the mod; a plain `.cs` text file is not reflected/compiled automatically unless the mod's build workflow turns it into an assembly. Derive `TranslatorBase` for ready English defaults and override what Chinese changes. `Translator.Provider` (`XRL.Language/Translator.cs`) declares this complete provider contract; these are the abstract methods (the parameter structs are nested under `Translator.Provider`):

```csharp
void NextPossibleLineBreakIndex(ReadOnlySpan<char> Span, int StartIndex,
    out int BreakBeforeIndex, out bool ReplaceIfBroken);
float GetGraphemeWidth(ReadOnlySpan<char> c);
string MakeAndList(IReadOnlyList<string> List, MakeAndListParams Params = default);
string MakeOrList(IReadOnlyList<string> List, MakeOrListParams Params = default);
string MakeCommaList(IReadOnlyList<string> List);
DescriptionBuilder CreateDescriptionBuilder(int Cutoff = int.MaxValue, bool BaseOnly = false);
void ExtractArticle(ref string Name, out string Article);
void ExtractAndSetDefiniteArticle(GameObject Object, string Name);
string DefiniteArticle(DefiniteArticleParams Params);
string IndefiniteArticle(IndefiniteArticleParams Params);
void Stutterize(StutterizeParams Params);
void Weirdify(WeirdifyParams Params);
void Unweirdify(TextBuilder TextBuilder);
CultureInfo GetCultureInfo();
StringComparer GetStringComparer();
StringComparer GetStringComparerIgnoreCase();
bool IsWordCharacter(char Char);
char ToLower(char Char);
char ToUpper(char Char);
string Cardinal(long num);
string CardinalNo(long num);
string Ordinal(long num);
string OrdinalWithDigits(long num);
string Multiplicative(long num);
protected void ProcessMagnitude(ref long num, ref int magnitude,
    TextBuilder result, string place);
protected bool ProcessMagnitudes(ref long num, ref int magnitude,
    TextBuilder result, string suffix = null);
string GameObjectDisplayName(GameObject GO, out bool AdjunctNounActive,
    GameObjectDisplayNameParams Params);
void MutateZoneName(MutateZoneNameParams Params);
void AddArticle(AddArticleParams Params);
```

`TranslatorBase.cs` is the actual English implementation. Its defaults include whitespace-only line breaks (`NextPossibleLineBreakIndex` finds space/LF), 1.5 cell width for Hangul/CJK/fullwidth ranges, comma/English “and”/“or” list joins, default English descriptions, extraction of `the/a/an/some`, definite and indefinite English articles, English culture/character casing, English number words and bundles of three digits, English display-name assembly, and English zone adjective placement. `CreateDescriptionBuilder` uses `DescriptionBuilder(int.MaxValue, BaseOnly)`; most descriptions are order-based. `GameObjectDisplayName` retrieves an event-built name, handles hidden wording, adjunct nouns, possession, definite/indefinite article prefixes, and capitalization. `AddArticle` distinguishes a/an and handles placement. The full defaults are inspectable in `TranslatorBase.cs`.

The verb path is independent; the essential implementation is:

```csharp
// GameObject.GetVerb (XRL.World/GameObject.cs)
if ((SecondPerson && IsPlayer() && Grammar.AllowSecondPerson) || GetPlurality(AsIfKnown))
    return PrependSpace ? " " + Verb : Verb;
if (PronounAntecedent && GetPseudoPlurality(AsIfKnown))
    return PrependSpace ? " " + Verb : Verb;
return Grammar.ThirdPerson(Verb, PrependSpace);

// GameObjectReplacers.Verb (XRL.World.Text.Delegates/GameObjectReplacers.cs)
return Object.GetVerb(verb, PrependSpace: false, pronounAntecedent);
```

This is why overriding `Translator.Provider.IndefiniteArticle` does not change `=verb:stare=`: `GameObject.GetVerb` conjugates independently.

Extension feasibility: a provider can override English articles, list joining, numeric words/ordinals/multiplicatives, culture/casing, word classification, widths and wrap points, stutter/weird text transforms, description concatenation, display-name assembly (including adjective+noun order), zone-name mutation, and article insertion. There is **no provider pluralization method**: `Grammar.Pluralize`, `Grammar.ThirdPerson`, and `GameObject.GetVerb` are separate static/instance English logic and need localized message templates, changed data/call sites, or Harmony patches. The provider also cannot intercept arbitrary direct English strings or UI calls that never route through `Translator`.

## 3. Grammar tags and selected XML data

- Object `<xtagGrammar Proper="..." massNoun="..." iArticle="..." adjunctNoun="..." adjunctNounPost="..." />` is object grammar metadata. `Proper=true` makes names proper and suppresses default articles; preserve it as a boolean regardless of Chinese proper-name translation. `massNoun=true` affects default indefinite article and whether an adjunct classifier is selected; do **not** flip it just to express Chinese countability. The provider should suppress English articles. `iArticle` overrides the English indefinite article for that object; it is irrelevant in Chinese if provider returns empty. `adjunctNoun` is used by `GetAdjunctNoun` as an English classifier/phrase such as `pair`, `set`, or `suit`; translate it to a natural Chinese classifier only if the provider/display-name logic continues to use adjunct nouns, and don't blindly leave the English value. `adjunctNounPost="true"` moves it after the object name; treat as structural boolean and keep when source relationship matters. `GetAdjunctNoun` and `IsMassNoun` are in `XRL.World/GameObject.cs`; `TranslatorBase.GameObjectDisplayName` chooses whether to use the adjunct and a translatable `Strings._T` template for pre/post order.
- In `Worlds.xml`, zone `Name` and `NameContext` are display text. `ProperName` is a boolean-like display/schema value (the language template marks it translatable, but it controls properness), and `IndefiniteArticle` is article text for zone display. With a Chinese provider, normally use empty article values or leave source values only if all corresponding paths are provider-mediated. Translate Name/NameContext; preserve proper-name semantics. The shipped template includes those fields.
- `PronounSets.xml`: `Name` is the set key/identity and should remain stable (`player`, `plural/player`, `sie/...`); `Subjective`, `Objective`, `PossessiveAdjective`, `SubstantivePossessive`, `Reflexive`, `PersonTerm`, `ImmaturePersonTerm`, `FormalAddressTerm`, `OffspringTerm`, `SiblingTerm`, `ParentTerm` feed pronoun/relationship replacement variables. Chinese may reuse the same pronoun across several fields, but populate all used fields intentionally and retain the expected forms. `BasePronounProvider.cs` and `PronounSet.cs` define fields and load behavior; `PronounSets.example.xml` marks the user-facing fields.
- `InventoryActions.xml`: `display` and `preferToHighlight` are user-facing strings and should be translated. `key` is parsed into `InventoryAction.Key` (`char`); retain the source ASCII/symbol key because it participates in keyboard selection. The example generator marks it, but translation changes can break the input binding. `InventoryAction.Name` is the stable key and must not change. See `XRL.World/InventoryAction.cs` and `InventoryActions.example.xml`.
- `Options.xml`: translate `DisplayText`, `ConsoleDisplayText`, `SwitchDisplayText`, `Category`, help text, and search keywords where present. `Values` stores actual option values; the example template explains choices may be written `internalValue|localized display`. Keep each internal left side exactly stable and translate only the display side. Some values are sent to code and are not prose.
- `Naming.xml`: `HyphenSeparator` and `NameSeparator` are visible separators (set to Chinese-appropriate punctuation/empty separator if the game's generated names should use that convention). `prefixes/infixes/postfixes` are random syllable/name fragments with `Name` plus `Weight`; translate/replace these phonetic syllables for Chinese naming. `Amount` controls how many are chosen. `template`/`titletemplate` is an output format containing variables; translate fixed glue text and retain variable names. `templatevar` and default template vars provide phrase/name components used during expansion. `value` entries (NameValue) supply weighted values for template variables; translate values while preserving IDs, weights, scope selectors, and syntax. NameStyle logic is in `XRL.Names/NameStyle.cs` and `NameStyles.cs`.

## 4. Font support

The game ships a `Source Han Mono SC` TMP font asset in its Unity-managed `FontManager.Fonts` list. `FontManager.GetFont` looks up a `TMP_FontAsset` by `faceInfo.familyName`; `LanguageLoader.ActiveFont` returns the configured family. `FontManager.UpdateFontFallbacks` automatically removes prior Source Han fallbacks and adds the active Source Han font, defaulting to `Source Han Mono SC` if the selected font is not one. `UITextSkin.ApplyFont` applies the configured font. There are no loose `.ttf`/`.otf` CJK files in the inspected Data tree; the font is Unity-serialized, not a loose font file. The reference mod sets the supported family name and does not need to bundle a font.

## 5. Coverage and what remains

The `ExampleLanguage` exporter derives templates from each loader's `LanguageXml.Document` schema and `_S`/`_T` collection. It covers many XML data names/descriptions, options, inventory action labels, books, worlds, conversations, naming, etc. It does not promise that every visible string is captured. The main uncovered groups are:

1. **Raw literals and concatenations in C#**: popup/help/window labels and messages assembled by direct string concatenation rather than `Strings._S`/`_T`; hard-coded generic UI/validation/debug text; messages from mods whose own source is not localized. These display verbatim. Efficient fix is to add `_S/_T` coverage upstream where possible; otherwise patch the specific producing method. Scope is broad and needs runtime inventory; high effort to guarantee full coverage.
2. **Runtime combat messages**: many go through `_T` and are covered by `Strings`/`Strings.appendix`, but they still contain English grammar variables and direct calls (`GameObject.GetVerb`, `does`, possessives). XML String coverage is relatively feasible; fully natural Chinese requires editing message templates and potentially patching source routines; medium/high effort.
3. **Runtime display names**: names composed from blueprint base names plus adjective/quality/material/title/stack/adjunct details are built via `GetDisplayNameEvent`/`TranslatorBase.GameObjectDisplayName`. Base blueprint names are in `Items.example.xml`; the exact assembled phrase order is not itself a static string. A provider can override assembly, and a Harmony patch can change direct `GameObject.GetDisplayName` flows. This is high effort because every name modifier, ordering, color/quality, and caller flag must still work.
4. **Generated history/sultan text**: `HistorySpice.jsonc` drives `HistoricStringExpander`; names and snippets are generated by query selection/expansion, outside the XML example set. A language-specific `HistorySpice.zh.json` is supported by `DataManager.FilePathFromBasePreferModFile`'s `<name>.<activeLanguage>.json` preference. Translate/replace data/query entries and keep query IDs, selectors and markup. Potentially large but data-only; medium/high effort. Sultan history also inserts generated names and static fragments from code, so partial data replacement won't guarantee translated prose.
5. **Library corpus/generated books**: `LibraryCorpus.json` and `MarkovBook` generate titles/paragraphs at runtime; these are not represented by XML templates. The same language-suffixed JSON override path can be used (`LibraryCorpus.zh.json`). Generated output can be localized by replacing corpus data and patching/redirecting corpus loading, but quality depends on supplying Chinese corpus suitable for Markov generation; medium effort. Actual authored `Books.xml` pages are in `Books.example.xml`.

Provider is useful for shared grammar and rendering routines, not a general runtime translation hook. Harmony patches or mod code can route hard-coded and composition-heavy text into localized templates. For any dynamic strings, a targeted proof-of-concept should check UI layout and markup as well as translation correctness.

## 6. Translator debugging and quick test loop

Relevant options in shipped `Options.xml` are gated by `OptionDebugTranslations==Yes`:

- `OptionDebugExampleLanguage`: adds selectable `example` language (restart required per option). The generated example XML is schema/template output, not a real translation.
- `OptionDebugStringTable`: `Strings.DebugEnabled`; renders `_S:`/`_T:` plus context/ID instead of translated text.
- `OptionDebugStringTableMisses`: logs each unique missing lookup as an error to Player.log for non-English active language; `Strings.TryGetString` returns the source ID as fallback.
- `OptionDebugStringTableLoadingChecks`: warns when a translated ID is absent from example Strings files or appears in another Context.

`LanguageXmlProcessor.Run()` regenerates `Base/ExampleLanguage` templates from registered schemas and code `_S/_T` entries. Do not modify the install for a normal mod test; use the user Mods folder, enable the mod, select `简体中文`/`zh`, restart if the option says so, then inspect representative menus, conversations, book pages, item names, and combat output. Check Player.log for XML loader errors and string-table misses. `VariableReplacers` exposes the wish commands `testreplacers` and `testlangreplacers` to exercise replacers; `Grammar` exposes `pluralizetestall`. `GameTextTest` contains expected-output cases for parser behavior (including English articles and conjugation) but is a test class, not an in-game command. No separate translator UI or universal automated missing-key report was found beyond the options above.

## Minimal provider example

See [ZhProvider.example.cs](ZhProvider.example.cs). It demonstrates the provider hook, article suppression, Chinese list separators, and culture. It compiles as a mod assembly against the game's `Assembly-CSharp.dll`; it deliberately does not attempt all Chinese number, name-order, line-breaking, or verb behaviors. Those require deliberate overrides/patches rather than assuming a language code changes English grammar.
