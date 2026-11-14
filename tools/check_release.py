"""Validate shipped mod files without requiring a local game installation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from package import MOD, mod_files

VERSION = re.compile(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\Z")
REQUIRED = {"manifest.json", "Languages.xml", "Strings.xml", "Strings.Conversations.xml",
            "historyspice.zh.json", "runtime_strings.tsv", "anatomy_labels.tsv",
            "Scripts/ZhProvider.cs", "Scripts/ZhRuntime.cs", "Scripts/ZhText.cs"}


def validate_mod(source: Path = MOD, tag: str | None = None) -> tuple[str, int]:
    files = mod_files(source)
    names = {p.relative_to(source).as_posix() for p in files}
    missing = REQUIRED - names
    if missing:
        raise ValueError("Missing required mod files: " + ", ".join(sorted(missing)))
    for path in files:
        if path.suffix.lower() == ".xml":
            ET.parse(path)
        elif path.suffix.lower() == ".json":
            json.loads(path.read_text(encoding="utf-8-sig"))
        elif path.suffix.lower() in {".tsv", ".cs", ".md", ".txt"}:
            text = path.read_text(encoding="utf-8-sig")
            if path.suffix.lower() == ".tsv":
                for number, row in enumerate(text.splitlines(), 1):
                    if row and (row.count("\t") != 1 or not all(row.split("\t"))):
                        raise ValueError(f"Invalid translation row: {path.name}:{number}")
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8-sig"))
    if manifest.get("ID") != "QudZH":
        raise ValueError("The release manifest ID must be QudZH")
    version = manifest.get("Version", "")
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        raise ValueError("Manifest Version must be a stable X.Y.Z version")
    if tag is not None and tag != "v" + version:
        raise ValueError(f"Release tag {tag!r} does not match manifest version v{version}")
    languages = ET.parse(source / "Languages.xml").getroot()
    if not any(node.get("Code") == "zh" for node in languages.iter("lang")):
        raise ValueError("Languages.xml must register the zh language")
    return version, len(files)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", help="Require this exact release tag to match the manifest")
    args = parser.parse_args()
    version, count = validate_mod(tag=args.tag)
    print(f"PASS: QudZH {version}, {count} distributable files")


if __name__ == "__main__":
    main()
