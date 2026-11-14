"""Publish the committed mod to its Steam Workshop item with SteamCMD.

GitHub is the source of truth: the uploaded files, title and description come
from mod/QudZH (manifest.json + workshop.json). The first upload creates the
item and writes its new WorkshopId back into workshop.json; later uploads
update that item and leave its Steam visibility unchanged.

  python3 tools/workshop.py --dry-run          # stage files and print the VDF
  python3 tools/workshop.py --changenote "..."  # upload (needs a SteamCMD login)

SteamCMD logs in as $STEAM_USERNAME with its cached credentials; run
`steamcmd +login <name> +quit` once interactively to cache them.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from check_release import validate_mod
from package import MOD, mod_files

APP_ID = 333640
# The in-game uploader stores its dropdown index (0 private, 1 friends, 2 public,
# 3 unlisted); SteamCMD numbers them 0 public, 1 friends, 2 private, 3 unlisted.
GAME_TO_STEAMCMD_VISIBILITY = {"0": 2, "1": 1, "2": 0, "3": 3}
REPOSITORY = "https://github.com/daniel5u/coq-zh"


def vdf_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def read_workshop(source: Path = MOD) -> dict:
    info = json.loads((source / "workshop.json").read_text(encoding="utf-8-sig"))
    if not isinstance(info.get("WorkshopId", 0), int) or info.get("WorkshopId", 0) < 0:
        raise ValueError("workshop.json WorkshopId must be a non-negative integer")
    for key in ("Title", "Description", "ImagePath"):
        if not isinstance(info.get(key), str) or not info[key].strip():
            raise ValueError(f"workshop.json needs a non-empty {key}")
    if not (source / info["ImagePath"]).is_file():
        raise ValueError(f"Preview image is missing: {info['ImagePath']}")
    return info


def build_vdf(info: dict, content: Path, preview: Path, changenote: str) -> str:
    published = int(info.get("WorkshopId", 0))
    fields = [
        ("appid", str(APP_ID)),
        ("publishedfileid", str(published)),
        ("contentfolder", str(content)),
        ("previewfile", str(preview)),
        ("title", info["Title"]),
        ("description", info["Description"]),
        ("changenote", changenote),
    ]
    if published == 0:
        # Only a new item gets the visibility from workshop.json; afterwards the
        # visibility chosen on Steam is kept.
        fields.append(("visibility", str(GAME_TO_STEAMCMD_VISIBILITY.get(str(info.get("Visibility", "0")), 2))))
    body = "".join(f"\t{vdf_string(key)}\t{vdf_string(value)}\n" for key, value in fields)
    return '"workshopitem"\n{\n' + body + "}\n"


def stage(source: Path, target: Path) -> Path:
    """Copy exactly the validated distributable files; return the content folder."""
    content = target / "content"
    for path in mod_files(source):
        destination = content / path.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
    return content


def created_id(output: str) -> int | None:
    match = re.search(r"PublishFileID\s*:?\s*(\d+)", output, re.IGNORECASE)
    return int(match.group(1)) if match else None


def save_workshop_id(source: Path, workshop_id: int) -> None:
    path = source / "workshop.json"
    info = json.loads(path.read_text(encoding="utf-8-sig"))
    info["WorkshopId"] = workshop_id
    path.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--changenote", help="Workshop change note (default: link to the GitHub release)")
    parser.add_argument("--steamcmd", default=os.environ.get("STEAMCMD", "steamcmd"))
    parser.add_argument("--dry-run", action="store_true", help="Stage files and print the VDF without uploading")
    args = parser.parse_args()

    version, _ = validate_mod(MOD)
    info = read_workshop(MOD)
    changenote = args.changenote or f"QudZH {version}: {REPOSITORY}/releases/tag/v{version}"
    with tempfile.TemporaryDirectory(prefix="qudzh-workshop-") as temp:
        root = Path(temp)
        content = stage(MOD, root)
        preview = root / ("preview" + Path(info["ImagePath"]).suffix)
        shutil.copyfile(MOD / info["ImagePath"], preview)
        vdf = root / "workshop_item.vdf"
        vdf.write_text(build_vdf(info, content, preview, changenote), encoding="utf-8")
        if args.dry_run:
            print(vdf.read_text(encoding="utf-8"))
            print(f"{sum(1 for p in content.rglob('*') if p.is_file())} files staged")
            return
        username = os.environ.get("STEAM_USERNAME")
        if not username:
            raise SystemExit("Set STEAM_USERNAME to the Steam account that owns the Workshop item")
        result = subprocess.run([args.steamcmd, "+login", username, "+workshop_build_item", str(vdf), "+quit"],
                                text=True, capture_output=True)
        output = result.stdout + result.stderr
        print(output.replace(username, "<steam user>"))
        if result.returncode != 0 or ("ERROR" in output.upper() and "SUCCESS" not in output.upper()):
            raise SystemExit(f"SteamCMD upload failed (exit {result.returncode})")
        if int(info.get("WorkshopId", 0)) == 0:
            new_id = created_id(output)
            if not new_id:
                raise SystemExit("Upload finished but no PublishFileID was found; set WorkshopId by hand")
            save_workshop_id(MOD, new_id)
            print(f"Created Workshop item {new_id}; commit mod/QudZH/workshop.json")
        print(f"Workshop item {info.get('WorkshopId') or 'new'} updated to QudZH {version}")


if __name__ == "__main__":
    main()
