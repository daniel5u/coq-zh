"""Reserve whole literal return values from effect description methods."""
import re
import sys
from pathlib import Path

from catalogue_translate import ROOT, WORK, read, write


def queue(name, dynamic=False, fragments=False):
    originals = sorted((WORK / 'batches').glob('CT[0-9][0-9][0-9][0-9].jsonl'))
    reserved = {r['id'] for p in (WORK / 'batches').glob('*.jsonl')
                if p not in originals for r in read(p)}
    installed = {line.split('\t', 1)[0].replace('\\n', '\n').replace('\\t', '\t').strip()
                 for line in (ROOT / 'mod/QudZH/runtime_strings.tsv').read_text().splitlines()
                 if '\t' in line}
    selected = []
    for path in originals:
        for row in read(path):
            ctx = row['context'][0]
            kind = 'concatenation-candidate' if dynamic else 'literal'
            if row['id'] in reserved or row['priority'] != 3 or ctx.get('kind') != kind:
                continue
            if ctx.get('member') not in {'GetDetails', 'GetDescription', 'GetInstanceDescription', 'GetLevelText'}:
                continue
            if fragments:
                src = row['src']
                if src.strip() in installed:
                    continue
                if re.search(r'_T\(|AssertLocalizationMatch|InlineLocalizationMatch', ctx.get('call', '')):
                    continue
                if not re.match(r'[A-Z+\-0-9]', src) or len(src) < 14:
                    continue
            source = ROOT / 'research/decompiled' / ctx['file']
            if not source.exists():
                continue
            if not dynamic and not fragments:
                line = source.read_text().splitlines()[ctx['line'] - 1].strip()
                if not re.fullmatch(r'return\s+"(?:[^"\\]|\\.)*";', line):
                    continue
            if not (8 if dynamic else 20) <= len(row['src']) <= 1800:
                continue
            selected.append(row)
            if len(selected) == 12:
                break
        if len(selected) == 12:
            break
    target = WORK / 'batches' / (name + '.jsonl')
    if target.exists():
        raise SystemExit('Refusing to overwrite ' + name)
    if selected:
        write(target, selected)
    print(name, len(selected))
    for row in selected:
        print(row['src'])


if __name__ == '__main__':
    queue(sys.argv[1], '--dynamic' in sys.argv[2:], '--fragments' in sys.argv[2:])
