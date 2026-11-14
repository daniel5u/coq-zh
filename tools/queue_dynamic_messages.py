"""Reserve whole message expressions and their capture context for review."""
import re
import sys

from catalogue_translate import WORK, read, write


def queue(names, size=12):
    originals = sorted((WORK / 'batches').glob('CT[0-9][0-9][0-9][0-9].jsonl'))
    reserved = {r['id'] for p in (WORK / 'batches').glob('*.jsonl')
                if p not in originals for r in read(p)}
    selected = []
    for path in originals:
        for row in read(path):
            ctx = row['context'][0]; src = row['src']
            if row['id'] in reserved or row['priority'] != 3 or ctx.get('kind') != 'concatenation-candidate':
                continue
            if not re.search(r'(?:AddPlayerMessage|EmitMessage|(?:^|\.)Fail)$', ctx.get('call', '')):
                continue
            if re.search(r'Wish|Debug|Test', ctx.get('file', '') + ' ' + ctx.get('member', '')):
                continue
            if not re.search(r'[.!?](?:}})?$', src) or src != src.strip() or len(src) > 500:
                continue
            if not re.match(r'[A-Z{]', src):
                continue
            if any(re.search(r'\.(?:Does|does|GetVerb|is|Is|Itis)\b', hole) for hole in ctx.get('holes', [])):
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
