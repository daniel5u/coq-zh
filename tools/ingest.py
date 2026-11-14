"""Ingest agent outputs into TM. usage: ingest.py NAME [NAME...]  (reads work/batches/NAME.jsonl + work/out/NAME.jsonl)
Valid rows go to TM; invalid ones are reported and released for re-batching."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from validate import check
from tm import load_tm, save_tm
WORK = os.path.join(ROOT, "work")
tm = load_tm()
assigned = json.load(open(os.path.join(WORK, "assigned.json")))
tot_ok = tot_bad = 0
model = os.environ.get("MODEL", "")
for name in sys.argv[1:]:
    inp = read_jsonl(os.path.join(WORK, "batches", name + ".jsonl"))
    outp = os.path.join(WORK, "out", name + ".jsonl")
    try: out = {r["id"]: r.get("zh") for r in read_jsonl(outp) if "id" in r}
    except Exception as e:
        print(name, "unreadable output", e); out = {}
    ok = bad = 0
    for u in inp:
        zh = out.get(u["id"])
        E, W = check(u, zh)
        if E:
            bad += 1; assigned.pop(u["src"], None)
        else:
            ok += 1
            cur = tm.get(u["src"])
            if cur and cur.get("batch") not in (name, None) and not os.environ.get("FORCE"): continue
            tm[u["src"]] = {"src": u["src"], "zh": zh, "batch": name, "model": model}
    print(f"{name}: ok {ok}, rejected {bad}")
    tot_ok += ok; tot_bad += bad
save_tm(tm)
json.dump(assigned, open(os.path.join(WORK, "assigned.json"), "w"), ensure_ascii=False)
print(f"total ok {tot_ok} rejected {tot_bad}; TM size {len(tm)}")
