import UnityPy, os, re, struct, json, sys
D=os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/Caves of Qud/CoQ.app/Contents/Resources/Data")
import os
P=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def strings(raw):
    out=[];i=0
    while i < len(raw)-4:
        n=struct.unpack_from("<i",raw,i)[0]
        if 2<=n<=400 and i+4+n<=len(raw):
            try:
                t=raw[i+4:i+4+n].decode("utf-8")
                if all(c.isprintable() or c in "\n\t" for c in t): out.append(t); i+=4+n+((4-n%4)%4); continue
            except: pass
        i+=4
    return out
cand=set()
for f in ["level0","sharedassets0.assets"]:
    env=UnityPy.load(os.path.join(D,f))
    for obj in env.objects:
        if obj.type.name!="MonoBehaviour": continue
        for t in strings(obj.get_raw_data()):
            if re.search(r"[A-Za-z]{3}",t) and re.search(r"[a-z]",t) and (" " in t or re.fullmatch(r"[A-Z][a-z]+",t)) and not re.search(r"[A-Za-z]+\.[A-Za-z]+,|Assembly|UnityEngine|^m_|\.png|\.prefab|_",t):
                cand.add(t.strip())
tm={json.loads(l)["src"] for l in open(P+"/data/tm.jsonl")}
rt={l.split("\t")[0] for l in open(P+"/mod/QudZH/runtime_strings.tsv") if "\t" in l}
miss=sorted(c for c in cand if c not in tm and c not in rt)
json.dump(miss,open("scene_missing.json","w"),ensure_ascii=False,indent=0)
print(len(cand),len(miss)); print(miss[:200])
