"""Inventory static game strings; candidate flags are NOT translation authorization.

Uses Roslyn for decompiled C#, plus XML (including RPM maps), JSON and text data.
Outputs are local research artifacts. No translations or game files are changed.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = Path.home() / "Library/Application Support/Steam/steamapps/common/Caves of Qud/CoQ.app/Contents/Resources/Data/StreamingAssets/Base"
VISIBLE = {"DisplayName", "DisplayText", "Short", "Description", "Title", "Text", "Message", "Intro", "Prompt", "DescriptionPrefix", "DescriptionPostfix", "BearerDescription", "HelpText", "Verb", "Label", "Unit"}
IDENTIFIERS = {"Name", "ID", "Id", "Key", "Type", "Blueprint", "Owner", "Part", "Class", "Command", "Sound", "Tile", "File", "Path", "Inherits", "Object"}
PROSE = re.compile(r"\b[A-Za-z]{2,}[ ,!?]+[A-Za-z]{2,}\b")


def write_row(stream, row):
    stream.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_jsonc(text):
    # Match strings before comments so URLs and quoted // remain literal text.
    tokens = r'"(?:\\.|[^"\\])*"|//[^\r\n]*|/\*[\s\S]*?\*/'
    text = re.sub(tokens, lambda m: m[0] if m[0].startswith('"') else re.sub(r"[^\r\n]", " ", m[0]), text)
    text = re.sub(r'"(?:\\.|[^"\\])*"|,\s*(?=[}\]])', lambda m: m[0] if m[0].startswith('"') else "", text)
    return json.loads(text)


def parse_game_xml(text):
    # The engine accepts numeric control-character entities forbidden by XML1.0.
    # Substitute during parsing and restore the exact characters in string values.
    restored = {}
    def entity(match):
        token = match[1]
        code = int(token[1:], 16) if token.startswith("x") else int(token)
        if code in (9, 10, 13) or 32 <= code <= 0xD7FF or 0xE000 <= code <= 0xFFFD or 0x10000 <= code <= 0x10FFFF:
            return match[0]
        marker = "__QUD_CONTROL_" + str(len(restored)) + "__"
        if marker in text: raise ValueError("Control-character marker collision")
        restored[marker] = chr(code)
        return marker
    root = ET.fromstring(re.sub(r"&#(x[0-9A-Fa-f]+|[0-9]+);", entity, text))
    if restored:
        def restore(value):
            for marker, original in restored.items(): value = value.replace(marker, original)
            return value
        for el in root.iter():
            el.attrib.update({key: restore(value) for key, value in el.attrib.items()})
            if el.text: el.text = restore(el.text)
            if el.tail: el.tail = restore(el.tail)
    return root


def data_rows(base, failures, counts):
    for file in sorted(base.rglob("*")):
        if not file.is_file() or "ExampleLanguage" in file.relative_to(base).parts:
            continue
        rel = str(file.relative_to(base))
        if file.suffix.lower() not in {".xml", ".rpm", ".json", ".jsonc", ".txt"}:
            counts["unparsed_other_files"] += 1
            continue
        counts["data_files_seen"] += 1
        try:
            if file.suffix.lower() in {".xml", ".rpm"}:
                root = parse_game_xml(file.read_text(encoding="utf-8-sig"))
                yield from xml_rows(root, rel, "/" + root.tag + "[1]")
            elif file.suffix.lower() in {".json", ".jsonc"}:
                def walk(value, path):
                    if isinstance(value, str):
                        yield {"file": rel, "path": path, "kind": "json-string", "src": value, "classification": "corpus-review" if "LibraryCorpus" in rel else "data-review"}
                    elif isinstance(value, dict):
                        for key, child in value.items():
                            child_path = path + "/" + key.replace("~", "~0").replace("/", "~1")
                            yield {"file": rel, "path": child_path, "kind": "json-key", "src": key, "classification": "identifier-review"}
                            yield from walk(child, child_path)
                    elif isinstance(value, list):
                        for i, child in enumerate(value): yield from walk(child, path + "/" + str(i))
                yield from walk(parse_jsonc(file.read_text(encoding="utf-8-sig")), "")
            elif file.suffix.lower() == ".txt":
                for line, text in enumerate(file.read_text(encoding="utf-8-sig").splitlines(), 1):
                    yield {"file": rel, "line": line, "kind": "text-line", "src": text, "classification": "corpus-review" if "Corpus" in rel else "data-review"}
        except (ET.ParseError, ValueError, UnicodeError, OSError) as exc:
            failures.append({"file": rel, "reason": str(exc)})


def xml_rows(element, file, path):
    for attr, value in element.attrib.items():
        role = "unclassified-data"
        if attr in VISIBLE: role = "display-candidate"
        elif attr in IDENTIFIERS: role = "identifier-review"
        elif PROSE.search(value): role = "prose-candidate"
        # Some files use Value for either a UI label or an internal setting.
        if attr == "Value" and element.attrib.get("Name") in VISIBLE: role = "display-candidate"
        yield {"file": file, "path": path + "/@" + attr, "kind": "xml-attribute", "src": value, "classification": role}
    if element.text and element.text.strip():
        yield {"file": file, "path": path + "/text()", "kind": "xml-text", "src": element.text, "classification": "data-review"}
    siblings = collections.Counter()
    for child in element:
        siblings[child.tag] += 1
        yield from xml_rows(child, file, path + "/" + child.tag + "[" + str(siblings[child.tag]) + "]")
        if child.tail and child.tail.strip():
            yield {"file": file, "path": path + "/tail-after/" + child.tag + "[" + str(siblings[child.tag]) + "]", "kind": "xml-tail", "src": child.tail, "classification": "data-review"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--code-dir", type=Path, default=ROOT / "research/decompiled")
    parser.add_argument("--out", type=Path, default=ROOT / "work/text_catalogue")
    args = parser.parse_args()
    if not args.game_base.is_dir() or not args.code_dir.is_dir():
        parser.error("Game data and decompiled C# directories must both exist")
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(["dotnet", "run", "--project", str(ROOT / "tools/text_catalogue/TextCatalogue.csproj"),
                             "--configuration", "Release", "-p:NuGetAudit=false", "--", str(args.code_dir.resolve()),
                             str(out / "code_strings.jsonl")], capture_output=True, text=True, check=True)
    code_summary = json.loads(result.stdout.strip().splitlines()[-1])
    tm = {r["src"]: r["zh"] for r in map(json.loads, (ROOT / "data/tm.jsonl").open())}
    runtime = {}
    for line in (ROOT / "mod/QudZH/runtime_strings.tsv").read_text().splitlines():
        if "\t" in line:
            en, zh = line.split("\t", 1)
            runtime[en.replace("\\n", "\n").replace("\\t", "\t")] = zh
    counts = collections.Counter(); failures = []; candidates = {}; official_count = 0
    def record(row, origin, stream=None):
        text = row["src"]
        if not text.strip() or not any(c.isalpha() for c in text): return
        row = dict(row, origin=origin)
        row["coverage"] = "tm-exact" if text in tm else "runtime-exact" if text in runtime else "unmatched-static"
        if stream: write_row(stream, row)
        counts[origin + "_strings"] += 1
        counts[origin + ":" + row["classification"]] += 1
        if row["classification"] not in {"display-candidate", "prose-candidate", "data-review"}: return
        if row["coverage"] != "unmatched-static": return
        group = candidates.setdefault(text, {"id": hashlib.sha256(text.encode()).hexdigest()[:20], "src": text, "classification": row["classification"], "occurrences": []})
        group["occurrences"].append({k: v for k, v in row.items() if k != "src"})
    with (out / "official_units.jsonl").open("w") as stream:
        for file in sorted((ROOT / "data/source").glob("*.jsonl")):
            for row in map(json.loads, file.open()):
                write_row(stream, row); official_count += 1
    for row in map(json.loads, (out / "code_strings.jsonl").open()): record(row, "code")
    with (out / "data_strings.jsonl").open("w") as stream:
        for row in data_rows(args.game_base, failures, counts): record(row, "data", stream)
    with (out / "review_candidates.jsonl").open("w") as stream:
        for text in sorted(candidates): write_row(stream, candidates[text])
    summary = {"code": code_summary, "official_units_including_history": official_count,
               "counts": dict(sorted(counts.items())), "unique_unmatched_review_candidates": len(candidates),
               "data_parse_gaps": failures,
               "limits": ["Candidates require review; they include false positives and existing runtime-template matches.",
                          "Coverage is exact-text membership, not verified in-game reachability or rendered coverage.",
                          "No Unity asset/binary, downloaded workshop mod, or generated runtime text scan.",
                          "C# parse errors are reported; syntax extraction does not require a successful game compilation.",
                          "Generated templates and concatenation holes are proposals, never automatically installed."]}
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__": main()
