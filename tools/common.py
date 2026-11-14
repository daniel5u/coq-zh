"""Shared helpers for the CoQ zh pipeline."""
import os, re, json
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/Caves of Qud/CoQ.app/Contents/Resources/Data/StreamingAssets/Base")
TEMPLATE = os.path.join(GAME, "ExampleLanguage")
DATA = os.path.join(ROOT, "data")
MARK = "▶"

# attributes that are grammar flags / keys, copied verbatim (not translated)
COPY_ATTRS = {("xtagGrammar", "Proper"), ("xtagGrammar", "massNoun"), ("xtagGrammar", "iArticle")}

ID_ATTRS = ("ID", "Name", "Key", "Code", "Level", "x", "y")

def el_sig(el):
    parts = [el.tag]
    for a in ID_ATTRS:
        if a in el.attrib and MARK not in el.attrib[a]:
            parts.append(f"{a}={el.attrib[a]}")
    return "[" + ",".join(parts) + "]"

def iter_units(fn):
    """Yield (unit_dict, setter) in document order for one template file."""
    tree = ET.parse(os.path.join(TEMPLATE, fn))
    stem = fn.replace(".example.xml", "")
    n = 0
    def walk(el, path, parents):
        nonlocal n
        sig = path + el_sig(el)
        ctx = el.attrib.get("Context")
        anc = {p.tag: p.attrib for p in parents}
        def mk(attr, raw, setter):
            """Split raw value into literal/translatable segments. Returns list of units + a rebuild fn."""
            nonlocal n
            n += 1
            base = f"{stem}#{n:05d}"
            pieces = raw.split(MARK)
            lit0 = pieces[0]
            segs = []  # (translatable, trailing_literal)
            for i, p in enumerate(pieces[1:]):
                last = (i == len(pieces) - 2)
                if last:
                    m = re.match(r"^(.*?)(\s*)$", p, re.S)
                else:
                    m = re.match(r"^(.*?)(\s*~\s*|,[^,|]*\||\s+)$", p, re.S)
                    if not m: m = re.match(r"^(.*?)()$", p, re.S)
                segs.append((m.group(1), m.group(2)))
            units = []
            for i, (src, _) in enumerate(segs):
                uid = base if len(segs) == 1 else f"{base}.{i+1}"
                u = {"id": uid, "file": stem, "tag": el.tag, "attr": attr, "path": sig, "src": src}
                if ctx: u["ctx"] = ctx
                if lit0.strip() and i == 0: u["prefix_literal"] = lit0.strip()
                if el.tag == "string" and "ID" in el.attrib and attr == "#text" and el.attrib["ID"] != src:
                    u["key"] = el.attrib["ID"]
                if (el.tag, attr) in COPY_ATTRS or src in ("true", "false") or (el.tag == "key" and stem == "InventoryActions"): u["copy"] = True
                units.append(u)
            def rebuild(trans):
                out = lit0
                for (src, tail), u in zip(segs, units):
                    out += trans.get(u["id"], src) + tail
                return out
            return units, rebuild, setter
        for k, v in list(el.attrib.items()):
            if MARK in v:
                yield mk(k, v, lambda val, el=el, k=k: el.set(k, val))
        if el.text and MARK in el.text and len(el) > 0:
            # mixed content (<description>/<leveltext>/<template> with <p>, <switch>, <stat/> ...):
            # every <p> (and text-bearing <case>/<default>) becomes one unit whose src is its inner XML.
            n += 1
            base = f"{stem}#{n:05d}"
            el.text = el.text.replace(MARK, "")
            k = 0
            def inner(e):
                return (e.text or "") + "".join(ET.tostring(g, encoding="unicode") for g in e)
            def set_inner(e, val):
                UNITS = {"day": "日", "degree": "度", "hit point": "点生命值", "penetrating hit": "次穿透命中", "rank": "级", "round": "回合", "serving": "份", "square": "格", "turn": "回合", "轮": "回合", "每轮": "每回合"}
                val = val.replace("Unit=\"轮\"", "Unit=\"回合\"").replace("Unit=\"每轮\"", "Unit=\"每回合\"")
                val = re.sub(r'Unit="\u25b6?([^"]*)"', lambda m: 'Unit="%s"' % UNITS.get(m.group(1), m.group(1)), val.replace(MARK, "") if False else val)
                new = ET.fromstring("<x>" + val.replace(MARK, "") + "</x>")
                tail = e.tail
                e.text = new.text
                e[:] = list(new)
                e.tail = tail
            targets = [d for d in el.iter() if d is not el and (d.tag == "p" or (d.tag in ("case", "default") and (d.text or "").strip() and not d.findall("p")))]
            if any((c.tail or "").strip() for c in el):
                targets = [el]
            for d in targets:
                src = inner(d).strip() if d is not el else inner(d).replace(MARK, "").strip()
                if not src or not re.search(r"[A-Za-z]", re.sub(r"<[^>]+>", "", src)): continue
                k += 1
                uid = f"{base}.p{k}"
                u = {"id": uid, "file": stem, "tag": d.tag, "attr": "#inner", "path": sig, "src": src}
                yield [u], (lambda trans, u=u, d=d: trans.get(u["id"], u["src"])), (lambda val, d=d: set_inner(d, val))
            for c in el:
                yield from walk(c, sig, parents + [el])
            return
        if el.text and MARK in el.text:
            yield mk("#text", el.text, lambda val, el=el: setattr(el, "text", val))
        for c in el:
            yield from walk(c, sig, parents + [el])
    root = tree.getroot()
    return tree, list(walk(root, "", []))

def template_files():
    return sorted(f for f in os.listdir(TEMPLATE) if f.endswith(".example.xml"))

def read_jsonl(p):
    out = []
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line: out.append(json.loads(line))
    return out

def write_jsonl(p, rows):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
