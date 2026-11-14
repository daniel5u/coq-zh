# Translator agent brief — Caves of Qud Simplified Chinese (QudZH)

Work from the repository root. You translate English game text into Simplified Chinese.

## Read first (mandatory)
1. `docs/STYLE_GUIDE.md` — register, markup rules, punctuation. Follow it strictly.
2. `docs/glossary.tsv` — the binding terminology list (en → zh). Each batch also has `work/batches/<NAME>.glossary.tsv` with the glossary entries that occur in that batch.
3. The game's text is literary and archaic; preserve that flavor (see the guide). UI text stays concise and modern.

## Input
`work/batches/<NAME>.jsonl` — one JSON object per line:
- `id`: unit id (copy it to output unchanged)
- `src`: the English text to translate
- `file`, `tag`, `attr`, `where`, `ctx`, `key`: context only (which game file/XML element/attribute; `ctx` is the developer's usage context; for conversations `ctx` is `Conversation <Speaker>.<Node>.<Field>`).
- `prefix_literal` (rare): structural text that precedes `src` in the game file; do not include it in your output.

## Output
Write `work/out/<NAME>.jsonl`: exactly one line per input unit, in any order:
`{"id": "<id>", "zh": "<Chinese translation>"}`
- Valid JSON per line (UTF-8, `ensure_ascii=False` is fine). Escape newlines in strings as `\n` inside JSON.
- Translate every unit yourself, with full attention to context. Do NOT call external translation APIs or MT tools. You may use a small Python script just to write the JSON file.
- Units in a batch are in game order; neighbouring units (same conversation, same book, same creature) give context — use it.

## Validate (mandatory)
Run: `python3 tools/check_batch.py work/batches/<NAME>.jsonl work/out/<NAME>.jsonl`
Fix every `ERROR` and re-run until it exits with 0 errors. Read the `warn` lines and fix them when they show a real problem (e.g. untranslated English left in output).

## Key rules recap
- Keep `=...=` variables, `{{X|...}}` markup, `[[...]]`, `&X`/`^X` color codes, `~`, `|`, `::` exactly. Delete `=verb:...=` tokens and write the Chinese verb instead.
- Comma-list attributes (PoeticFeatures, Activity, SacredThing, …): ASCII `,` separators, same item count.
- Use glossary terms. For new proper nouns, follow the guide's transliteration rules (和合本 for biblical names; meaning-based for descriptive names).
- Full-width Chinese punctuation in prose, `……` for `...`.

## Glossary proposals
If you coin a translation for a recurring proper noun / game term that is NOT in `docs/glossary.tsv`, append it to `work/glossary_proposals/<NAME>.tsv` as `en<TAB>zh<TAB>note` lines (no header). Do not edit `docs/glossary.tsv` yourself.

## Do not
- Do not edit anything outside `work/out/` and `work/glossary_proposals/`.
- Do not skip units, merge units, or add notes inside translations.
- Do not run git commands.

## When finished
Reply with: batch names done, unit counts, final check_batch result, and any notable doubts (≤10 lines).
