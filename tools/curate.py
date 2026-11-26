"""Turn raw extractions (raw/*.json) into data/gen/*.yaml with stable ids.

Ids are  <src>.p<printed page>.<slug of title>  (plus -2, -3 when a page repeats a title).
Hand-named ids come from the NAMES maps below, so generators can say 'sd.enc.forest'
instead of 'sd.p154.details'.

Usage: curate.py RAW_DIR DATA_DIR
"""
import sys, os, re, json, yaml

RAW, DATA = sys.argv[1], sys.argv[2]
OUT = os.path.join(DATA, 'gen')
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from hexgen.tables import parse_label
from hexgen.dice import die_range

SOURCES = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), '..', 'sources.yaml')))


def slug(s, n=40):
    s = re.sub(r'[’\']', '', s.lower())
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:n].rstrip('-') or 'table'


def clean(s):
    s = re.sub(r'\s+', ' ', str(s)).strip()
    return re.sub(r'(\w)- (\w)', r'\1\2', s)


def check(t):
    """Return a list of problems; an empty list means the table rolls cleanly."""
    probs = []
    if not t.get('die'):
        return probs
    try:
        lo, hi = die_range(t['die'])
    except ValueError:
        return ['bad die']
    covered = set()
    for r in t['rows']:
        rg = parse_label(r[0], hi)
        if rg is None:
            probs.append(f'bad label {r[0]!r}'); continue
        covered.update(range(rg[0], rg[1] + 1))
    gaps = [n for n in range(lo, hi + 1) if n not in covered]
    if gaps:
        probs.append(f'{len(gaps)} results uncovered')
    if any(not any(c for c in r[1:]) for r in t['rows']):
        probs.append('empty row')
    return probs


def trim_spill(rows):
    """Body text sometimes lands on a table's last line or beside a short row: cut a cell
    that is far longer than its column's norm at the point where the prose begins."""
    import statistics
    for c in range(1, max(len(r) for r in rows)):
        lens = sorted(len(r[c]) for r in rows if len(r) > c and r[c])
        if len(lens) < 4: continue
        med = statistics.median(lens)
        for r in rows:
            if len(r) > c and len(r[c]) > max(80, 2.2 * med):
                m = re.search(r'(?<=[a-z\)])\.?\s+(?=(?:Now|If|When|The GM|GMs|This|These|For|Once|Most|Some|Roll|Players)\b)', r[c][int(med * 0.5):])
                if m:
                    r[c] = r[c][:int(med * 0.5) + m.start()].rstrip(' .') 
    return rows


def merge_halves(ts):
    """Join a table split in two (side by side or over a page) when the second picks up
    where the first ends (1–2 … 49–50 | 51–52 … 99–00)."""
    out = []
    for t in ts:
        if out:
            p = out[-1]
            try:
                end = parse_label(p['rows'][-1][0], 100)[1]
                start = parse_label(t['rows'][0][0], 100)[0]
            except (TypeError, IndexError):
                end, start = None, None
            if (p['die'] == t['die'] and end is not None and start == end + 1
                    and abs(t['pdf_page'] - p['pdf_page']) <= 1 and (p['title'] == t['title'] or start > 1)):
                p['rows'] += t['rows']; continue
        out.append(dict(t, rows=list(t['rows'])))
    return out


def emit(name, src, tables, extras=None):
    doc = {'source': src, 'tables': tables}
    if extras: doc['extras'] = extras
    with open(os.path.join(OUT, name + '.yaml'), 'w', encoding='utf-8') as f:
        yaml.safe_dump(doc, f, allow_unicode=True, sort_keys=False, width=200)
    bad = {k: v['review'] for k, v in tables.items() if v.get('review')}
    print(f'{name}: {len(tables)} tables, {len(bad)} flagged for review')


def from_extract(key, names=None, keep=None):
    """Generic: raw/<key>.json from extract_pdf → data/gen/<key>.yaml."""
    src = SOURCES[key]
    raw = json.load(open(os.path.join(RAW, key + '.json')))
    raw = merge_halves(raw)
    names = names or {}
    tables, seen = {}, {}
    for t in raw:
        if keep and not keep(t):
            continue
        title = clean(t['title'])
        base = f"{src['id'].lower()}.p{t['page']}.{slug(title)}"
        seen[base] = seen.get(base, 0) + 1
        tid = base if seen[base] == 1 else f'{base}-{seen[base]}'
        tid = names.get(tid, tid)
        rows = [[r[0]] + [clean(c) for c in r[1:]] for r in t['rows']]
        if key != 'ss':
            rows = trim_spill(rows)
        d = {'title': title, 'die': t['die'], 'page': t['page'], 'rows': rows}
        if t.get('cols'): d['cols'] = [clean(c) for c in t['cols']]
        probs = check(d)
        if probs: d['review'] = '; '.join(probs)
        tables[tid] = d
    emit(key, src, tables)
    return tables


