"""Python mirror of ZhRuntime.TranslateLine for offline testing. usage: runtime_sim.py "line" ..."""
import re, sys, glob, os
NUM = r"[+-]?\d+(?:\.\d+)?(?:d\d+(?:[+-]\d+)?)?"
NUMRX = re.compile(r"(?<![A-Za-z#])" + NUM)
def load():
    exact, norm, tpl = {}, {}, []
    for f in sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "work", "runtime", "*.tsv"))):
        for l in open(f, encoding="utf-8"):
            l = l.rstrip("\n")
            if "\t" not in l: continue
            en, zh = l.split("\t", 1)
            if re.search(r"\{\d+\}", en):
                rx = "^"; i = 0
                while i < len(en):
                    c = en[i]
                    if c == "#": rx += "(" + NUM + ")"; i += 1; continue
                    m = re.match(r"\{(\d+)\}", en[i:])
                    if m: rx += f"(?P<t{m.group(1)}>.+?)"; i += len(m.group(0)); continue
                    rx += re.escape(c); i += 1
                tpl.append((re.compile(rx + "$"), zh))
            elif "#" in en: norm[en] = zh
            else: exact[en] = zh
    return exact, norm, tpl
E, N, T = load()
def fill(z, nums):
    it = iter(nums)
    return re.sub(r"#(\d)?", lambda m: nums[int(m.group(1)) - 1] if m.group(1) else next(it, "#"), z)
def tr(line):
    t = line.strip()
    if t in E: return E[t]
    nums = []
    key = NUMRX.sub(lambda m: (nums.append(m.group(0)), "#")[1], t)
    if nums and key in N: return fill(N[key], nums)
    for rx, z in T:
        m = rx.match(t)
        if m:
            caps = [g for k, g in zip(range(1, 99), m.groups()) if k <= len(m.groups())]
            numcaps = [m.group(i) for i in range(1, len(m.groups()) + 1) if i not in [rx.groupindex[n] for n in rx.groupindex]]
            z2 = fill(z, numcaps)
            return re.sub(r"\{(\d+)\}", lambda q: m.group("t" + q.group(1)) if ("t" + q.group(1)) in rx.groupindex else q.group(0), z2)
    return None
if __name__ == "__main__":
    print(f"loaded exact={len(E)} norm={len(N)} templates={len(T)}")
    for a in sys.argv[1:]: print(repr(a), "->", tr(a))
