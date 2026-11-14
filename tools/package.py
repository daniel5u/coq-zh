"""Create a deterministic installable ZIP from the committed mod directory."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "mod" / "QudZH"
ALLOWED_SUFFIXES = {".xml", ".json", ".tsv", ".cs", ".md", ".txt", ".png", ".jpg", ".jpeg"}
ALLOWED_NAMES = {"LICENSE", "NOTICE", "COPYING"}
IGNORED_PARTS = {"__pycache__", "bin", "obj"}


def mod_files(source: Path) -> list[Path]:
    """Reject links and unexpected payloads; skip local editor/build debris."""
    if source.is_symlink() or not source.is_dir():
        raise ValueError(f"Mod directory is missing or is a symlink: {source}")
    files = []
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if any(part.startswith(".") or part in IGNORED_PARTS for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError(f"Symlinks cannot be packaged: {relative}")
        if not path.is_file():
            continue
        if path.suffix.lower() not in ALLOWED_SUFFIXES and path.name not in ALLOWED_NAMES:
            raise ValueError(f"Unexpected mod payload: {relative}")
        files.append(path)
    if not files:
        raise ValueError("The mod contains no distributable files")
    return files


def package(source: Path = MOD, output: Path = ROOT / "dist" / "QudZH.zip") -> Path:
    """ZIP bytes do not depend on source timestamps, permissions, or path names."""
    source, output = source.resolve(), output.resolve()
    if output == source or source in output.parents:
        raise ValueError("Archive output must be outside the mod directory")
    files = mod_files(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, suffix=".zip", delete=False) as temp:
        temporary = Path(temp.name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in files:
                name = "QudZH/" + path.relative_to(source).as_posix()
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    checksum = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_name(output.name + ".sha256").write_text(f"{checksum}  {output.name}\n", encoding="ascii")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "QudZH.zip")
    args = parser.parse_args()
    from check_release import validate_mod
    version, count = validate_mod(MOD)
    archive = package(MOD, args.output)
    print(f"QudZH {version}: {count} validated files -> {archive}")
    print(f"SHA-256: {archive.with_name(archive.name + '.sha256')}")


if __name__ == "__main__":
    main()
