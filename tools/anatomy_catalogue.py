"""Catalogue visible anatomy descriptions that default to internal Type names."""
import hashlib
import json
from pathlib import Path

from catalogue_translate import WORK, write
from catalogue_overlays import annotate_context
from extract_catalogue import DEFAULT_BASE, parse_game_xml

source = DEFAULT_BASE / "Bodies.xml"
root = parse_game_xml(source.read_text(encoding="utf-8-sig"))
rows = []; cache = {source: root}
for collection in ["bodyparttypes", "bodyparttypevariants"]:
    group = root.find(collection)
    if group is None: continue
    counts = {}
    for node in group:
        counts[node.tag] = counts.get(node.tag, 0) + 1
        if node.tag not in {"bodyparttype", "bodyparttypevariant"} or node.get("Description") is not None: continue
        text = node.get("Type")
        if not text: continue
        context = {"origin": "data", "file": "Bodies.xml", "kind": "implicit-anatomy-description",
                   "path": f"/bodies[1]/{collection}[1]/{node.tag}[{counts[node.tag]}]/@Description",
                   "fallback": {"source_attribute": "Type", "reason": "Anatomies and BodyPartType default Description to Type when absent."}}
        annotate_context(context, cache)
        rows.append({"id": "bodydesc-" + hashlib.sha256(text.encode()).hexdigest()[:16],
                     "src": text, "priority": 2, "context": [context]})
for start in range(0, len(rows), 24):
    name = f"CTB{start // 24 + 1:03}"
    path = WORK / "batches" / (name + ".jsonl")
    if not path.exists(): write(path, rows[start:start + 24])
(WORK / "anatomy_manifest.json").write_text(json.dumps({"units": len(rows), "batch_size": 24,
                                                      "source": str(source), "target_attribute": "Description"}, indent=2) + "\n")
print(f"Prepared {len(rows)} implicit anatomy labels in {(len(rows) + 23) // 24} batches; Type/VariantOf stay unchanged.")
