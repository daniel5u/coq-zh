"""Usage: python3 tools/check_batch.py <batch_input.jsonl> <batch_output.jsonl>
Checks an agent's output against the batch input. Prints problems; exit 1 if errors."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from validate import check
from common import read_jsonl
inp = {u["id"]: u for u in read_jsonl(sys.argv[1])}
out = {}
bad = 0
try:
    rows = read_jsonl(sys.argv[2])
except Exception as e:
    print("OUTPUT NOT VALID JSONL:", e); sys.exit(1)
for r in rows:
    if "id" not in r or "zh" not in r: print("row missing id/zh:", str(r)[:120]); bad += 1; continue
    out[r["id"]] = r["zh"]
for i, u in inp.items():
    if i not in out: print(f"{i}: MISSING"); bad += 1; continue
    E, W = check(u, out[i])
    for e in E: print(f"{i}: ERROR {e}"); bad += 1
    for w in W: print(f"{i}: warn {w}")
extra = set(out) - set(inp)
if extra: print("warn: ignoring unknown ids in output:", sorted(extra)[:10])
print(f"{len(inp)} units, {len(out)} answered, {bad} errors")
sys.exit(1 if bad else 0)
