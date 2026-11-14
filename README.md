<img src="assets/icon.svg" width="64" height="64" alt="">

# QudZH — 《卡德洞窟》简体中文汉化

A complete Simplified Chinese translation mod for **Caves of Qud**, built on the official `lang-experimental` localization framework.

## What it covers

| Area | Coverage |
|---|---|
| Official translatable text (`StreamingAssets/Base/ExampleLanguage`, 41 files) | **26,194 / 26,194 units (100%)** |
| Procedural history phrase bank (`HistorySpice` → `historyspice.zh.json`) — sultan gospels, village histories, gossip, tombstones, recipes | 5,222 / 5,222 |
| Procedural name generator (`Naming.xml`) | 100% — syllable-level transliteration + meaning-based epithets |
| Pronouns and kinship terms (`Genders.xml`, `PronounSets.xml`) | Chinese 他/她/它/TA, 父亲/母亲… |
| Runtime grammar (C# `ZhProvider` + Harmony patches) | CJK line wrapping, no English articles, Chinese lists/numbers, no English pluralisation/conjugation on Chinese words |

Style: classical-flavoured written Chinese (半文半白, 雅而不涩，古而不僻) for lore, descriptions and books; plain modern Chinese for UI. Biblical/Semitic names follow the Chinese Union Version (和合本): 约帕 Joppa, 各各他 Golgotha, 拿非利人 Nephilim, 利悉 Resheph. See [docs/STYLE_GUIDE.md](docs/STYLE_GUIDE.md) and the ~1,600-entry terminology list [docs/glossary.tsv](docs/glossary.tsv).

## Install

1. Steam → Caves of Qud → Properties → Betas → select **`lang-experimental`**.
2. Download `QudZH.zip` from the [latest release](https://github.com/daniel5u/coq-zh/releases/latest) (or use `mod/QudZH` from this repository) and extract the `QudZH` folder into your mods folder:
   - macOS: `~/Library/Application Support/com.FreeholdGames.CavesOfQud/Mods/QudZH`
   - Windows: `%USERPROFILE%\AppData\LocalLow\Freehold Games\CavesOfQud\Mods\QudZH`
   - Linux: `~/.config/unity3d/Freehold Games/CavesOfQud/Mods/QudZH`
3. Launch the game → **Mods** → enable **卡德洞窟 简体中文 (QudZH)**. Disable any other Chinese language mod (two `zh` packs conflict).
4. **Options → Language → 简体中文**, then restart.
5. The mod ships C# scripts (`Scripts/`): allow script mods when the game asks.

## Repository layout

```
mod/QudZH/            the built mod (what you install)
  *.xml               language overlays (Lang="zh"), generated
  historyspice.zh.json
  Genders.xml         Chinese pronouns/kin terms
  Scripts/            ZhProvider.cs, ZhGrammarPatches.cs, ZhText.cs
docs/                 STYLE_GUIDE, glossary, agent prompts
data/source/          extracted English units (from ExampleLanguage)
data/tm.jsonl         translation memory (English → Chinese), the source of truth
data/overrides.json   per-unit overrides where identical English needs different Chinese
tools/                extract / batch / validate / ingest / build pipeline
research/             engine research (ENGINE_REPORT.md), decompiled sources (git-ignored)
```

## Rebuilding

```bash
python3 tools/extract.py          # re-extract after a game update
python3 tools/spice.py extract
python3 tools/build.py            # writes mod/QudZH and reports coverage
python3 tools/qa.py               # untranslated + glossary-consistency report (allowlist: docs/qa_allow.tsv)
python3 tools/recheck_tm.py       # re-validate every translation
bash tools/package.sh             # rebuild dist/QudZH.zip for distribution
```

New/changed strings after a game update: `python3 tools/make_batches.py <group> <PREFIX> 12000`, translate `work/batches/*.jsonl` per `docs/AGENT_BRIEF.md`, then `tools/ingest_ready.sh`.

To inventory text beyond the official language files, run `python3 tools/extract_catalogue.py`
with the installed .NET 11 SDK. This uses Roslyn to scan decompiled C# and reads XML,
RPM maps, JSON/JSONC and text files. Local results are in `work/text_catalogue/`:
raw strings, official units, deduplicated review candidates and `summary.json`.
Candidates are research inputs, not verified untranslated text or installable patches.
See [docs/TEXT_EXTRACTION_SCOPE.md](docs/TEXT_EXTRACTION_SCOPE.md) for coverage limits.

## Known limitations

- Runtime templates translate additional C# text, including mutation descriptions. Hard-coded phrases outside those templates can still appear in English.
- `LibraryCorpus.json` (Markov-generated book text) is not translated.
- Not yet play-tested end to end; please report rendering issues (especially generated combat messages and procedural history sentences).

## Steam Workshop sync

GitHub is the source of truth for the Workshop item: `tools/workshop.py` uploads exactly the files
in the release ZIP, with the title, description and preview from `mod/QudZH/workshop.json`.

```bash
python3 tools/workshop.py --dry-run                     # show what would be uploaded
STEAM_USERNAME=<account> python3 tools/workshop.py       # upload (SteamCMD must have a cached login)
```

The first upload creates the item and writes its `WorkshopId` into `workshop.json`; commit that file.
Each later `vX.Y.Z` tag also updates the item from CI (`workshop` job) when the `steam-workshop`
environment has the secrets `STEAM_USERNAME` and `STEAM_CONFIG_VDF` (base64 of a logged-in
SteamCMD `config.vdf`). Without them the job is skipped.

## License

Original code is [MIT](LICENSE). Original Chinese translations and project documentation are [CC BY-SA 4.0](LICENSES/CC-BY-SA-4.0.txt). *Caves of Qud* game text and other third-party material keep their own rights. See [NOTICE.md](NOTICE.md).

This is an unofficial fan translation, not affiliated with Freehold Games or Kitfox Games.
