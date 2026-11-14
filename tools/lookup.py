"""Find existing translations of an English term. usage: lookup.py "term" [more terms]"""
import os, sys, json, glob, re
sys.path.insert(0, os.path.dirname(__file__))
from common import ROOT, read_jsonl
from tm import load_tm
tm = load_tm()
pairs = {}
for f in glob.glob(os.path.join(ROOT, "work/out/*.jsonl")):
    name = os.path.basename(f)[:-6]
    try:
        src = {r["id"]: r["src"] for r in read_jsonl(os.path.join(ROOT, "work/batches", name + ".jsonl"))}
        for r in read_jsonl(f):
            if r.get("id") in src: pairs.setdefault(src[r["id"]], r.get("zh"))
    except Exception: pass
for k, v in tm.items(): pairs[k] = v["zh"]
gl = {}
for line in open(os.path.join(ROOT, "docs/glossary.tsv"), encoding="utf-8"):
    p = line.rstrip("\n").split("\t")
    if len(p) >= 2: gl[p[0]] = p[1]
for q in sys.argv[1:]:
    ql = q.lower(); hits = []
    for k, v in gl.items():
        if ql in k.lower(): hits.append(("GLOSSARY", k, v))
    for k, v in pairs.items():
        if len(k) < 80 and ql in k.lower(): hits.append(("tm", k, v))
    hits.sort(key=lambda h: (h[0] != "GLOSSARY", len(h[1])))
    print(f"== {q}")
    for h in hits[:15]: print(f"  [{h[0]}] {h[1]} => {h[2]}")
