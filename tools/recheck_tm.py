"""Re-validate every TM entry; with --purge remove failures from TM and release them for rebatching."""
import os, sys, json, collections
sys.path.insert(0, os.path.dirname(__file__))
from common import ROOT
from tm import load_tm, save_tm, all_units
from validate import check
tm = load_tm(); units = {}
for u in all_units(): units.setdefault(u["src"], u)
bad = collections.defaultdict(list)
for s, r in tm.items():
    u = units.get(s)
    if not u: continue
    E, _ = check(u, r["zh"])
    if E: bad[r["batch"]].append((s, r["zh"], E[0]))
for b, l in sorted(bad.items()):
    print(b, len(l))
    for s, z, e in l[:3]: print("   ", repr(s[:60]), "=>", repr(z[:60]), "|", e[:80])
if "--purge" in sys.argv:
    ap = os.path.join(ROOT, "work/assigned.json"); assigned = json.load(open(ap))
    for b, l in bad.items():
        for s, z, e in l: tm.pop(s, None); assigned.pop(s, None)
    save_tm(tm); json.dump(assigned, open(ap, "w"), ensure_ascii=False)
    print("purged", sum(len(l) for l in bad.values()))