# ------------------------------------------------------------------ WWN
WWN_NAMES = {}
from_extract('wwn', WWN_NAMES)

# WWN tags (community / court / ruin / wilderness): lists + write-ups
tags = json.load(open(os.path.join(RAW, 'wwn_tags.json')))
tag_tables = {}
for kind, v in tags.items():
    tag_tables[f'wwn.tag.{kind}'] = {'title': f'{kind.title()} tag', 'page': v['pdf_page'] - SOURCES['wwn']['offset'],
                                     'rows': [t['tag'] for t in v['tags']]}
emit('wwn_tags', dict(SOURCES['wwn'], id='WWN'), tag_tables,
     {'wwn_tags': {k: {t['tag']: {x: t[x] for x in ('desc', 'enemies', 'friends', 'complications', 'things', 'places')}
                       for t in v['tags']} for k, v in tags.items()}})

# ------------------------------------------------------------------ Shadowdark core encounter d100s
SD_ENC = ['arctic', 'artisan', 'castle', 'cave', 'deep-tunnels', 'desert', 'forest', 'grassland', 'high-district',
          'jungle', 'low-district', 'market', 'mountain', 'ocean', 'river-coast', 'ruins', 'slums', 'swamp',
          'tavern', 'temple', 'tomb', 'university']
raw = json.load(open(os.path.join(RAW, 'sdcore.json')))
tables = {}
for i, name in enumerate(SD_ENC):
    a, b = raw[2 * i], raw[2 * i + 1]
    rows = [[r[0]] + [clean(c) for c in r[1:]] for r in a['rows'] + b['rows']]
    d = {'title': f'{name.replace("-", " ").title()} encounters', 'die': 'd100', 'page': a['page'], 'rows': rows}
    if check(d): d['review'] = '; '.join(check(d))
    tables[f'sd.enc.{name}'] = d
emit('sdcore', SOURCES['sdcore'], tables)

# ------------------------------------------------------------------ OSE wilderness encounters
raw = json.load(open(os.path.join(RAW, 'ose.json')))
ids = ['ose.enc.terrain-a', 'ose.enc.terrain-b', 'ose.enc.sub1', 'ose.enc.sub2', 'ose.enc.B', 'ose.enc.C', 'ose.enc.D',
       'ose.enc.F', 'ose.enc.G', 'ose.enc.J', 'ose.enc.L', 'ose.enc.O', 'ose.enc.S']
tables = {}
for tid, t in zip(ids, raw):
    rows = [[r[0]] + [clean(c) for c in r[1:]] for r in t['rows'] if r[0].strip().isdigit() and int(r[0]) <= t['size']]
    d = {'title': clean(t['title']), 'die': t['die'], 'page': t['page'], 'cols': [clean(c) for c in t.get('cols', [])],
         'rows': rows}
    if check(d): d['review'] = '; '.join(check(d))
    tables[tid] = d
OSE_TITLES = {'ose.enc.sub1': 'Sub-table 1', 'ose.enc.sub2': 'Sub-table 2', 'ose.enc.B': 'Sub-table B: Broken, Hills, Mountains',
              'ose.enc.C': 'Sub-table C: City, Settled', 'ose.enc.D': 'Sub-table D: Desert', 'ose.enc.F': 'Sub-table F: Forest',
              'ose.enc.G': 'Sub-table G: Clear, Grasslands', 'ose.enc.J': 'Sub-table J: Jungle', 'ose.enc.L': 'Sub-table L: Lake, River',
              'ose.enc.O': 'Sub-table O: Ocean, Sea', 'ose.enc.S': 'Sub-table S: Swamp'}
for k, v in OSE_TITLES.items():
    if k in tables: tables[k]['title'] = 'Wilderness Encounter ' + v
# the two d8 grids: one table per terrain
for tid in ('ose.enc.terrain-a', 'ose.enc.terrain-b'):
    t = tables.pop(tid)
    for c, col in enumerate(t['cols']):
        tables['ose.enc.by.' + slug(col)] = {'title': f'Encounter type — {col}', 'die': 'd8', 'page': t['page'],
                                             'rows': [[r[0], r[c + 1]] for r in t['rows']]}
emit('ose', SOURCES['ose'], tables)

# ------------------------------------------------------------------ Spectacular Settlements, CWN NPCs, Montfroid
from_extract('ss')
from_extract('mont')
from_extract('uvg', keep=lambda t: t['pdf_page'] in (10, 177, 178, 180, 184, 196, 257))
from_extract('cwn', keep=lambda t: t['page'] in range(134, 136) or t['page'] in (186,))

