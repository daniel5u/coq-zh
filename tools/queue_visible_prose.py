"""Reserve complete, literal messages for review; never install automatically."""
import json
import re
import sys
from pathlib import Path

from catalogue_translate import WORK, read, write


def queue(names, size=12):
    originals = sorted((WORK / 'batches').glob('CT[0-9][0-9][0-9][0-9].jsonl'))
    reserved = {r['id'] for p in (WORK / 'batches').glob('*.jsonl')
                if p not in originals for r in read(p)}
    accepted = {r['src'] for r in read(Path('data/catalogue_zh.jsonl'))}
    concatenations = {(r['file'], r['line']) for r in read(Path('work/text_catalogue/code_strings.jsonl'))
                      if r['kind'] == 'concatenation-candidate'}
    selected = []
    for path in originals:
        for row in read(path):
            if row['priority'] != 3 or row['id'] in reserved or row['src'] in accepted:
                continue
            src = row['src']; ctx = row['context'][0]
            if not re.search(r'(?:AddPlayerMessage|EmitMessage|JournalAPI.AddAccomplishment|(?:^|\.)Fail|displayLines.Add)$', ctx.get('call', '')):
                continue
            if re.search(r'Wish|Debug|Test', ctx.get('file', '') + ' ' + ctx.get('member', '')):
                continue
            if ctx.get('kind') != 'literal' or (ctx.get('file'), ctx.get('line')) in concatenations:
                continue
            if src != src.strip() or len(src) > 700 or not re.match(r'[A-Z={]', src):
                continue
            if not re.search(r'[.!?](?:}})?$', src) or '<spice.' in src:
                continue
            selected.append(row)
            if len(selected) == size * len(names):
                break
        if len(selected) == size * len(names):
            break
    for index, name in enumerate(names):
        rows = selected[index * size:(index + 1) * size]
        if not rows:
            break
        target = WORK / 'batches' / (name + '.jsonl')
        if target.exists():
            raise SystemExit('Refusing to overwrite ' + name)
        write(target, rows)
        print(name, len(rows))
        for row in rows:
            print(row['src'])


if __name__ == '__main__':
    queue(sys.argv[1:])
