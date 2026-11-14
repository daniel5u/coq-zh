"""Prepare/review catalogue translations without promoting internal keys to runtime text.

prepare: create stable, small context-bearing batches; check BATCH: validate agent output.
"""
import collections
import json
from pathlib import Path
import re
import sys

from validate import check

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work/catalogue_translation"


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))


def prepare():
    if (WORK / "manifest.json").exists():
        print("Existing manifest preserved; use its pending batches.")
        return
    candidates = read(ROOT / "work/text_catalogue/review_candidates.jsonl")
    tm = {r["src"] for r in read(ROOT / "data/tm.jsonl")}
    runtime = {line.split("\t", 1)[0].replace("\\n", "\n").replace("\\t", "\t")
               for line in (ROOT / "mod/QudZH/runtime_strings.tsv").read_text().splitlines() if "\t" in line}
    def priority(row):
        occurrences = row["occurrences"]
        if any(o.get("classification") == "display-candidate" and re.search(r"(?:Popup\.|MessageQueue\.)", o.get("call", "")) for o in occurrences): return 0
        if any(o.get("classification") == "display-candidate" and o.get("origin") == "code" for o in occurrences): return 1
        if any(o.get("classification") == "display-candidate" for o in occurrences): return 2
        return 3
    rows = []
    for candidate in sorted(candidates, key=lambda r: (priority(r), r["id"])):
        if candidate["src"] in tm or candidate["src"] in runtime: continue
        context = sorted(candidate["occurrences"], key=lambda o: o.get("classification") != "display-candidate")[:2]
        rows.append({"id": candidate["id"], "src": candidate["src"], "priority": priority(candidate), "context": context})
    batches = []; current = []; chars = 0
    for row in rows:
        if current and (len(current) >= 55 or chars + len(row["src"]) > 6500):
            name = f"CT{len(batches) + 1:04}"
            write(WORK / "batches" / (name + ".jsonl"), current)
            batches.append({"name": name, "units": len(current), "characters": chars, "status": "pending"})
            current = []; chars = 0
        current.append(row); chars += len(row["src"])
    if current:
        name = f"CT{len(batches) + 1:04}"
        write(WORK / "batches" / (name + ".jsonl"), current)
        batches.append({"name": name, "units": len(current), "characters": chars, "status": "pending"})
    (WORK / "out").mkdir(exist_ok=True)
    (WORK / "manifest.json").write_text(json.dumps({"units": len(rows), "batches": batches}, indent=2) + "\n")
    print(f"Prepared {len(rows)} review units in {len(batches)} batches; {sum(r['priority'] == 0 for r in rows)} popup/log candidates first.")


