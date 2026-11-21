"""Extract WWN tag write-ups (description + Enemies/Friends/Complications/Things/Places).

Usage: extract_wwn_tags.py WWN.pdf TABLES.json OUT.json
TABLES.json is extract_pdf output; its d100 'Tag' tables give the tag names and the pages
after each table hold the write-ups (in reading order, two columns a page).
"""
import sys, json, re, subprocess

pdf, tables, out = sys.argv[1:4]
KEYS = {'E': 'enemies', 'F': 'friends', 'C': 'complications', 'T': 'things', 'P': 'places'}

def col_text(p):
    t = []
    for x in (0, 306):
        t.append(subprocess.run(['pdftotext', '-q', '-f', str(p), '-l', str(p), '-x', str(x), '-y', '40',
                                 '-W', '306', '-H', '720', pdf, '-'], capture_output=True, text=True).stdout)
    return '\n'.join(t)

d = json.load(open(tables))
groups = {}
for t in d:
    if t['die'] == 'd100' and t['title'].strip() == 'Tag':
        groups.setdefault(t['pdf_page'], []).extend(r[1] for r in t['rows'])
kinds = dict(zip(sorted(groups), ['community', 'court', 'ruin', 'wilderness']))
res = {}
for start, names in sorted(groups.items()):
    text = '\n'.join(col_text(p) for p in range(start + 1, start + 15))
    lines = [l.strip() for l in text.splitlines()]
    norm = lambda s: re.sub(r'[^a-z]', '', s.lower().replace('’', "'"))
    want = {norm(n): n for n in names}
    tags, cur, key = [], None, None
    for l in lines:
        if not l: continue
        if norm(l) in want and (cur is None or cur.get('places') or key):
            cur = {'tag': want[norm(l)], 'desc': '', **{v: '' for v in KEYS.values()}}
            tags.append(cur); key = None; continue
        if cur is None: continue
        if l in KEYS: key = KEYS[l]; continue
        if key: cur[key] = (cur[key] + ' ' + l).strip()
        else: cur['desc'] = (cur['desc'] + ' ' + l).strip()
    for t in tags:
        for k in KEYS.values():
            s = re.sub(r'(\w)- (\w)', r'\1\2', t[k])
            t[k] = [x.strip() for x in re.split(r',\s+(?=[A-Z])', s) if x.strip()]
        t['desc'] = re.sub(r'(\w)- (\w)', r'\1\2', t['desc'])
    res[kinds[start]] = {'source': 'WWN', 'pdf_page': start, 'tags': tags,
                         'missing': sorted(set(names) - {t['tag'] for t in tags})}
    print(kinds[start], len(tags), 'of', len(names), 'missing', res[kinds[start]]['missing'][:8], file=sys.stderr)
json.dump(res, open(out, 'w'), ensure_ascii=False, indent=1)
