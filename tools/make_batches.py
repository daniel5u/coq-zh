"""Create translation batches for untranslated, unassigned source strings.
usage: make_batches.py GROUP PREFIX MAXCHARS [MAXUNITS] [LIMIT_BATCHES]"""
import os, sys, json, re, collections
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from tm import load_tm, all_units
NAMEATTR={'DisplayName','Name','Title','ProperName','NameContext','NameForStatus','TinkerDisplayName','displayName','displayNameSingular','shortName','displayTitle','displayTitleSingular','shortTitle','narrationName','adjective','smearedAdjective','smearedName','stainedName','circulatoryLossNoun','circulatoryLossTerm','waterRitualName','noun','Category','TinkerCategory','name','title','ChargenTitle','SingularTitle','Unit','BiomeAdjective','BiomeEpithet','display'}
UIFILES=('Strings','Options','InventoryActions','Manual','EmbarkModules','Statistics','Templates','Widgets','Strings.appendix','TutorialStaging','Genotypes','Subtypes')
def group_of(r):
    if r['file']=='HistorySpice': return 'spice'
    if r['file']=='Naming': return 'naming'
    if r['attr'] in NAMEATTR and len(r['src'])<60: return 'terms'
    if r['file']=='Strings.Conversations': return 'conv'
    if r['file'] in ('Books','Quests'): return 'lore'
    if r['file'] in UIFILES: return 'ui'
    return 'desc'
WORK = os.path.join(ROOT, "work")
ASSIGNED = os.path.join(WORK, "assigned.json")
def load_glossary():
    rows = []
    with open(os.path.join(ROOT, "docs", "glossary.tsv"), encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 2 and p[0]: rows.append(p)
    return rows
def gloss_subset(gl, texts):
    blob = "\n".join(texts).lower()
    out = []
    for p in gl:
        if re.search(r"(?<![a-z])" + re.escape(p[0].lower()) + r"(?![a-z])", blob): out.append(p)
    return out
def main():
    group, prefix, maxchars = sys.argv[1], sys.argv[2], int(sys.argv[3])
    maxunits = int(sys.argv[4]) if len(sys.argv) > 4 else 10**9
    limit = int(sys.argv[5]) if len(sys.argv) > 5 else 10**9
    tm = load_tm()
    assigned = json.load(open(ASSIGNED)) if os.path.exists(ASSIGNED) else {}
    seen = set(); pending = []
    for r in all_units():
        if r.get('copy') or r['src'] in tm or r['src'] in assigned or r['src'] in seen: continue
        if not r['src'].strip(): continue
        if group_of(r) != group: continue
        seen.add(r['src'])
        row = {k: r[k] for k in ('id','src','file','tag','attr') }
        for k in ('ctx','key','prefix_literal'):
            if k in r: row[k] = r[k]
        row['where'] = r['path'][-160:]
        pending.append(row)
    # keep conversation/book units together: sort is document order already
    batches = []; cur = []; cc = 0
    def ckey(r):
        c = r.get('ctx') or r['where']
        m = re.match(r"Conversation ([^.]+)", c or "")
        return m.group(1) if m else None
    for r in pending:
        L = len(r['src']) + 40
        if cur and (cc + L > maxchars or len(cur) >= maxunits):
            # try not to split a conversation: allow 30% overflow if same conversation
            if not (group == 'conv' and ckey(r) == ckey(cur[-1]) and cc + L < maxchars * 1.3):
                batches.append(cur); cur = []; cc = 0
        cur.append(r); cc += L
    if cur: batches.append(cur)
    batches = batches[:limit]
    gl = load_glossary()
    os.makedirs(os.path.join(WORK, "batches"), exist_ok=True)
    existing = {f.split('.')[0] for f in os.listdir(os.path.join(WORK, "batches"))}
    n = 0; names = []
    for b in batches:
        n += 1
        while f"{prefix}{n:03d}" in existing: n += 1
        name = f"{prefix}{n:03d}"; names.append(name)
        write_jsonl(os.path.join(WORK, "batches", name + ".jsonl"), b)
        with open(os.path.join(WORK, "batches", name + ".glossary.tsv"), "w", encoding="utf-8") as f:
            f.write("en\tzh\tnote\n")
            for p in gloss_subset(gl, [r['src'] for r in b]): f.write("\t".join(p) + "\n")
        for r in b: assigned[r['src']] = name
    json.dump(assigned, open(ASSIGNED, "w"), ensure_ascii=False)
    print(f"{group}: {len(pending)} pending units -> {len(batches)} batches: {names[0] if names else ''}..{names[-1] if names else ''}")
if __name__ == "__main__": main()
