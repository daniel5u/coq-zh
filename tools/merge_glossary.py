"""Merge work/glossary_proposals/*.tsv into docs/glossary.tsv. Prints conflicts."""
import os, sys, glob, re, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(ROOT, "docs/glossary.tsv")
lines = open(G, encoding="utf-8").read().splitlines()
header, rows = lines[0], [l.split("\t") for l in lines[1:] if l.strip()]
have = {r[0]: r for r in rows}
props = collections.defaultdict(set)
for f in sorted(glob.glob(os.path.join(ROOT, "work/glossary_proposals/*.tsv"))):
    for l in open(f, encoding="utf-8"):
        p = l.rstrip("\n").split("\t")
        if len(p) < 2 or not p[0].strip() or not p[1].strip(): continue
        en, zh = p[0].strip(), p[1].strip()
        if "{{" in en or "{{" in zh or "=" in en: continue
        if len(en.split()) > 4 or len(en) > 40: continue
        props[en].add(zh)
added = 0; conflicts = []
for en, zhs in sorted(props.items()):
    if en in have:
        if have[en][1] not in zhs or len(zhs) > 1:
            if any(z != have[en][1] for z in zhs): conflicts.append((en, have[en][1], sorted(zhs)))
        continue
    if len(zhs) > 1: conflicts.append((en, None, sorted(zhs))); continue
    rows.append([en, next(iter(zhs)), "proposed"]); have[en] = rows[-1]; added += 1
with open(G, "w", encoding="utf-8") as f:
    f.write(header + "\n")
    for r in rows: f.write("\t".join(r) + "\n")
print("added", added, "total", len(rows))
for c in conflicts: print("CONFLICT", c)
