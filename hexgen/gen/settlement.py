"""Settlements, from a crossroads to a capital, and the port that a coastal one keeps.

Layers, richest first:
  Spectacular Settlements — the full procedure for that size (origin, age, condition,
      leadership, law, crime, wealth, faith, history, events, opportunities, danger)
  Worlds Without Number   — why it exists, who runs it, a pressing problem, a local who
      needs the PCs, what it offers, and two Community tags with enemies/friends/
      complications/things/places
  Perilous Wilds          — one feature and one problem with their steading tags
  Overland Hexcrawl       — districts and what stands in each, shops, a tavern with its
      menu and drinks, events, rumours; Shadowdark core district encounter tables
"""
import re
from .common import line, roll, tidy_ss, first_sentence, name_settlement, name_person
from .npc import npc

# Spectacular Settlements: printed page ranges of each chapter
SS_RANGE = {'trading post': (10, 30), 'village': (49, 67), 'town': (95, 113), 'city': (141, 172),
            'capital': (209, 251), 'fortress': (297, 321)}
SS_SKIP = re.compile(r'additional-locations|^shops|^services|quality|hired-help|table-title|base-size|thickness|'
                     r'height|tower-|curtain|moat|gatehouse|outbuilding|barracks|number-of|shape|floors|rooms|'
                     r'raised-entrance|entry-defenses|exterior-wall|vendor|overflow|market-square|magic-shop|'
                     r'district|housing|noble-residence|guild-member|shop-or-service|non-commercial|'
                     r'location-notability|place-of-worship|fervency|alignment-of|resource-origin|'
                     r'population-capacity|primary-nobles|connection|visitor-roles|reason-for-visit|'
                     r'how-much-you-love|change$|^name|environment|^weather|danger-level')
# Overland Hexcrawl settlement types (rows of oh.settlement-type, in order) per size
OH_TYPE_ROWS = {'trading post': [0], 'village': [1, 2], 'town': [3, 4], 'city': [5, 6, 7],
                'capital': [8, 9], 'fortress': [4]}
PW_KIND = {'trading post': 'village', 'village': 'village', 'town': 'town', 'city': 'city', 'capital': 'city',
           'fortress': 'keep'}
WWN_KIND = {'trading post': 'p145', 'village': 'p145', 'town': 'p146', 'city': 'p146', 'capital': 'p146',
            'fortress': 'p147'}
DISTRICT_TABLE = {'Transient': 'oh.transient-and-craft.transient', 'Craft': 'oh.transient-and-craft.craft',
                  'Common': 'oh.common-and-mercantile.common', 'Mercantile': 'oh.common-and-mercantile.mercantile',
                  'Affluent': 'oh.affluent-and-education.affluent', 'Education': 'oh.affluent-and-education.education',
                  'Religious': 'oh.religious-and-military.religious', 'Military': 'oh.religious-and-military.military',
                  'Spectacle': 'oh.spectacle-and-palace.spectacle', 'Palace': 'oh.spectacle-and-palace.palace'}


def ss_profile(R, size):
    lo, hi = SS_RANGE[size]
    out, seen = [], set()
    for tid in sorted(R.tables, key=lambda t: (R.tables[t].page or 0, t)):
        if not tid.startswith('ss.'):
            continue
        t = R.tables[tid]
        slug = tid.split('.', 2)[2]
        if not (lo <= (t.page or 0) <= hi) or SS_SKIP.search(slug) or getattr(t, 'review', None):
            continue
        key = re.sub(r'-\d+$', '', slug)
        if key in seen:
            continue
        seen.add(key)
        words = []
        for w in re.split(r'\s(?=\S\s\S\s)', t.title)[0].split():
            if w[0].isupper() or w in ('of', 'the', 'and', 'in', 'a', '-', 'to'):
                words.append(w)
            else:
                break
        title = ' '.join(words[:5]).rstrip(' -') or t.title
        res = R.roll(tid)
        res['text'] = str(next(iter(res['values'].values()), res['text']))
        # a sidebar caught on the same baseline usually starts after a full stop with a lowercase word
        res['text'] = re.split(r'(?<=\.)\s+(?=[a-z])|\s+\d+\s+[A-Z][a-z]+(?:-[A-Z][a-z]+)?\.\s', res['text'])[0]
        text = tidy_ss(re.sub(r'^Note:.*?(?=[A-Z][a-z]+\.)', '', res['text']))
        if text:
            out.append({'label': title, 'text': text, 'cite': res['cite']})
    return out


