"""Emit context and matching established terminology for text-only translators."""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
glossary = []
for line in (ROOT / "docs/glossary.tsv").read_text().splitlines():
    parts = re.split(r"\\t|\t", line)
    if len(parts) > 1 and parts[0]: glossary.append(parts[:2])
terms = []
for line in (ROOT / "data/tm.jsonl").read_text().splitlines():
    row = json.loads(line)
    if 3 <= len(row["src"]) <= 40 and re.fullmatch(r"[A-Za-z][A-Za-z '\-]+", row["src"]):
        terms.append([row["src"], row["zh"]])
result = {}
anatomy_usage = {}
if any(name.startswith("CTB") for name in sys.argv[1:]):
    from extract_catalogue import DEFAULT_BASE, parse_game_xml
    for anatomy in parse_game_xml((DEFAULT_BASE / "Bodies.xml").read_text(encoding="utf-8-sig")).iter("anatomy"):
        for part_type in {node.get("Type") for node in anatomy.iter()} - {None}:
            anatomy_usage.setdefault(part_type, []).append(anatomy.get("Name"))
for name in sys.argv[1:]:
    rows = [json.loads(line) for line in (ROOT / "work/catalogue_translation/batches" / (name + ".jsonl")).read_text().splitlines()]
    text = "\n".join(r["src"] for r in rows)
    for row in rows:
        if row["id"].startswith("bodydesc-"):
            row["anatomy_examples"] = anatomy_usage.get(row["src"], [])[:8]
    def matches(entries):
        return sorted([item for item in entries if re.search(r"(?<![A-Za-z])" + re.escape(item[0]) + r"(?![A-Za-z])", text, re.I)], key=lambda x: -len(x[0]))[:60]
    result[name] = {"units": [{"id": r["id"], "src": r["src"], "context": r["context"],
                              **({"anatomy_examples": r["anatomy_examples"]} if "anatomy_examples" in r else {})} for r in rows],
                    "glossary": matches(glossary), "existing_terms": matches(terms)}
print(json.dumps(result, ensure_ascii=False))
