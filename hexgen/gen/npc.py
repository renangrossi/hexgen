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
    for label, tid in [('Virtue', 'cwn.p135.notable-npc-virtues-or-qualities'), ('Flaw', 'cwn.p135.npc-personality-flaws'),
                       ('Problem', 'cwn.p135.current-npc-problems'), ('Desire', 'cwn.p135.current-npc-desires')]:
        if R.dice.chance(1, 2):
            L.append(roll(R, label, tid))
    out['lines'] = [x for x in L if x]
    return out


BONDS = {'a friendship': [('Met', 'wwn.p385.how-did-they-meet'), ('Done together', 'wwn.p385.what-have-they-done-together'),
                          ('Holds them together', 'wwn.p385.what-tie-harmonizes-their-differences'),
                          ('Threatens it', 'wwn.p385.what-threatens-to-divide-them')],
         'a tragedy': [('What happened', 'wwn.p386.what-was-its-basic-form'), ('When', 'wwn.p386.when-did-it-happen'),
                       ('Their part in it', 'wwn.p386.what-was-their-responsibility-for-it'),
                       ('After', 'wwn.p386.what-ugly-consequences-followed'), ('Scars', 'wwn.p386.what-scars-do-they-have-from-it')],
         'a romance': [('Met', 'wwn.p387.how-did-they-meet'), ('Sparked by', 'wwn.p387.what-sparked-the-romance'),
                       ('Trouble', 'wwn.p387.what-problem-does-one-or-both-have'), ('Now', 'wwn.p387.whats-the-current-issue-they-face')]}


def bond(R, person):
    """Give an NPC a friendship, tragedy or romance from WWN pp. 385–387."""
    kind = R.dice.pick(list(BONDS))
    with_whom = name_person(R)
    lines = [roll(R, lab, tid) for lab, tid in BONDS[kind]]
    person['lines'].append({'label': 'Bond', 'text': f'{kind} with {with_whom}', 'cite': 'WWN'})
    person['lines'] += [l for l in lines if l]
    return person