def wwn_layer(R, size):
    p = WWN_KIND[size]
    L = []
    if p == 'p145':
        L.append(roll(R, 'Why it is here', 'wwn.p145.rationale-for-the-villages-existence'))
    elif p == 'p146':
        L.append(roll(R, 'Why it is here', 'wwn.p146.rationale-for-the-citys-existence'))
    else:
        L.append(roll(R, 'Why it is here', 'wwn.p147.why-are-they-staying-here'))
    base = f'wwn.{p}.who-runs-it-significant-locals-a-current'
    for col, label in [('Who Runs It?', 'Who runs it'), ('Significant Locals', 'A notable local'),
                       ('A Current Pressing Problem', 'Pressing problem')]:
        L.append(roll(R, label, base, col))
    base = f'wwn.{p}.local-likely-to-interact-with-adventurer'
    L.append(roll(R, 'Who comes to the PCs', base, 'Local Likely to Interact with Adventurers'))
    L.append(roll(R, 'What it can offer heroes', base, 'Interesting Things the Place Can Offer Heroes'))
    return [x for x in L if x]


def community_tags(R, n=2):
    tags = R.extras.get('wwn_tags', {}).get('community', {})
    names = R.dice.shuffle(list(tags))[:n]
    out = []
    for name in names:
        t = tags[name]
        out.append({'tag': name, 'desc': t['desc'], 'cite': 'WWN p.' + str(R.get('wwn.tag.community').page),
                    'enemy': R.dice.pick(t['enemies']) if t['enemies'] else '',
                    'friend': R.dice.pick(t['friends']) if t['friends'] else '',
                    'complication': R.dice.pick(t['complications']) if t['complications'] else '',
                    'thing': R.dice.pick(t['things']) if t['things'] else '',
                    'place': R.dice.pick(t['places']) if t['places'] else ''})
    return out


def districts(R, size, system):
    t = R.get('oh.settlement-type')
    row = t.rows[R.dice.pick(OH_TYPE_ROWS[size])]
    kind, n = row[1], R.dice.roll(row[2])
    n = max(1, min(n, 12))
    names = [r[1] for r in R.get('oh.district-type').rows]
    out = []
    for i in range(n):
        d = R.dice.pick(names)
        key = d.split()[0]
        stands = [R.text(DISTRICT_TABLE[key]) for _ in range(R.dice.between(1, 3))] if key in DISTRICT_TABLE else []
        enc = system.town_encounter(R, key)
        out.append({'name': d, 'stands': stands, 'encounter': enc})
    return kind, out


def tavern(R):
    a, b, c = (R.roll('oh.tavern-generator') for _ in range(3))
    cls = R.dice.pick(['Poor — 1d4 cp', 'Standard — 1d6 sp', 'Wealthy — 1d8 gp'])
    name = f"{a['values']['Name']} {b['values']['Name 2']}"
    t = a
    return {'name': name, 'known_for': c['values']['Known for'],
            'menu': R.text('oh.menu', cls), 'drink': R.text('oh.drinks'), 'class': cls.split(' —')[0],
            'cite': t['cite']}


