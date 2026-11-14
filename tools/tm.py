"""Translation memory: data/tm.jsonl, keyed by source string."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, read_jsonl
TM_PATH = os.path.join(DATA, "tm.jsonl")
def load_tm():
    tm = {}
    for r in read_jsonl(TM_PATH): tm[r["src"]] = r
    return tm
def save_tm(tm):
    tmp = TM_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for k in sorted(tm): f.write(json.dumps(tm[k], ensure_ascii=False) + "\n")
    os.replace(tmp, TM_PATH)
def all_units():
    from common import read_jsonl as rj
    d = os.path.join(DATA, "source"); out = []
    for fn in sorted(os.listdir(d)): out += rj(os.path.join(d, fn))
    return out
