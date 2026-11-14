import sys, UnityPy, glob, os, json
D=os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/Caves of Qud/CoQ.app/Contents/Resources/Data")
out=set()
for f in ["level0","sharedassets0.assets","resources.assets","globalgamemanagers.assets"]:
    env=UnityPy.load(os.path.join(D,f))
    for obj in env.objects:
        if obj.type.name!="MonoBehaviour": continue
        try: tree=obj.read_typetree()
        except Exception: continue
        if "parameterizedTextFields" in tree:
            for p in tree.get("parameterizedTextFields") or []:
                v=p.get("value")
                if v: out.add(v)
print(json.dumps(sorted(out),ensure_ascii=False,indent=0))