# ------------------------------------------------------------------ Overland Hexcrawl (Simplified) harvest
def md_clean(c):
    c = clean(c).replace('**', '')
    return re.sub(r'(?<=\w)\*+$', '', c).strip()


def split_side_by_side(cols, rows, die):
    """['', 'A', '', 'B'] or ['1d6','Faction','1d10','Hold'] → several (die, cols, rows)."""
    cells = [r if r[0] is not None else r[1:] for r in rows]
    heads = cols if rows[0][0] is not None else cols
    n = len(cells[0])
    hd = lambda j: (heads[j] if j < len(heads) else '') or ''
    lab = [j for j in range(n) if (j == 0 or hd(j) == '' or re.match(r'^\d*d\d+$', hd(j)))
           and all(c[j] == '' or parse_label(c[j], 100) for c in cells)
           and sum(1 for c in cells if c[j]) >= len(cells) * 0.6]
    if not lab or lab[0] != 0:
        return [(die, cols, rows)]
    out = []
    for k, j in enumerate(lab):
        end = lab[k + 1] if k + 1 < len(lab) else n
        h = heads[j] if j < len(heads) else ''
        m = re.match(r'^\d*d\d+$', h or '')
        d = h if m else die
        seg = [c[j:end] for c in cells if c[j]]
        out.append((d, heads[j + 1:end], seg))
    return out


def from_harvest(key, prefix, srcid):
    raw = json.load(open(os.path.join(RAW, key + '.json')))
    tables, seen = {}, {}
    for t in raw:
        cols = t['cols']; rows = [r for r in t['rows'] if isinstance(r, list) and len(r) == len(cols)]
        if not rows: continue
        rows = [[md_clean(c) for c in r] for r in rows]
        die = (t.get('die') or '').strip()
        m = re.match(r'^(\d*d\d+)\b', die)
        die = m.group(1) if m else None
        caption = md_clean(t.get('caption', ''))
        parts = split_side_by_side(cols, rows, die) if all(parse_label(r[0], 100) or r[0] == '' for r in rows) else [(die, cols[1:], rows)]
        if len(parts) == 1 and parts[0][2] is rows and not all(parse_label(r[0], 100) for r in rows):
            parts = [(None, cols, [[None] + r for r in rows])]
        merged = len(parts) == 2 and parts[0][1] == parts[1][1]
        if merged:  # same columns twice = one long table
            parts = [(parts[0][0], parts[0][1], parts[0][2] + parts[1][2])]
        for i, (pd, pcols, prow) in enumerate(parts):
            sub = '' if len(parts) == 1 else '.' + slug(pcols[0] if pcols and pcols[0] else str(i + 1), 24)
            base = f'{prefix}.{slug(caption) or "table"}{sub}'
            seen[base] = seen.get(base, 0) + 1
            tid = base if seen[base] == 1 else f'{base}-{seen[base]}'
            labelled = all(r[0] is not None and parse_label(r[0], 100) for r in prow)
            d = {'title': caption + (f' — {pcols[0]}' if sub and pcols else ''), 'page': None,
                 'cols': [clean(c) for c in pcols], 'rows': prow if labelled else [[None] + [c for c in r if c is not None] for r in prow]}
            if pd and labelled: d['die'] = pd
            if t.get('src'): d['note'] = 'source: ' + clean(t['src'])
            if d.get('die') and check(d): d['review'] = '; '.join(check(d))
            tables[tid] = d
    if 'oh.rumors-in-the-reaches-1-50' in tables:
        a = tables.pop('oh.rumors-in-the-reaches-1-50'); b = tables.pop('oh.rumors-in-the-reaches-51-100')
        a['rows'] += b['rows']; a['title'] = 'Rumors in the Reaches'; a.pop('review', None)
        tables['oh.rumors-wr'] = a
    emit(key, SOURCES[key], tables)

from_harvest('oh', 'oh', 'OH')


def from_tft():
    """raw/tft.json (harvest_tft.py) → data/gen/tft.yaml: the ten Wildland 4d6 tables."""
    tables = {}
    for t in json.load(open(os.path.join(RAW, 'tft.json'))):
        tables[t['id']] = {'title': t['title'], 'page': t['page'], 'die': t['die'], 'cols': t['cols'],
                           'rows': t['rows'], 'note': f"party LV {t['party_lv']} · {t['terrain']}"}
    emit('tft', SOURCES['tft'], tables)


from_tft()
from_harvest('sea', 'sea', 'SV')
