import sys, os, re, collections
import xml.etree.ElementTree as ET
src = sys.argv[1]
combos = collections.Counter(); units=0; chars=0; multi=0
for fn in sorted(os.listdir(src)):
    t = ET.parse(os.path.join(src, fn))
    for el in t.iter():
        for k, v in el.attrib.items():
            if '▶' in v:
                combos[(fn, el.tag, k)] += 1; units += 1; chars += len(v)
                if v.count('▶')>1: multi+=1
        if el.text and '▶' in el.text:
            combos[(fn, el.tag, '#text')] += 1; units += 1; chars += len(el.text)
            if el.text.count('▶')>1: multi+=1
print(units, chars, 'multi', multi)
for k, c in sorted(combos.items()): print(c, *k)
