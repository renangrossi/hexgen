import re
"""Build a whole region: map, settlements and ports, roads, hex contents, ruins, lairs,
powers and their relations, a rumour table and a ship roster. Returns plain data that
the renderers turn into Markdown, HTML and JSON."""
from .hexmap import HexMap, distance
from .systems import SYSTEMS, OH_COL
from .gen.common import line, roll
from .gen import settlement as S, site, faction, ship as SH, quest as Q, realm as RM

SIZES = ['capital', 'city', 'town', 'town', 'village', 'village', 'village', 'village', 'village', 'trading post',
         'fortress']


def place_settlements(R, M, n):
    good = [h for h in M if h.terrain in ('grassland', 'forest', 'hills', 'jungle', 'desert', 'arctic', 'swamp')]
    score = lambda h: (0.6 if h.coast else 0) + (1 if h.river else 0) + (1 if h.terrain == 'grassland' else 0) + M.dice.real()
    good.sort(key=score, reverse=True)
    chosen = []
    for h in good:
        if len(chosen) >= n:
            break
        if all(distance((h.c, h.r), (o.c, o.r)) >= 3 for o in chosen):
            chosen.append(h)
    return chosen


TERRAIN_WORDS = {'sea': ['Bay', 'Sea', 'Sound'], 'lake': ['Lake'], 'grassland': ['Downs', 'Plains', 'Meadows', 'Steppe', 'Reach', 'March', 'Heath', 'Flats'],
                 'forest': ['Forest', 'Woods', 'Groves', 'Thicket'], 'jungle': ['Jungle', 'Thicket'],
                 'swamp': ['Marsh', 'Fen', 'Bog', 'Morass', 'Slough', 'Quagmire'], 'hills': ['Hills', 'Downs', 'Fells', 'Heights', 'Upland', 'Foothills'],
                 'mountains': ['Mountains', 'Peaks', 'Range', 'Teeth', 'Wall', 'Heights'], 'desert': ['Desert', 'Dunes', 'Sands', 'Waste', 'Wasteland', 'Expanse'],
                 'arctic': ['Waste', 'Expanse', 'Fells', 'Wall']}


def region_name(R, M):
    from collections import Counter
    land = Counter(h.terrain for h in M if not h.water)
    top = land.most_common(1)[0][0] if land else 'sea'
    name = R.text('pw.region.template')
    words = set(R.get('pw.name.terrain').rows and [r[1] for r in R.get('pw.name.terrain').rows])
    for w in sorted(words, key=len, reverse=True):
        if re.search(rf'\b{w}\b', name):
            return re.sub(rf'\b{w}\b', R.dice.pick(TERRAIN_WORDS[top]), name, count=1)
    return name


def build(R, w=16, h=12, system='sd', climate='temperate', sea='w', settlements=None, title=None):
    sysp = SYSTEMS[system]
    M = HexMap(w, h, R.dice, climate, sea)
    n = settlements or max(3, (w * h) // 22)
    sites = place_settlements(R, M, n)
    # the best-placed settlement is the largest; a coastal one becomes the port city
    sizes = ['city'] + [S for S in SIZES[2:]] * 3
    if n >= 8:
        sizes = ['capital', 'city'] + sizes[1:]
    for i, hx in enumerate(sites):
        size = sizes[i] if i < len(sizes) else 'village'
        coastal = hx.coast or (size in ('town', 'city', 'capital') and any(nb.terrain == 'lake' for nb in M.nbrs(hx)))
        hx.settlement = S.settlement(R, sysp, size, coastal, hx.terrain)
    # roads: link each settlement to its nearest larger neighbour, then the two largest
    ranked = sorted(sites, key=lambda x: SIZES.index(x.settlement['size']) if x.settlement['size'] in SIZES else 99)
    for i, a in enumerate(ranked[1:], 1):
        b = min(ranked[:i], key=lambda o: distance((a.c, a.r), (o.c, o.r)))
        if a.settlement['size'] not in ('trading post',) or R.dice.chance(1, 2):
            M.road(a, b)
    # contents
    land = [x for x in M if not x.water and not x.settlement]
    for hx in M:
        if hx.settlement:
            continue
        hx.contents = (site.sea_hex(R, sysp, hx, any(not n.water for n in M.nbrs(hx))) if hx.terrain == 'sea'
                       else site.stock(R, sysp, hx))
    for hx in R.dice.shuffle(land)[:max(2, len(land) // 18)]:
        hx.contents.insert(0, site.ruin(R, sysp))
    for hx in R.dice.shuffle(land)[:max(2, len(land) // 16)]:
        hx.contents.insert(0, site.lair(R, sysp, hx))
    for hx in R.dice.shuffle(land)[:max(2, len(land) // 14)]:
        t = site.wilderness_tag(R)
        if t: hx.contents.append(t)
    for hx in R.dice.shuffle(land)[:max(1, len(land) // 60)]:
        hx.contents.insert(0, RM.great_feature(R))
    for hx in [x for x in M if x.road and not x.settlement]:
        if R.dice.chance(1, 3):
            hx.contents.append(site.road_encounter(R))
    # powers
    powers = [faction.court(R) for _ in range(2)] + [faction.faction(R) for _ in range(2)]
    rel = faction.relations(R, powers)
    # region-level tables for play
    name = title or region_name(R, M)
    region = {
        'name': name, 'seed': R.dice.seed, 'system': sysp, 'climate': climate, 'w': w, 'h': h,
        'map': M, 'settlements': sites, 'powers': powers, 'relations': rel,
        'hooks': [roll(R, 'Hook', 'wwn.p372.ways-of-introducing-an-adventure-hook') for _ in range(3)],
        'rumours': [roll(R, 'Rumour', 'oh.rumours') for _ in range(10)],
        'ships': [SH.ship(R) for _ in range(6)] if any(x.terrain == 'sea' for x in M) else [],
        'problems': [roll(R, 'National problem', 'wwn.p121.current-national-problems'),
                     roll(R, 'Good news', 'wwn.p121.good-things-happening-right-now'),
                     roll(R, 'Thematic element', 'wwn.p122.thematic-element')],
        'weather_cols': OH_COL,
        'realm': RM.realm(R), 'faiths': [RM.faith(R), RM.faith(R), RM.cult(R)],
        'adventures': [Q.adventure(R) for _ in range(3)],
        'family': [Q.family_lore(R) for _ in range(4)],
    }
    return region
