import UnityPy, os, re, struct, json
D=os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/Caves of Qud/CoQ.app/Contents/Resources/Data")
def strings(raw):
    out=[];i=0
    while i < len(raw)-4:
        n=struct.unpack_from("<i",raw,i)[0]
        if 1<=n<=600 and i+4+n<=len(raw):
            try:
                t=raw[i+4:i+4+n].decode("utf-8")
                if all(c.isprintable() or c in "\n\t" for c in t): out.append(t); i+=4+n+((4-n%4)%4); continue
            except: pass
        i+=4
    return out
vals=set()
for f in ["level0","sharedassets0.assets","resources.assets"]:
    env=UnityPy.load(os.path.join(D,f))
    for obj in env.objects:
        if obj.type.name!="MonoBehaviour": continue
        raw=obj.get_raw_data()
        if b"%BodyText%" not in raw and b"%Title%" not in raw: continue
        s=strings(raw)
        for j,t in enumerate(s):
            if t.startswith("%") and t.endswith("%") and j+1<len(s): vals.add(s[j+1])
print(json.dumps(sorted(vals),ensure_ascii=False))
