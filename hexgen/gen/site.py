"""What is in a wilderness hex.

Stocking follows the Overland Hexcrawl content roll (1d6: hazard / empty / special /
monsters) and layers the richer books on each result:
  hazard   → OH terrain hazards (move/damage/weaken) + PW hazard prompt
  empty    → OH 'what can be learned here' + how you learn it
  special  → OH special → disputes / threats / mysteries / an NPC in trouble
  monsters → the system's terrain encounter table, PW disposition and activity
Points of interest (OH by terrain), landmarks (OH, from the Sandbox Generator Landmarks
expansion), PW discoveries, WWN wilderness tags, ruins (WWN ruin chapter + ruin tags +
PW dungeon overview + OH dungeon tables) and lairs come on top.
"""
from .common import line, roll
from ..systems import OH_SLUG

SPECIAL_TABLE = {'Arbitrate a dispute': 'oh.disputes-to-arbitrate', 'Prevent a threat': 'oh.threats-to-prevent',
                 'Uncover a mystery': 'oh.mysteries-to-uncover', 'NPC(s)/Monster(s) in need': 'oh.trouble-an-npc-is-in'}
LANDMARK = {'Natural': ('oh.natural-landmarks-d6-1-to-3', 'oh.natural-landmarks-d6-4-to-6'),
            'Artificial': ('oh.artificial-landmarks-d6-1-to-3', 'oh.artificial-landmarks-d6-4-to-6'),
            'Magic': ('oh.magic-landmarks-d6-1-to-3', 'oh.magic-landmarks-d6-4-to-6')}


def item(kind, title, lines, cite=''):
    return {'kind': kind, 'title': title, 'lines': [l for l in lines if l], 'cite': cite}


def hazard(R, terrain):
    tid = f'oh.hazards-{OH_SLUG[terrain]}'
    col = R.dice.pick([0, 0, 1, 1, 2, 2])
    h = R.roll(tid, col) if tid in R else None
    kind = (R.get(tid).cols[col] if h else '').split(' ', 1)[-1]
    return item('hazard', 'Hazard', [line(f'{kind} hazard', h) if h else None,
                                     roll(R, 'Why it is dangerous', 'oh.hazard'),
                                     roll(R, 'Prompt', 'pw.hazard')])


def empty(R):
    return item('lore', 'Something to learn', [roll(R, 'What can be learned', 'oh.empty'),
                                               roll(R, 'How it comes', 'oh.how-you-learn-it')])


def special(R):
    s = R.roll('oh.special')
    sub = SPECIAL_TABLE.get(s['text'])
    lines = [line('Situation', s)]
    if sub:
        lines.append(roll(R, 'Detail', sub))
    elif 'landmark' in s['text'].lower():
        lines.append(landmark(R)['lines'][0])
    else:
        lines.append(roll(R, 'Prompt', 'pw.discovery'))
    return item('special', 'Situation', lines)


def monsters(R, system, hx):
    e = system.encounter(R, hx.terrain, hx.river, hx.coast)
    return item('creatures', 'Creatures', [line('Who', e['text'], e['cite']),
                                           roll(R, 'Mood', 'pw.disposition'), roll(R, 'Doing', 'pw.activity')])


def landmark(R):
    kind = R.text('oh.what-kind')
    a, b = LANDMARK.get(kind, LANDMARK['Natural'])
    k = R.dice.roll('d6')
    tid, col = (a, k - 1) if k <= 3 else (b, k - 4)
    res = R.roll(tid, col)
    return item('landmark', 'Landmark', [line(f'{kind} — {R.get(tid).cols[col].split(" ", 1)[-1]}', res),
                                         roll(R, 'Seen', 'pw.visibility')])


def poi(R, terrain):
    tid = f'oh.points-of-interest-{OH_SLUG[terrain]}'
    if tid not in R:
        return None
    r = R.roll(tid)
    v = r['values']
    return item('poi', v.get('Location', r['text']), [line('Development', v.get('Development', ''), r['cite'])])


def wilderness_tag(R):
    tags = R.extras.get('wwn_tags', {}).get('wilderness', {})
    if not tags:
        return None
    name = R.dice.pick(list(tags)); t = tags[name]
    page = R.get('wwn.tag.wilderness').page
    pick = lambda k: R.dice.pick(t[k]) if t[k] else ''
    return item('tag', name, [line('', t['desc'], f'WWN p.{page}'), line('Enemy', pick('enemies')),
                              line('Friend', pick('friends')), line('Complication', pick('complications')),
                              line('Thing', pick('things')), line('Place', pick('places'))])


