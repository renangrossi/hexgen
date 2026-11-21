"""List every table the generator rolls, grouped by source, with page and what it feeds.
Traces Registry.roll across many regions (both systems, all climates) and every settlement size.
Writes docs/sources.html (a fragment the guide includes)."""
import os, sys, html, collections
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from hexgen.tables import Registry
from hexgen.dice import Dice
from hexgen import campaign
from hexgen.systems import SYSTEMS
from hexgen.gen import settlement as S, site, faction, ship, npc, quest, realm

DATA = os.path.join(os.path.dirname(__file__), '..', 'data')
used = collections.defaultdict(set)
part = ['Region']
orig = Registry.roll
def roll(self, tid, *a, **k):
    used[tid].add(part[-1]); return orig(self, tid, *a, **k)
Registry.roll = roll

def wrap(mod, fn, label):
    f = getattr(mod, fn)
    def g(*a, **k):
        part.append(label)
        try: return f(*a, **k)
        finally: part.pop()
    setattr(mod, fn, g)
for mod, fn, label in [(S, 'settlement', 'Settlements'), (S, 'port', 'Ports'), (S, 'hireling', 'Hirelings'),
                       (S, 'trade_job', 'Trade jobs'), (S, 'districts', 'Districts & street encounters'),
                       (S, 'tavern', 'Taverns'), (npc, 'npc', 'NPCs'), (ship, 'ship', 'Ships'),
                       (site, 'stock', 'Hex contents'), (site, 'sea_hex', 'Sea hexes'), (site, 'ruin', 'Ruins'),
                       (site, 'lair', 'Lairs'), (site, 'wilderness_tag', 'Wilderness tags'), (site, 'landmark', 'Landmarks'),
                       (faction, 'court', 'Powers'), (faction, 'faction', 'Powers'), (faction, 'relations', 'Powers'),
                       (quest, 'quest', 'Quests'), (quest, 'adventure', 'Adventures'), (realm, 'realm', 'Realm'),
                       (realm, 'faith', 'Faiths'), (realm, 'cult', 'Faiths'), (realm, 'great_feature', 'Great features'),
                       (site, 'area', 'Dungeon areas'), (site, 'sea_trouble', 'Sea hexes'), (site, 'road_encounter', 'Roads'),
                       (site, 'unique_monster', 'Lairs'), (S, 'ss_extras', 'Settlements'), (S, 'fortress_layout', 'Settlements')]:
    wrap(mod, fn, label)
S.npc = npc.npc  # settlement imported npc directly
import hexgen.gen.settlement as SM; SM.npc = npc.npc
import hexgen.campaign as C; C.S = S; C.site = site; C.faction = faction; C.SH = ship; C.Q = quest; C.RM = realm
SM.quest = quest.quest; SM.bond = npc.bond

for seed in range(40):
    for system in ('sd', 'ose'):
        R = Registry(DATA, Dice(seed))
        campaign.build(R, 14, 10, system, ['temperate', 'cold', 'hot', 'dry'][seed % 4], ['w', 'ns', 'e', ''][seed % 4])
for size in S.SS_RANGE:
    for seed in range(15):
        R = Registry(DATA, Dice(1000 + seed))
        S.settlement(R, SYSTEMS['sd'], size, True)
# tag write-ups are read from extras, not rolled: record them by hand
for k, lab in [('community', 'Settlements'), ('court', 'Powers'), ('ruin', 'Ruins'), ('wilderness', 'Wilderness tags')]:
    used[f'wwn.tag.{k}'].add(lab)

R = Registry(DATA)
by = collections.defaultdict(list)
for tid in used:
    if tid not in R: continue
    t = R.get(tid)
    by[t.source.get('id')].append((t.page or 0, t.title, tid, sorted(used[tid])))
E = html.escape
order = ['WWN', 'SS', 'PW', 'OSS', 'SD', 'OSE', 'OH', 'SV', 'MONT', 'UVG', 'CWN', 'FIX']
o = []
total = sum(len(v) for v in by.values())
o.append(f'<p>The generator rolls <b>{total}</b> tables from <b>{len(by)}</b> sources. All {len(R.tables)} extracted tables can be rolled from the “Any table” tab; the list below is only what the generator uses.</p>')
for sid in sorted(by, key=lambda s: order.index(s) if s in order else 99):
    src = next((v for v in R.sources.values() if v.get('id') == sid), {})
    rows = sorted(by[sid])
    o.append(f'<h3>{E(sid)} — {E(src.get("title", "hand corrections"))} <small>({len(rows)} tables)</small></h3>')
    o.append('<table><tr><th>Page</th><th>Table</th><th>Feeds</th></tr>')
    for p, title, tid, parts in rows:
        o.append(f'<tr><td>{p or "—"}</td><td>{E(title)}<br><code>{E(tid)}</code></td><td>{E(", ".join(parts))}</td></tr>')
    o.append('</table>')
open(os.path.join(os.path.dirname(__file__), '..', 'docs', 'sources.html'), 'w').write('\n'.join(o))
print(total, 'tables;', {k: len(v) for k, v in by.items()})
