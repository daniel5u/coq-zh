"""Build language-only XML overlays for explicitly approved catalogue fields.

Verified loader contracts: DataManager.CacheFile (Lang/LoadPriority),
ObjectBlueprintLoader.ReadObjectBlueprintsXML (Load=Merge),
CommandBindingManager.HandleCommandNode and SkillFactory (ID/Name merges).
"""
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from extract_catalogue import DEFAULT_BASE, ROOT, parse_game_xml

OUT = ROOT / "mod/QudZH"
ALLOWED = {
    ("objects", "object", "part"): {"Text", "Short", "DisplayName", "BehaviorDescription"},
    ("commands", "command"): {"DisplayText", "ConsoleDisplayText"},
    ("skills", "skill", "power"): {"Description", "DisplayName", "Snippet"},
    ("skills", "skill"): {"Description", "DisplayName", "Snippet"},
    ("bodies", "bodyparttypevariants", "bodyparttypevariant"): {"Description", "DescriptionPrefix"},
    ("bodies", "bodyparttypes", "bodyparttype"): {"Description", "DescriptionPrefix"},
}


def field_allowed(chain, attr, owners):
    verified = {"Impaler": {"Message"}, "Food": {"Message"}, "FusionReactor": {"Description"},
                "FallsApart": {"Message"}, "ItemConvertor": {"Verb"}}
    return attr in ALLOWED.get(chain, set()) or (
        chain == ("objects", "object", "part") and
        attr in verified.get(owners[-1].get("Name"), set()))


def identity(owner):
    if owner["tag"] in {"bodyparttypevariants", "bodyparttypes"}: return {}
    if owner["tag"] == "bodyparttypevariant":
        return {"Type": owner["Type"], "VariantOf": owner["VariantOf"]}
    if owner["tag"] == "bodyparttype": return {"Type": owner["Type"]}
    key = "ID" if owner["tag"] == "command" else "Name"
    if key not in owner: raise ValueError("Missing merge key: " + str(owner))
    return {key: owner[key]}


def find_node(root, owners):
    node = root
    for owner in owners[1:]:
        keys = identity(owner)
        node = next((x for x in node if x.tag == owner["tag"] and all(x.get(k) == v for k, v in keys.items())), None)
        if node is None: return None
    return node


def resolve(root, path):
    node = root
    steps = path.split("/")[2:]
    for step in steps:
        if step.startswith("@"): return node, step[1:]
        match = re.fullmatch(r"([^\[]+)\[(\d+)\]", step)
        if not match: raise ValueError("Unsupported path: " + path)
        node = [x for x in node if x.tag == match[1]][int(match[2]) - 1]
    raise ValueError("Expected an attribute path")


def annotate_context(context, cache):
    """Attach source merge keys, never translatable values, to XML context."""
    if context.get("origin") != "data" or not context.get("path", "").startswith("/"): return
    path = DEFAULT_BASE / context["file"]
    if path.suffix not in {".xml", ".rpm"}: return
    if path not in cache: cache[path] = parse_game_xml(path.read_text(encoding="utf-8-sig"))
    node = cache[path]; owners = []
    for step in context["path"].split("/")[1:]:
        match = re.fullmatch(r"([^\[]+)\[(\d+)\]", step)
        if not match: break
        if owners or match[1] != node.tag:
            node = [child for child in node if child.tag == match[1]][int(match[2]) - 1]
        owners.append({"tag": node.tag, **{k: v for k,v in node.attrib.items() if k in {"Name", "ID", "Class", "Key", "Type", "VariantOf"}}})
    context["owner"] = owners


def build():
    accepted = [json.loads(line) for line in (ROOT / "data/catalogue_zh.jsonl").read_text().splitlines()]
    existing = []
    for path in sorted(OUT.glob("*.xml")):
        if not path.name.startswith("Catalogue_"): existing.append(ET.parse(path).getroot())
    source_cache = {}; roots = {}; report = []
    for record in accepted:
        if not record.get("install_xml"): continue
        for context in record["context"]:
            if context.get("origin") != "data" or not context.get("owner"): continue
            owners = context["owner"]; chain = tuple(o["tag"] for o in owners)
            attr = context["path"].rsplit("/@", 1)[-1]
            event = {"id": record["id"], "file": context["file"], "path": context["path"]}
            if not field_allowed(chain, attr, owners):
                report.append(dict(event, status="unsupported-field")); continue
            source_path = DEFAULT_BASE / context["file"]
            if source_path not in source_cache: source_cache[source_path] = parse_game_xml(source_path.read_text(encoding="utf-8-sig"))
            source_node, source_attr = resolve(source_cache[source_path], context["path"])
            original = source_node.get(source_attr)
            implicit_anatomy = (chain in {
                ("bodies", "bodyparttypes", "bodyparttype"),
                ("bodies", "bodyparttypevariants", "bodyparttypevariant")} and
                source_attr == "Description" and original is None and
                context.get("fallback", {}).get("source_attribute") == "Type" and
                source_node.get("Type") == record["src"])
            if original != record["src"] and not implicit_anatomy:
                raise ValueError("Stale catalogue source: " + str(event))
            for root in existing:
                if root.tag != chain[0]: continue
                previous = find_node(root, owners)
                if previous is not None and re.search(r"[㐀-鿿]", previous.get(attr, "")):
                    report.append(dict(event, status="already-localized")); break
            else:
                root = roots.setdefault(chain[0], ET.Element(chain[0], Lang="zh", LoadPriority="-1100"))
                node = root
                for owner in owners[1:]:
                    keys = identity(owner)
                    child = next((x for x in node if x.tag == owner["tag"] and all(x.get(k) == v for k,v in keys.items())), None)
                    if child is None:
                        child = ET.SubElement(node, owner["tag"], keys)
                        if owner["tag"] == "object": child.set("Load", "Merge")
                    node = child
                if attr in node.attrib and node.get(attr) != record["zh"]: raise ValueError("Conflicting overlay value")
                node.set(attr, record["zh"])
                report.append(dict(event, status="generated"))
    for name, root in roots.items():
        ET.indent(root)
        ET.ElementTree(root).write(OUT / ("Catalogue_" + name + ".xml"), encoding="utf-8", xml_declaration=True)
    # Keep previous generated filenames inert if later approval revocations empty a root.
    for path in OUT.glob("Catalogue_*.xml"):
        name = path.stem.removeprefix("Catalogue_")
        if name not in roots:
            ET.ElementTree(ET.Element(name, Lang="zh", LoadPriority="-1100")).write(path, encoding="utf-8", xml_declaration=True)
    (ROOT / "work/catalogue_translation/xml_integration.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    from collections import Counter
    print("Catalogue XML:", dict(Counter(r["status"] for r in report)))
    return roots, report


if __name__ == "__main__": build()
