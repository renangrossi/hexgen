"""NPCs: a name, a station, a look, a want, and a hook — WWN's NPC tables (pp. 380–387)
with names from the Overland Hexcrawl name lists."""
from .common import line, roll, name_person

STATION = {'underclass': 'Underclass', 'commoner': 'Commoners', 'gentry': 'Gentry'}
SPECIFIC = ['wwn.p381.specific-criminals', 'wwn.p381.specific-merchants', 'wwn.p381.specific-nobility',
            'wwn.p381.specific-tribals', 'wwn.p381.specific-villagers', 'wwn.p381.specific-warriors']


def npc(R, role=None, station=None):
    st = station or R.dice.pick(['underclass', 'commoner', 'commoner', 'gentry'])
    out = {'name': name_person(R), 'role': role or '', 'lines': []}
    L = out['lines']
    if 'wwn.p380.underclass-commoners-gentry' in R:
        L.append(roll(R, 'Who', 'wwn.p380.underclass-commoners-gentry', STATION[st]))
    for label, tid in [('First noticed', 'wwn.p383.the-first-thing-noticed'),
                       ('Manner', 'wwn.p383.visible-mannerisms-or-traits'),
                       ('Unexpected', 'wwn.p383.one-way-they-differ-from-expectations'),
                       ('Twist', 'wwn.p380.npc-characteristic-twists'),
                       ('Wants', 'wwn.p384.whats-the-basic-ambitions-form'),
                       ('In the way', 'wwn.p384.whats-the-biggest-immediate-obstacle')]:
        r = roll(R, label, tid)
        if r: L.append(r)
    out['lines'] = [x for x in L if x]
    return out
