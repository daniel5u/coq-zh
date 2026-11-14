"""Apply a TM patch file (JSONL {src, zh}) after validation. usage: apply_patch.py PATCH.jsonl"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from common import read_jsonl
from tm import load_tm, save_tm, all_units
from validate import check
tm = load_tm(); units = {}
for u in all_units(): units.setdefault(u["src"], u)
ok = bad = 0
for r in read_jsonl(sys.argv[1]):
    s, z = r["src"], r["zh"]
    if s not in tm: print("not in TM:", s[:60]); bad += 1; continue
    E, _ = check(units.get(s, {"src": s}), z)
    if E: print("REJECT", s[:60], E[0][:100]); bad += 1; continue
    tm[s] = {**tm[s], "zh": z, "batch": tm[s]["batch"] + "+consistency"}; ok += 1
save_tm(tm); print(f"applied {ok}, rejected {bad}")
