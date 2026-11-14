"""HistorySpice (sultan histories, gossip, tombstones, recipes...) -> units, and build historyspice.zh.json.
usage: spice.py extract | build"""
import os, sys, re, json
sys.path.insert(0, os.path.dirname(__file__))
from common import GAME, DATA, ROOT, write_jsonl
from tm import load_tm
from zhpost import zh_post
SRC = os.path.join(GAME, "HistorySpice.jsonc")
def load():
    t = open(SRC, encoding="utf-8-sig").read()
    t = re.sub(r"^\s*//.*$", "", t, flags=re.M)
    return json.loads(t)
def leaves(x, p):
    if isinstance(x, dict):
        for k, v in x.items(): yield from leaves(v, p + [k])
    elif isinstance(x, list):
        for i, v in enumerate(x): yield from leaves(v, p + [i])
    elif isinstance(x, str): yield p, x
def translatable(p, s):
    if any(isinstance(k, str) and k.startswith("@") for k in p): return False
    if re.fullmatch(r"\s*(=[^=]+=\s*)+", s): return False
    if not re.search(r"[A-Za-z]", s): return False
    if p[:2] == ["spice", "digits"]: return False
    if any(isinstance(k, str) and k.startswith("_") for k in p): return False
    if re.fullmatch(r"spice\.[A-Za-z0-9_.@-]+", s.strip()): return False
    return True
def extract():
    d = load(); rows = []
    for p, s in leaves(d, []):
        if not translatable(p, s): continue
        path = "/".join(map(str, p))
        rows.append({"id": "HistorySpice#" + path, "file": "HistorySpice", "tag": "spice", "attr": str(p[-1]) if isinstance(p[-1], str) else str(p[-2]),
                     "path": path, "src": s})
    write_jsonl(os.path.join(DATA, "source", "HistorySpice.jsonl"), rows)
    print("spice units", len(rows))
def build():
    d = load(); tm = load_tm(); n = t = 0
    def tr(x, p):
        nonlocal n, t
        if isinstance(x, dict): return {k: tr(v, p + [k]) for k, v in x.items()}
        if isinstance(x, list): return [tr(v, p + [i]) for i, v in enumerate(x)]
        if isinstance(x, str) and translatable(p, x):
            t += 1
            if x in tm: n += 1; return zh_post(tm[x]["zh"])
        return x
    out = tr(d, [])
    spice = {k + "=": v for k, v in out["spice"].items()}
    path = os.path.join(ROOT, "mod", "QudZH", "historyspice.zh.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"lang": "zh", "spice": spice}, f, ensure_ascii=False, indent=1)
    print(f"historyspice.zh.json: {n}/{t} translated")
if __name__ == "__main__":
    {"extract": extract, "build": build}[sys.argv[1]]()
