"""Assemble mod XML files from template + data/zh/*.jsonl translations."""
import os, sys, json, shutil
sys.path.insert(0, os.path.dirname(__file__))
from common import *
OUT = os.path.join(ROOT, "mod", "QudZH")
from tm import load_tm
from zhpost import zh_post
class Trans:
    """Lookup by unit id -> translation via TM keyed on source text."""
    def __init__(self):
        self.tm = load_tm(); self.src = {}
        op = os.path.join(DATA, "overrides.json")
        self.ov = json.load(open(op, encoding="utf-8")) if os.path.exists(op) else {}
        nmp = os.path.join(DATA, "naming_map.json")
        if os.path.exists(nmp): self.ov.update(json.load(open(nmp, encoding="utf-8")))
        for fn in os.listdir(os.path.join(DATA, "source")):
            for r in read_jsonl(os.path.join(DATA, "source", fn)): self.src[r["id"]] = r
    def __contains__(self, i):
        r = self.src.get(i)
        if r is None: return False
        return i in self.ov or not r["src"].strip() or r["src"] in self.tm or r["attr"] in ("IndefiniteArticle", "DefiniteArticle") or (r["tag"] == "namestyles")
    def get(self, i, default=None):
        r = self.src.get(i)
        if r is None: return default
        if i in self.ov: return zh_post(self.ov[i])
        if r.get("copy"): return r["src"]
        if r["attr"] in ("IndefiniteArticle", "DefiniteArticle"): return ""
        if r["tag"] == "namestyles" and r["attr"] == "NameSeparator": return "·"
        t = self.tm.get(r["src"]); return zh_post(t["zh"]) if t else default
def load_trans(): return Trans()
VERSION = "0.1.0"
def build_runtime():
    """Collect work/runtime/*.tsv (EN<TAB>ZH templates for C#-built text) into runtime_strings.tsv."""
    import glob as _g, re as _re
    rows = {}
    bad = 0
    for f in sorted(_g.glob(os.path.join(ROOT, "work", "runtime", "*.tsv"))):
        for line in open(f, encoding="utf-8"):
            line = line.rstrip("\n")
            if "\t" not in line or line.startswith("#!"): continue
            en, zh = line.split("\t", 1)
            en, zh = en.strip(), zh.strip()
            if not en or not zh or not _re.search(r"[A-Za-z]", en): continue
            if en.count("#") != len(_re.findall(r"#(?!\d)", zh)) + len(_re.findall(r"#\d", zh)) or \
               sorted(_re.findall(r"\{\d+\}", en)) != sorted(set(_re.findall(r"\{\d+\}", zh))) and sorted(set(_re.findall(r"\{\d+\}", en))) != sorted(set(_re.findall(r"\{\d+\}", zh))):
                bad += 1; continue
            rows[en] = zh
    with open(os.path.join(OUT, "runtime_strings.tsv"), "w", encoding="utf-8") as f:
        for en, zh in rows.items(): f.write(en + "\t" + zh + "\n")
    print(f"runtime_strings.tsv: {len(rows)} templates ({bad} rejected)")
def write_meta():
    import shutil, glob as _g
    for f in _g.glob(os.path.join(DATA, "static", "*")): shutil.copy(f, OUT)
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"ID": "QudZH", "Title": "卡德洞窟 简体中文 (QudZH)", "Version": VERSION,
                   "Author": "QudZH contributors",
                   "Description": "《卡德洞窟》简体中文语言包：基于官方 lang-experimental 本地化框架，覆盖全部官方可翻译文本，统一术语表，古雅文风；附带中文排版（断行、数词、去冠词）运行时支持。需切换到 Steam 测试分支 lang-experimental。",
                   "Tags": "Localization"}, f, ensure_ascii=False, indent=2)
    with open(os.path.join(OUT, "Languages.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n<languages Encoding="utf-8">\n  <lang Code="zh" DisplayName="简体中文" FontFamily="Source Han Mono SC" />\n</languages>\n')
def build_anatomy_labels():
    """Reuse reviewed anatomy translations at the display boundary for old saves."""
    rows = {}
    for r in read_jsonl(os.path.join(DATA, "catalogue_zh.jsonl")):
        if r.get("reviewed") and r.get("install_xml") and any(
            c.get("file") == "Bodies.xml" for c in r.get("context", [])
        ):
            rows[r["src"]] = r["zh"]
    with open(os.path.join(OUT, "anatomy_labels.tsv"), "w", encoding="utf-8") as f:
        for en, zh in sorted(rows.items()):
            f.write(en + "\t" + zh + "\n")
def main():
    trans = load_trans()
    os.makedirs(OUT, exist_ok=True)
    tot = done = 0; missing = []
    for fn in template_files():
        tree, units = iter_units(fn)
        for us, rebuild, setter in units:
            for u in us:
                tot += 1
                if u.get("copy") or u["id"] in trans: done += 1
                else: missing.append(u)
            setter(rebuild(trans))
        root = tree.getroot()
        root.set("Lang", "zh")
        for st in root.iter("string"):
            if "Value" not in st.attrib and not (st.text or "").strip():
                st.text = None; st.set("Value", "")
        for ns in root.iter("namestyles"):
            if "NameSeparator" in ns.attrib: ns.set("NameSeparator", "·")
        pass  # no ET.indent: it injects whitespace into mixed content
        tree.write(os.path.join(OUT, fn.replace(".example.xml", ".xml")), encoding="utf-8", xml_declaration=True)
    write_meta()
    build_runtime()
    if os.path.exists(os.path.join(DATA, "catalogue_zh.jsonl")):
        from catalogue_overlays import build as build_catalogue_overlays
        build_catalogue_overlays()
        build_anatomy_labels()
    with open(os.path.join(ROOT, "work", "missing.jsonl"), "w", encoding="utf-8") as f:
        for u in missing: f.write(json.dumps(u, ensure_ascii=False) + "\n")
    print(f"built {OUT}: {done}/{tot} units translated ({100*done/tot:.2f}%)")
if __name__ == "__main__":
    main()
    import subprocess; subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "spice.py"), "build"])
