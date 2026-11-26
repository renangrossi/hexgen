"""The realm the region belongs to: government, history, people, neighbors, building
style (WWN pp. 121–133, 374–375); its faiths and one cult (WWN pp. 136–141); and the
region's great terrain features (WWN pp. 117–119)."""
from .common import line, roll


def _lines(R, pairs):
    return [l for l in (roll(R, a, b, *c) for a, b, *c in pairs) if l and l['text']]


def realm(R):
    single = R.text('wwn.p129.number-of-rulers')
    rulers = 'wwn.p130.single-rulers' if 'single' in single.lower() or single.startswith('One') else 'wwn.p130.multiple-rulers'
    gov = _lines(R, [('Rulers', 'wwn.p129.number-of-rulers'), ('Who rules', rulers),
                     ('Ruling class', 'wwn.p129.example-ruling-classes'), ('Claim to rule', 'wwn.p129.sources-of-legitimacy'),
                     ('Holds power through', 'wwn.p129.institutions-and-agents-of-control'),
                     ('Struggle within', 'wwn.p130.current-struggle-within-the-government'),
                     ('How established', 'wwn.p131.how-established-is-the-current-ruler'),
                     ('Ministers’ trouble', 'wwn.p131.what-problems-do-their-ministers-have'),
                     ('Strength', 'wwn.p131.a-strength-of-the-government'), ('Stability', 'wwn.p131.how-stable-is-the-government'),
                     ('Officials causing problems', 'wwn.p131.officials-recently-causing-problems'),
                     ('Recent event', 'wwn.p131.recent-governmental-event')])
    hist = _lines(R, [('Origin', 'wwn.p132.how-did-they-originate'),
                      ('The first inhabitants', 'wwn.p132.what-became-of-the-original-inhabitants'),
                      ('Great crisis', 'wwn.p132.historical-crises'), ('Survived it by', 'wwn.p132.how-did-they-overcome-the-crisis'),
                      ('Height of glory', 'wwn.p133.what-was-great-about-its-peak-6-they-wer', 0),
                      ('The unabsorbed', 'wwn.p133.what-became-of-the-unabsorbed-survivors')])
    people = _lines(R, [('Build', 'wwn.p125.whats-the-typical-build-of-the-people'),
                        ('Skin', 'wwn.p125.typical-skin-colors-in-the-populace'),
                        ('Hair', 'wwn.p125.hair-color-hair-texture'),
                        ('Adornment', 'wwn.p125.optional-common-forms-of-adornment'),
                        ('Quirk', 'wwn.p125.optional-physical-quirks-or-traits'),
                        ('They esteem', 'wwn.p126.values-they-esteem'), ('And', 'wwn.p126.values-they-esteem'),
                        ('Core loyalty', 'wwn.p127.major-unit-of-social-identity'),
                        ('Model society', 'wwn.p127.example-template-societies')])
    neighbors = _lines(R, [('Dispute with a neighbor', 'wwn.p121.disputes-with-a-neighboring-state'),
                            ('Tie to a neighbor', 'wwn.p121.positive-ties-with-a-neighboring-state')])
    style = _lines(R, [('Buildings are', 'wwn.p374.architectural-adjectives'), ('Built of', 'wwn.p374.favorite-materials'),
                       ('Colors', 'wwn.p374.favorite-color-schemes'), ('Motifs', 'wwn.p375.common-visual-motifs'),
                       ('Adorned with', 'wwn.p375.structure-adornment'), ('Features', 'wwn.p375.favorite-structural-features'),
                       ('Towns laid out', 'wwn.p375.settlement-design-patterns')])
    return {'Government': gov, 'History': hist, 'People': people, 'Neighbors': neighbors, 'Building style': style}


def faith(R):
    concern = R.roll('wwn.p138.human-concern-natural-principle', R.dice.pick(['Human Concern', 'Natural Principle']))
    L = [line('God of', concern),
         roll(R, 'Role in society', 'wwn.p137.what-does-this-god-do-in-society'),
         roll(R, 'Came from', 'wwn.p136.where-did-the-god-come-from'),
         roll(R, 'Why it matters', 'wwn.p136.why-does-the-faith-matter'),
         roll(R, 'Church', 'wwn.p136.church-structures'),
         roll(R, 'Clergy', 'wwn.p137.what-are-the-clerics-like'),
         roll(R, 'Wants', 'wwn.p137.what-does-the-faith-want')]
    return {'title': 'Faith', 'lines': [l for l in L if l and l['text']]}


def cult(R):
    L = _lines(R, [('Goal', 'wwn.p141.what-general-goal-do-they-have'), ('What is horrible', 'wwn.p141.whats-so-horrible-about-the-faith'),
                   ('Rewards', 'wwn.p140.rewards-of-the-sinister-faith'), ('Enforces its will by', 'wwn.p141.how-do-the-clergy-enforce-their-will'),
                   ('Unity', 'wwn.p141.how-unified-is-the-cult'), ('Trouble', 'wwn.p141.what-problems-does-it-have'),
                   ('Trait', 'wwn.p141.specific-traits-of-the-cult')])
    return {'title': 'Cult', 'lines': L}


def great_feature(R):
    f = R.roll('wwn.p117.significant-terrain-features')
    L = [line('What', f)] + _lines(R, [('Danger', 'wwn.p119.how-dangerous-is-the-feature'), ('Use', 'wwn.p119.what-use-is-the-feature'),
                                       ('Last event', 'wwn.p119.what-kind-of-event-last-happened-there'),
                                       ('People', 'wwn.p119.how-populated-is-the-feature'),
                                       ('Antagonists', 'wwn.p119.what-antagonists-are-common-there'),
                                       ('Quirk', 'wwn.p119.optional-quirk-of-the-feature')])
    return {'kind': 'feature', 'title': 'Great feature', 'lines': L, 'cite': ''}
