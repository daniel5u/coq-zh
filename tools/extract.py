"""Extract all translatable units from the ExampleLanguage template into data/source/*.jsonl"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import *
tot = 0
for fn in template_files():
    _, units = iter_units(fn)
    rows = [x for us, *_ in units for x in us]
    write_jsonl(os.path.join(DATA, "source", fn.replace(".example.xml", ".jsonl")), rows)
    tot += len(rows)
print("units", tot)
