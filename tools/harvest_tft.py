"""Harvest the Wildland denizen tables of Thematic Foe Tables (your book) from its
markdown source, with each foe's stat line taken from its block.

Usage: harvest_tft.py MERGED_SD_DIR TFT.pdf OUT.json
Reads 29-38 *-wl-*.md (and 36a, 36b) (one 4d6 table each). Pages are found in the PDF by the
table's heading, so a TFT rebuild that moves pages only needs `make data`."""
import glob, json, os, re, subprocess, sys

src_dir, pdf, out_path = sys.argv[1:4]
STAT = re.compile(r'AC (\d+)[^,]*, HP (\d+), ATK (.+?), MV .*\bLV (\d+)')


def norm(s):
    return re.sub(r'[^a-z ]', '', s.lower()).strip()


PLURAL = (('ies', 'y'), ('ves', 'f'), ('ves', 'fe'), ('oxen', 'ox'), ('men', 'man'), ('es', ''), ('s', ''),
          ('ice', 'ouse'), ('eese', 'oose'))


def singles(word):
    yield word
    for a, b in PLURAL:
        if word.endswith(a):
            yield word[:-len(a)] + b


def candidates(name):
    """Full name first, then singulars of its last or first word, then without a
    'herd'/'of the …' tail, then its last words alone ('Horsehead Hawks' -> 'hawk')."""
    n = norm(name)
    w = n.split()
    yield n
    for s in singles(w[-1]):
        yield ' '.join(w[:-1] + [s])
    for s in singles(w[0]):
        yield ' '.join([s] + w[1:])
    short = re.sub(r' (herd|pack|swarm|of the .+)$', '', n)
    if short != n:
        yield from candidates(short)
    for k in range(1, len(w)):
        for s in singles(w[-1]):
            yield ' '.join(w[k:-1] + [s])


def blocks(text):
    out = {}
    for m in re.finditer(r'^#### (.+)\n(?:(?!#### ).*\n?)*', text, re.M):
        body = m.group(0)
        st = STAT.search(body)
        if not st:
            continue
        react = re.search(r'\*\*Reactions \(d6\)\.\*\* (.+)', body)
        out[norm(m.group(1))] = {'AC': st.group(1), 'HP': st.group(2), 'Attack': st.group(3),
                                 'LV': st.group(4), 'Reactions': react.group(1).strip() if react else ''}
    return out


pages = subprocess.run(['pdftotext', '-layout', pdf, '-'], capture_output=True, text=True).stdout.split('\f')
flat = [' '.join(p.split()).lower() for p in pages]

ALL = {}
for g in sorted(glob.glob(os.path.join(src_dir, '*.md'))):   # a block printed once serves every table
    for k, v in blocks(open(g, encoding='utf-8').read()).items():
        ALL.setdefault(k, v)

tables, missing = [], []
for f in sorted(glob.glob(os.path.join(src_dir, '[23][0-9]*-wl-*.md'))):
    text = open(f, encoding='utf-8').read()
    head = re.search(r'^### (.+?) — DENIZENS \((\d+d\d+)\) · party LV ([\d–-]+) · (.+)$', text, re.M)
    if not head:
        continue
    title, die, lv, terrain = head.groups()
    chapter = re.search(r'^## (.+)$', text, re.M).group(1)
    key = title.lower()
    page = next((i + 1 for i, p in enumerate(flat) if key in p), None)
    bl = {**ALL, **blocks(text)}
    rows = []
    for line in text[head.end():].splitlines():
        m = re.match(r'^\| (\d+) \| (.+?) \| (\w) \| (.+?) \|$', line)
        if not m:
            if rows and not line.strip().startswith('|') and line.strip():
                break
            continue
        roll, foe, typ, no = m.groups()
        st = next((bl[c] for c in candidates(foe) if c in bl), None)
        if st is None:
            missing.append(f'{os.path.basename(f)}: {foe}')
            st = {'AC': '', 'HP': '', 'Attack': '', 'LV': '', 'Reactions': ''}
        rows.append([roll, foe, typ, no, st['LV'], st['AC'], st['HP'], st['Attack'], st['Reactions']])
    slug = re.sub(r'^\d+[a-z]?-wl-|\.md$', '', os.path.basename(f))
    tables.append({'id': f'tft.wl.{slug}', 'title': f'{chapter} — {title}', 'terrain': terrain,
                   'party_lv': lv, 'die': die, 'page': page,
                   'cols': ['Foe', 'Type', 'No.', 'LV', 'AC', 'HP', 'Attack', 'Reactions'], 'rows': rows})

json.dump(tables, open(out_path, 'w'), ensure_ascii=False, indent=0)
print(f'{len(tables)} tables, {sum(len(t["rows"]) for t in tables)} rows', file=sys.stderr)
for m in missing:
    print('  no block:', m, file=sys.stderr)
if missing:
    sys.exit(1)
