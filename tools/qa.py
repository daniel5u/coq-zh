"""QA over TM: untranslated entries and glossary-term violations. usage: qa.py [--write]"""
import os, sys, re, json, collections
sys.path.insert(0, os.path.dirname(__file__))
from common import ROOT
from tm import load_tm
from validate import strip_tokens, LATIN_WORD, CJK
tm = load_tm()
allow = {"untranslated": set(), "glossary": set()}
_ap = os.path.join(ROOT, "docs/qa_allow.tsv")
if os.path.exists(_ap):
    for l in open(_ap, encoding="utf-8").read().splitlines()[1:]:
        p = l.split("\t")
        if len(p) >= 2 and p[1] in allow: allow[p[1]].add(p[0])
gl = []
for l in open(os.path.join(ROOT, "docs/glossary.tsv"), encoding="utf-8").read().splitlines()[1:]:
    p = l.split("\t")
    if len(p) >= 2 and p[0][:1].isupper() and len(p[0]) >= 3: gl.append((p[0], p[1]))
untrans = []; viol = collections.Counter(); vex = {}
for src, r in tm.items():
    zh = r["zh"]
    rest = strip_tokens(src)
    if r.get("batch") != "translit" and LATIN_WORD.search(rest) and not CJK.search(zh) and src not in allow["untranslated"]:
        untrans.append(src)
    for en, z in gl:
        if en in allow["glossary"]: continue
        if re.search(r"(?<![A-Za-z])" + re.escape(en) + r"(?![A-Za-z])", src) and z not in zh and en not in zh:
            viol[en] += 1; vex.setdefault(en, (src[:80], zh[:80], z))
print("untranslated-looking:", len(untrans))
for s in untrans[:40]: print("  ", repr(s[:80]))
print("glossary violations:", sum(viol.values()))
for en, c in viol.most_common(40): print(f"  {c:4d} {en} -> {vex[en][2]} | e.g. {vex[en][0]!r} => {vex[en][1]!r}")
if "--write" in sys.argv:
    json.dump({"untranslated": untrans}, open(os.path.join(ROOT, "work/qa.json"), "w"), ensure_ascii=False, indent=0)