def ruin(R, system):
    tags = R.extras.get('wwn_tags', {}).get('ruin', {})
    kind = R.roll('wwn.p183.what-basic-kind-of-ruin-is-it')
    L = [line('What it was', kind),
         roll(R, 'Age', 'wwn.p183.how-old-is-the-ruin'),
         roll(R, 'How it fell', 'wwn.p183.how-did-it-become-ruined'),
         roll(R, 'Since then', 'wwn.p183.whos-used-the-ruin-before'),
         roll(R, 'Not yet plundered because', 'wwn.p183.why-hasnt-it-been-plundered-bare-yet'),
         roll(R, 'Locals say', 'wwn.p183.what-do-the-locals-think-of-it'),
         roll(R, 'Form', 'pw.dungeon.form'),
         roll(R, 'Way in', 'pw.p66.accessibility') if 'pw.p66.accessibility' in R else None,
         roll(R, 'Dungeon type', 'oh.dungeon-type'), roll(R, 'Size', 'oh.dungeon-size'),
         roll(R, 'Quirk inside', 'oh.dungeon-effects'),
         roll(R, 'Hazard', 'wwn.p241.example-types-of-hazards'),
         roll(R, 'Enigma', 'wwn.p241.example-enigmas'),
         roll(R, 'Treasure hidden in', 'wwn.p241.possible-treasure-locations')]
    if tags:
        name = R.dice.pick(list(tags)); t = tags[name]
        L.append(line(f'Tag: {name}', t['desc'], f"WWN p.{R.get('wwn.tag.ruin').page}"))
        for k, lab in [('enemies', 'Enemy'), ('complications', 'Complication'), ('things', 'Thing')]:
            if t[k]: L.append(line(lab, R.dice.pick(t[k])))
    e = system.dungeon_encounter(R, 'ruins')
    L.append(line('Wandering inside', e['text'], e['cite']))
    L.append(roll(R, 'Treasure', R.dice.pick(['oh.treasure-0-3', 'oh.treasure-4-6', 'oh.treasure-7-9'])))
    return item('ruin', 'Ruin', L)


def lair(R, system, hx):
    e = system.encounter(R, hx.terrain, hx.river, hx.coast)
    return item('lair', 'Lair', [line('Whose', e['text'], e['cite']),
                                 roll(R, 'What it is doing', 'wwn.p229.whats-that-bestial-monster-doing'),
                                 roll(R, 'Complication', 'wwn.p229.wilderness-lair-complications'),
                                 roll(R, 'Lair', 'pw.natural.lair'),
                                 roll(R, 'Hoard', R.dice.pick(['oh.treasure-0-3', 'oh.treasure-4-6']))])


def stock(R, system, hx):
    """Fill one land hex."""
    out = []
    c = R.text('oh.content-and-treasure', 'What is here')
    if c == 'Hazard':
        out.append(hazard(R, hx.terrain))
    elif c == 'Empty':
        out.append(empty(R))
    elif c == 'Special':
        out.append(special(R))
    else:
        out.append(monsters(R, system, hx))
    if R.dice.chance(1, 3):
        out.insert(0, poi(R, hx.terrain))
    if R.dice.chance(1, 4):
        out.append(landmark(R))
    if R.dice.chance(1, 4):
        out.append(item('discovery', 'Discovery', [roll(R, 'Found', 'pw.discovery')]))
    return [o for o in out if o]


def sea_hex(R, system, hx, near_land=False):
    out = []
    u = R.roll('sea.uncharted-hex-1-for-each-open-sea-in-a-r')
    if not u['text'].startswith('Open sea'):
        out.append(item('sea', 'At sea', [line('The hex holds', u['text'].split('(§')[0].strip(), u['cite'])]))
        if 'vessel' in u['text'].lower() or 'sail' in u['text'].lower():
            from .ship import ship
            s = ship(R)
            out.append(item('ship', s['name'], [line('Ship', f"{s['type']}, {s['purpose'].lower()}, {s['attitude'].lower()}; crew of {s['crew'].lower()}", 'OSS p.3')] + s['lines']))
    if R.dice.chance(1, 3):
        out.append(item('sea', 'Find', [roll(R, 'On the water', 'sea.finds')]))
    if 'island' in u['text'].lower() or R.dice.chance(1, 6):
        out.append(item('sea', 'Island', [roll(R, 'Island', 'sea.island'), roll(R, 'Name', 'pw.place.template')]))
    if near_land and R.dice.chance(1, 3):
        p = poi(R, 'sea')
        if p: out.append(p)
    if R.dice.chance(1, 3):
        e = system.encounter(R, 'sea')
        out.append(item('creatures', 'Creatures', [line('Who', e['text'], e['cite'])]))
    return out
