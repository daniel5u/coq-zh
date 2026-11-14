# Catalogue translation batches

Read `docs/STYLE_GUIDE.md` and consult `docs/glossary.tsv` (or `tools/lookup.py`) before translating. Existing terminology wins. UI/log text uses concise modern Chinese; descriptions and lore retain 典雅书面语、半文半白、雅而不涩，古而不僻. Preserve the game's dry wit and biblical names. Do not flatten ornate prose or invent details. A game round is 回合.

Inputs: `work/catalogue_translation/batches/CTxxxx.jsonl`. Each record contains source, stable ID and extracted context. Inspect nearby lines in `research/decompiled/<file>` when context is ambiguous. The catalogue is intentionally broad: not every candidate is visible or safely translatable.

Read eight records at a time with `python3 tools/catalogue_translate.py show CTxxxx 0 8`, then starts 8, 16, 24, etc. Write or append each completed chunk immediately. If tool output is truncated, request fewer records or narrower source excerpts and continue; truncation does not mean the input is inaccessible. Do not stop without output because an initial read was too large.

Write exactly one output record per input ID to `work/catalogue_translation/out/CTxxxx.jsonl`:

- `{"id":"...","status":"translate","zh":"..."}` for complete visible phrases/templates or independently meaningful labels. This is still a proposal subject to coordinator review.
- `{"id":"...","status":"review","reason":"...","zh":"optional draft"}` for incomplete concatenation fragments, unclear context, composite formatting needing engineering, or text that cannot safely stand alone. Do not reconstruct missing words or replace variables with invented names.
- `{"id":"...","status":"skip","reason":"..."}` for internal IDs/localization keys, paths, programming expressions, debug/wish output, exceptions or already-covered text. Explain the specific reason.

Preserve `{0}`/`{1}` placeholders, their counts, color openers/closers, ASCII structural separators, newlines and significant surrounding whitespace. Preserve `#` characters. Keep `=...=` token names; localize verb/counted-noun parameters only as specified in STYLE_GUIDE. Never translate control IDs, sound names, required confirmation words, file extensions or key bindings. Use context to distinguish displayed labels from internal keys. Preserve markup identifiers even when they are English words.

Do not edit TM, glossary, source batches, runtime files or another agent's output. Do not build, deploy, commit or spawn subagents. Translate the assigned batches yourself; no external translation services. Validate each batch with `python3 tools/catalogue_translate.py check CTxxxx`; fix all errors. If a real source constraint prevents validation, classify the record as review with a clear reason rather than corrupting a token.

Finish all assigned batches before your final reply. Report per batch: translated/review/skip counts and validation status.
