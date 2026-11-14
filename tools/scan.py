import UnityPy, os, re, struct
D=os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/Caves of Qud/CoQ.app/Contents/Resources/Data")
hits={}
for f in ["level0","sharedassets0.assets","resources.assets"]:
    env=UnityPy.load(os.path.join(D,f))
    for obj in env.objects:
        if obj.type.name!="MonoBehaviour": continue
        raw=obj.get_raw_data()
        if b"System Settings" in raw or b"Minimap" in raw:
            # extract length-prefixed strings
            strs=[]
            i=0
            while i < len(raw)-4:
                n=struct.unpack_from("<i",raw,i)[0]
                if 2<=n<=200 and i+4+n<=len(raw):
                    s=raw[i+4:i+4+n]
                    try:
                        t=s.decode("utf-8")
                        if re.fullmatch(r"[ -~]+",t) and re.search(r"[A-Za-z]{2}",t): strs.append(t); i+=4+n+((4-n%4)%4); continue
                    except: pass
                i+=4
            hits[(f,obj.path_id)]=strs
for k,v in hits.items(): print(k, v[:40])
