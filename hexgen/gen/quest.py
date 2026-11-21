"""Quests and adventures.

quest()      — a job a settlement offers: Overland Hexcrawl's quest generator (source,
               trouble, urgency, archetype and objective, patron and reward, where) with
               WWN's hook, investigation and negotiation tables on top.
adventure()  — a regional adventure seed from WWN's adventure creation chapter
               (pp. 227–249) and its idea tables (pp. 372–373).
"""
from .common import line, roll, name_person


def quest(R):
    q = R.roll('oh.quest-archetypes')
    p = R.roll('oh.patron')
    L = [line('Comes as', R.roll('oh.quest-source')),
         line('The trouble', R.roll('oh.type-of-trouble')),
         line('Urgency', R.roll('oh.urgency')),
         line('Where', R.roll('oh.location')),
         line('Objective', q['values'].get('Objective', ''), q['cite']),
         line('Patron', f"{p['values'].get('Who', '')}, {name_person(R)} — {p['values'].get('Reward', '')}", p['cite']),
         roll(R, 'Why it hooks', 'wwn.p247.what-makes-the-hook-so-enticing'),
         roll(R, 'Patron will not simply cooperate because', 'wwn.p249.why-wont-they-cooperate'),
         roll(R, 'Their weak point', 'wwn.p249.whats-their-weakest-point'),
         roll(R, 'Complication', 'wwn.p246.possible-investigation-complications'),
         roll(R, 'A clue costs', 'wwn.p247.whats-the-cost-of-the-clue'),
         roll(R, 'Twist at the end', 'wwn.p246.twists-to-the-resolution')]
    if any(w in q['text'].lower() for w in ('dungeon', 'lair', 'hideout', 'tomb', 'crypt', 'ruin')):
        L.insert(5, line('Dungeon', f"{R.text('oh.dungeon-type')}, {R.text('oh.dungeon-size').lower()}", 'OH'))
    return {'title': q['values'].get('Quest', q['text']), 'lines': [l for l in L if l and l['text']]}


def adventure(R):
    L = [roll(R, 'Bait', 'wwn.p372.bait-for-adventure-hooks'),
         roll(R, 'How it reaches the PCs', 'wwn.p372.ways-of-introducing-an-adventure-hook'),
         roll(R, 'Theme', 'wwn.p373.this-theme-informs-the-adventure'),
         roll(R, 'What is going on', 'wwn.p228.whats-going-on-right-now'),
         roll(R, 'The target’s troubles', 'wwn.p228.what-problems-do-they-have-may-or-may-no', 0),
         roll(R, 'Twist', 'wwn.p228.twists-about-the-target-or-their-allies'),
         roll(R, 'A mistake that twists it', 'wwn.p373.this-mistake-twists-the-adventure'),
         roll(R, 'Reality intrudes', 'wwn.p373.this-reality-intrudes-into-the-situation'),
         roll(R, 'Throw in', 'wwn.p373.throw-this-event-into-the-adventure')]
    return {'title': 'Adventure', 'lines': [l for l in L if l and l['text']]}


def family_lore(R):
    return roll(R, 'Family lore', 'oh.family-lore')
