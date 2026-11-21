"""Ships met at sea or found at anchor.

Of Ships & the Sea gives type, purpose, attitude, crew and disposition; the Overland
Hexcrawl sea tables give the hull's state, faction, hold, crew mood, one crew member and
the ship's story; Sea Voyages' boat list supplies Shadowdark stats for the hull.
"""
from .common import line

# OSS type → Sea Voyages boat row name (for SD stats)
SV_BOAT = {'Rowboat': 'Rowboat', 'Keelboat': 'Sailboat', 'Longship': 'Longship', 'Sailing ship': 'Sloop',
           'Galley': 'Galley', 'Warship': 'Galleon'}


def boat_stats(R, kind):
    if 'sea.boats' not in R:
        return None
    want = SV_BOAT.get(kind, kind).lower()
    for r in R.get('sea.boats').rows:
        if r[1].lower().startswith(want[:5]):
            cols = R.get('sea.boats').cols
            return dict(zip(cols, r[1:]))
    return None


def ship(R, in_port=False):
    kind = R.text('oss.ship.type')
    purpose = R.text('oss.ship.purpose')
    att = R.text('oss.ship.attitude') if not in_port else R.dice.pick(['Friendly', 'Neutral', 'Neutral'])
    crew = R.text(f'oss.ship.crew.{att.lower()}')
    nm = R.roll('oss.ship.name')['values']
    name = f"The {nm['Adjective']} {nm['Noun']}"
    s = {'name': name, 'type': kind, 'purpose': purpose, 'attitude': att, 'crew': crew,
         'stats': boat_stats(R, kind), 'lines': []}
    L = s['lines']
    if purpose == 'Ghost':
        L.append(line('Disposition', 'A ghost ship; it cannot be diseased', 'OSS p.3'))
    else:
        L.append(line('Disposition', R.roll('oss.ship.disposition')))
    L.append(line('State', R.roll('oh.the-vessel.state')))
    L.append(line('Hold', R.roll('oh.who-crews-it.in-the-hold')))
    L.append(line('Crew are', R.roll('oh.the-crew.they-are')))
    one = R.roll('oh.the-crew.one-of-them-is')
    cn = R.roll('oss.crew.name')['values']
    L.append(line('Aboard', f"{one['text']}, called “{cn['First half']} {cn['Second half']}”", one['cite'] + ', OSS p.3'))
    st = R.roll('oh.her-story')
    if not st['text'].startswith('None'):
        L.append(line('Her story', st))
    return s
