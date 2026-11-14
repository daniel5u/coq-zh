"""Rebuild docs/glossary.tsv = core (docs/glossary_core.tsv) + resolved + vetted proposals.
A proposal is replaced by the TM translation if the TM has that exact English source."""
import os, sys, re, glob, collections
sys.path.insert(0, os.path.dirname(__file__))
from common import ROOT
from tm import load_tm
JUNK = re.compile(r"[阿埃伊奥乌]{2}|[斯姆特格普瓦尔克][阿埃伊奥乌][斯姆特格普瓦尔克伊奥乌阿埃]|[一-鿿] [一-鿿]|[A-Za-z]{3,}|(?:姆埃|尔埃|特埃|斯乌|格乌|德奥|普奥|克尔|伊克|奥特|埃尔)")
tm = load_tm()
def rows(p):
    out = []
    for l in open(p, encoding="utf-8").read().splitlines():
        q = l.split("\t")
        if len(q) >= 2 and q[0].strip() and q[1].strip() and q[0] != "en": out.append([q[0].strip(), q[1].strip(), q[2] if len(q) > 2 else ""])
    return out
core = rows(os.path.join(ROOT, "docs/glossary_core.tsv"))
resolved = rows(os.path.join(ROOT, "docs/glossary_resolved.tsv")) if os.path.exists(os.path.join(ROOT, "docs/glossary_resolved.tsv")) else []
have = {}
for r in core + resolved: have[r[0]] = r
props = collections.defaultdict(collections.Counter)
for f in glob.glob(os.path.join(ROOT, "work/glossary_proposals/*.tsv")):
    for en, zh, _ in rows(f):
        if "{{" in en or "=" in en or len(en) > 40 or len(en.split()) > 4: continue
        props[en][zh] += 1
added = junk = 0
for en, c in sorted(props.items()):
    if en in have: continue
    if en in tm and not JUNK.search(tm[en]["zh"]) and "{{" not in tm[en]["zh"]:
        zh = tm[en]["zh"]
    else:
        zh = c.most_common(1)[0][0]
    if JUNK.search(zh): junk += 1; continue
    have[en] = [en, zh, "proposed"]; added += 1
with open(os.path.join(ROOT, "docs/glossary.tsv"), "w", encoding="utf-8") as f:
    f.write("en\tzh\tnote\n")
    for r in have.values(): f.write("\t".join(r) + "\n")
print(f"core {len(core)} resolved {len(resolved)} proposals added {added} junk-dropped {junk} total {len(have)}")