def settlement(R, system, size='village', coastal=False, terrain='grassland', name=None):
    s = {'name': name or name_settlement(R), 'size': size, 'coastal': coastal, 'terrain': terrain}
    s['ss'] = ss_profile(R, size)
    s['wwn'] = wwn_layer(R, size)
    s['tags'] = community_tags(R, 2 if size in ('village', 'trading post') else 3)
    k = PW_KIND[size]
    s['pw'] = [x for x in [roll(R, 'Feature', f'pw.steading.{k}.feature'), roll(R, 'Problem', f'pw.steading.{k}.problem')] if x]
    s['oh_type'], s['districts'] = districts(R, size, system)
    s['shops'] = sorted({R.text('oh.shops', R.dice.pick(['Poor', 'Standard', 'Standard', 'Wealthy']))
                         for _ in range({'trading post': 2, 'village': 3, 'town': 5, 'city': 8, 'capital': 10,
                                         'fortress': 2}[size])})
    s['tavern'] = tavern(R)
    s['event'] = roll(R, 'Event', 'oh.settlement-events')
    s['rumours'] = [roll(R, 'Rumour', 'oh.rumours') for _ in range(3)]
    roles = [('ruler or headman', 'gentry'), ('innkeeper', 'commoner'), ('someone who needs help', None)]
    if size in ('city', 'capital'):
        roles += [('rival', 'gentry'), ('fixer', 'underclass')]
    s['npcs'] = [npc(R, role, st) for role, st in roles]
    s['environment'] = terrain
    s['hirelings'] = [hireling(R) for _ in range({'trading post': 1, 'village': 1, 'fortress': 2}.get(size, 3))]
    if size in ('town', 'city', 'capital', 'trading post'):
        s['jobs'] = [trade_job(R) for _ in range(2)]
    if size in ('town', 'city', 'capital'):
        s['temple'] = [x for x in [roll(R, 'In charge', 'wwn.p139.who-is-in-charge-there'),
                                   roll(R, 'Can provide', 'wwn.p139.what-particular-help-can-it-provide'),
                                   roll(R, 'Trouble', 'wwn.p139.what-problems-does-it-have'),
                                   roll(R, 'Quirk', 'wwn.p139.particular-quirks-about-the-temple')] if x]
    if coastal:
        s['port'] = port(R, size)
    return s


def hireling(R):
    """WWN Montfroid hireling tables (p. 29) with an OH name."""
    return {'name': name_person(R), 'lines': [x for x in [
        roll(R, 'Was', 'mont.p29.what-was-their-original-profession'), roll(R, 'Age', 'mont.p29.how-old-is-the-hireling'),
        roll(R, 'Fights', 'mont.p29.how-do-they-fight'), roll(R, 'Also', 'mont.p29.what-other-talent-do-they-have'),
        roll(R, 'Signs on because', 'mont.p29.why-are-they-doing-this'),
        roll(R, 'Quirk', 'mont.p29.particular-traits-or-personality-quirks')] if x]}


def trade_job(R):
    """A merchant's commission: UVG trade-job tables (p. 180)."""
    a = R.roll('uvg.p180.they-want-because'); b = R.roll('uvg.p180.the-catch-is-and-the-destination')
    va, vb = list(a['values'].values()), list(b['values'].values())
    va[0] = va[0].rstrip('.').replace('. ', ', ')
    return line('Trade job', f"They want {va[0].lower()}, because {va[-1][0].lower() + va[-1][1:]} "
                f"The catch: {vb[0][0].lower() + vb[0][1:]} Bound for {vb[-1][0].lower() + vb[-1][1:]}", a['cite'])


# ---------------------------------------------------------------------------- ports
PORT_ROW = {'trading post': 0, 'village': 0, 'fortress': 0, 'town': 1, 'city': 2, 'capital': 2}


def port(R, size):
    t = R.get('sea.port-d6')
    row = t.rows[min(PORT_ROW[size], len(t.rows) - 1)]
    p = {'kind': row[1], 'has': row[2], 'cite': t.cite()}
    q = R.roll('sea.in-port')
    p['rules'] = q['values'].get('Who rules'); p['trouble'] = q['values'].get('Trouble on the quay'); p['rcite'] = q['cite']
    n = {'trading post': 1, 'village': 1, 'fortress': 1, 'town': 3, 'city': 5, 'capital': 7}[size]
    from .ship import ship
    p['ships'] = [ship(R, in_port=True) for _ in range(n)]
    a = R.roll('oh.available-ship')
    c = R.roll('oh.captain')
    p['passage'] = {'ship': a['values'], 'captain': c['values'], 'cite': a['cite']}
    return p