def validate_batch(name):
    units = {r["id"]: r for r in read(WORK / "batches" / (name + ".jsonl"))}
    output = read(WORK / "out" / (name + ".jsonl"))
    errors = []; seen = set(); counts = collections.Counter()
    for row in output:
        identity = row.get("id")
        if identity not in units or identity in seen:
            errors.append(f"unknown/duplicate id: {identity}"); continue
        seen.add(identity); status = row.get("status")
        counts[status] += 1
        if status not in {"translate", "review", "skip"}:
            errors.append(f"{identity}: invalid status"); continue
        if status != "translate":
            if not row.get("reason"): errors.append(f"{identity}: review/skip needs reason")
            continue
        src = units[identity]["src"]; zh = row.get("zh")
        issues, _ = check({"src": src}, zh)
        if isinstance(zh, str):
            if collections.Counter(re.findall(r"\{\d+[^{}]*\}", src)) != collections.Counter(re.findall(r"\{\d+[^{}]*\}", zh)):
                issues.append("C# placeholder mismatch")
            if src.count("\n") != zh.count("\n"): issues.append("newline count mismatch")
            def literals(text):
                text = re.sub(r"\{\d+[^{}]*\}", "", text)
                return collections.Counter(re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?", text))
            required, actual = literals(src), literals(zh)
            if any(actual[n] < count for n, count in required.items()): issues.append("source numeric literal missing")
        errors.extend(f"{identity}: {issue}" for issue in issues)
    errors.extend(f"missing id: {identity}" for identity in units.keys() - seen)
    for error in errors: print(error)
    print(name, dict(counts), f"{len(errors)} errors")
    return len(errors)


def ingest(name):
    """Only coordinator-approved records enter the catalogue/runtime bank."""
    if validate_batch(name): raise SystemExit("Fix batch validation before ingestion")
    units = {r["id"]: r for r in read(WORK / "batches" / (name + ".jsonl"))}
    outputs = {r["id"]: r for r in read(WORK / "out" / (name + ".jsonl"))}
    decisions = json.loads((WORK / "reviews" / (name + ".json")).read_text())
    path = ROOT / "data/catalogue_zh.jsonl"
    catalogue = {r["id"]: r for r in read(path)} if path.exists() else {}
    accepted = 0
    for identity, output in outputs.items():
        decision = decisions.get(identity)
        if output["status"] == "translate" and not decision:
            raise SystemExit("Unreviewed translation: " + identity)
        if not decision or decision["action"] != "accept":
            if decision: catalogue.pop(identity, None)  # Revocations must reach the runtime bank.
            continue
        src = units[identity]["src"]; zh = decision.get("zh", output.get("zh"))
        errors, _ = check({"src": src}, zh)
        if errors: raise SystemExit(str(errors))
        if collections.Counter(re.findall(r"\{\d+[^{}]*\}", src)) != collections.Counter(re.findall(r"\{\d+[^{}]*\}", zh)):
            raise SystemExit("Approved placeholder mismatch: " + identity)
        if src.count("\n") != zh.count("\n"): raise SystemExit("Approved newline mismatch")
        install = decision.get("install_runtime", False)
        if install and ("\t" in src or "\t" in zh or "#" in src):
            raise SystemExit("Runtime encoding requires engineering review: " + identity)
        catalogue[identity] = {"id": identity, "src": src, "zh": zh, "batch": name,
                               "model": decision.get("translation_model", "gpt-6-luna"), "reviewed": True,
                               "install_runtime": install, "context": units[identity]["context"]}
        if "translation_model" not in decision:
            catalogue[identity]["reasoningEffort"] = "low"
        catalogue[identity]["install_xml"] = decision.get("install_xml", False)
        accepted += 1
    write(path, [catalogue[k] for k in sorted(catalogue)])
    bank = ROOT / "work/runtime/catalogue_reviewed.tsv"
    def escape(value): return value.replace("\n", "\\n")
    bank.write_text("#! Coordinator-reviewed catalogue translations only\n" + "".join(
        escape(r["src"]) + "\t" + escape(r["zh"]) + "\n" for r in sorted(catalogue.values(), key=lambda r: r["src"]) if r["install_runtime"]))
    print(f"{name}: {accepted} reviewed translations accepted; catalogue total {len(catalogue)}")


def safe_next(name, count, priority=0):
    target = WORK / "batches" / (name + ".jsonl")
    if target.exists(): raise SystemExit("Batch already exists; refusing overwrite")
    originals = sorted((WORK / "batches").glob("CT[0-9][0-9][0-9][0-9].jsonl"))
    reserved = {row["id"] for path in (WORK / "batches").glob("*.jsonl")
                if path not in originals for row in read(path)}
    concatenations = {(r["file"], r["line"]) for r in read(ROOT / "work/text_catalogue/code_strings.jsonl")
                      if r["kind"] == "concatenation-candidate"}
    selected = []
    source_cache = {}; existing_xml = []
    triage_path = WORK / "auto_triage.jsonl"
    triaged = {r["id"]: r for r in read(triage_path)} if triage_path.exists() else {}
    if priority == 2:
        from catalogue_overlays import annotate_context, find_node, field_allowed, OUT, DEFAULT_BASE
        import xml.etree.ElementTree as ET
        existing_xml = [ET.parse(p).getroot() for p in OUT.glob("*.xml") if not p.name.startswith("Catalogue_")]
    for path in originals:
        for row in read(path):
            if row["id"] in reserved or row["id"] in triaged or row["priority"] != priority: continue
            if priority == 2:
                localized = []
                for context in row["context"]:
                    annotate_context(context, source_cache)
                    owners = context.get("owner", []); chain = tuple(o["tag"] for o in owners)
                    attr = context.get("path", "").rsplit("/@", 1)[-1]
                    found = False
                    if field_allowed(chain, attr, owners):
                        for root in existing_xml:
                            if root.tag != chain[0]: continue
                            node = find_node(root, owners)
                            if node is not None and re.search(r"[㐀-鿿]", node.get(attr, "")): found = True; break
                    localized.append(found)
                if row["context"] and all("pronoungeneration" in c.get("path", "").lower() for c in row["context"]):
                    triaged[row["id"]] = {"id": row["id"], "status": "internal-pronoun-generation", "context": row["context"]}
                    continue
                if row["src"].startswith("[") and row["src"].endswith("]"):
                    abstract = []
                    for context in row["context"]:
                        owners = context.get("owner", [])
                        if len(owners) < 2 or owners[0]["tag"] != "objects": abstract.append(False); continue
                        obj = find_node(source_cache[DEFAULT_BASE / context["file"]], owners[:2])
                        abstract.append(obj is not None and any(x.tag == "tag" and x.get("Name") == "BaseObject" and x.get("Value", "true").lower() not in {"false", "0"} for x in obj))
                    if abstract and all(abstract):
                        triaged[row["id"]] = {"id": row["id"], "status": "base-archetype-placeholder", "context": row["context"]}
                        continue
                if localized and all(localized):
                    triaged[row["id"]] = {"id": row["id"], "status": "already-localized-field", "context": row["context"]}
                    continue
            ctx = row["context"][0]; src = row["src"]
            if re.search(r"Wish|Debug|Test", ctx.get("file", "") + " " + ctx.get("member", "")): continue
            if ctx.get("kind") == "literal" and (ctx.get("file"), ctx.get("line")) in concatenations: continue
            if any(re.search(r"(?:^|\.)(?:does|Does|verb|GetVerb)\(|\.[Ii]s\b", h) for h in ctx.get("holes", [])): continue
            if src != src.strip() or (priority != 2 and not re.search(r"[.!?]$", src)): continue
            if len(src) > 4000: continue  # Long prose gets separate literary batches.
            if not re.search(r"[A-Za-z]{3}", src) or src.count("{{") != src.count("}}"): continue
            selected.append(row)
            if len(selected) == count:
                write(target, selected)
                if priority == 2: write(triage_path, triaged.values())
                print(f"{name}: {len(selected)} tier-{priority} candidates reserved"); return
    if selected: write(target, selected)
    if priority == 2: write(triage_path, triaged.values())
    print(f"{name}: {len(selected)} tier-{priority} candidates remaining")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "prepare": prepare()
    elif len(sys.argv) == 3 and sys.argv[1] == "check": sys.exit(bool(validate_batch(sys.argv[2])))
    elif len(sys.argv) == 3 and sys.argv[1] == "ingest": ingest(sys.argv[2])
    elif len(sys.argv) == 4 and sys.argv[1] == "safe-next": safe_next(sys.argv[2], int(sys.argv[3]))
    elif len(sys.argv) == 4 and sys.argv[1] == "safe-descriptions": safe_next(sys.argv[2], int(sys.argv[3]), priority=1)
    elif len(sys.argv) == 4 and sys.argv[1] == "safe-data": safe_next(sys.argv[2], int(sys.argv[3]), priority=2)
    elif len(sys.argv) == 5 and sys.argv[1] == "show":
        rows = read(WORK / "batches" / (sys.argv[2] + ".jsonl"))
        start, count = int(sys.argv[3]), int(sys.argv[4])
        for row in rows[start:start + count]:
            print(json.dumps(row, ensure_ascii=False))
        print(f"Records {start}..{min(start + count, len(rows)) - 1}; total {len(rows)}")
    else: raise SystemExit("Usage: catalogue_translate.py prepare | check BATCH | show BATCH START COUNT")
