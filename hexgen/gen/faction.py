"""Powers of the region: WWN courts (with Court tags) and OH factions, and how they
stand toward each other (OH relation tables)."""
from .common import line, roll, name_person

COURT_PAGES = {'Noble court': 'p163', 'Merchant house': 'p164', 'Criminal court': 'p165',
               'Barbarian court': 'p166', 'Priestly court': 'p167'}


def court(R):
    kind = R.dice.pick(list(COURT_PAGES))
    p = COURT_PAGES[kind]
    base = f'wwn.{p}.major-figure-minor-figure-the-source-of'
    tags = R.extras.get('wwn_tags', {}).get('court', {})
    tag = R.dice.pick(list(tags)) if tags else None
    L = [roll(R, 'Theme', 'wwn.p163.main-theme-of-the-court'),
         roll(R, 'Major figure', base, 'Major Figure'), roll(R, 'Minor figure', base, 'Minor Figure'),
         roll(R, 'Their power rests on', base, 'The Source of their Power in the Court'),
         roll(R, 'Inside, they fight over', f'wwn.{p}.internal-conflicts-external-conflicts', 'Internal Conflicts'),
         roll(R, 'Outside, they fight over', f'wwn.{p}.internal-conflicts-external-conflicts', 'External Conflicts')]
    extra = [t for t in R.find(f'wwn.{p}.') if not any(x in t for x in ('major-figure', 'internal-conflicts', 'main-theme'))]
    for t in extra:
        L.append(roll(R, R.get(t).title, t))
    if tag:
        t = tags[tag]
        L.append(line(f'Tag: {tag}', t['desc'], f"WWN p.{R.get('wwn.tag.court').page}"))
        for k, lab in [('enemies', 'Enemy'), ('friends', 'Friend'), ('complications', 'Complication')]:
            if t[k]: L.append(line(lab, R.dice.pick(t[k])))
    return {'name': f'{kind} of {name_person(R).split()[1]}', 'kind': kind, 'lines': [l for l in L if l]}


def faction(R):
    f = R.roll('oh.faction-generator')['values']
    return {'name': f"The {f.get('Symbol', 'Sign')}", 'kind': 'Faction',
            'lines': [line('Mission', f.get('Mission', ''), 'OH'), line('Symbol', f.get('Symbol', ''), 'OH'),
                      line('Led by', f"{f.get('Leader', '')}, {name_person(R)}", 'OH')]}


def relations(R, powers):
    """OH 'Between two domains' (2d6) sets the stance; its column says why."""
    out = []
    cols = R.get('oh.what-the-relationship-is').cols
    for i, a in enumerate(powers):
        for b in powers[i + 1:]:
            st = R.roll('oh.between-two-domains')
            state = next((c for c in cols if c.lower() in st['text'].lower()), R.dice.pick(cols))
            why = R.roll('oh.what-the-relationship-is', state)
            out.append({'a': a['name'], 'b': b['name'], 'state': state, 'why': why['text'],
                        'cite': f"{st['cite']}, {why['cite']}"})
    return out
