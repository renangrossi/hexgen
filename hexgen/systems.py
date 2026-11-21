"""What changes between Shadowdark and Old-School Essentials.

Everything system-specific sits here: travel rates, encounter odds, which encounter
tables a terrain rolls on, and how a creature line is presented. Generators never
name a system directly; they ask the profile.
"""
import re

# OH / Sea Voyages column names used by the shared weather & hazard tables
OH_COL = {'grassland': 'Grasslands', 'forest': 'Forest', 'hills': 'Hills, Mountains', 'mountains': 'Hills, Mountains',
          'jungle': 'Jungle', 'swamp': 'Swamp', 'desert': 'Desert', 'arctic': 'Glacier', 'sea': 'Sea / Lake',
          'lake': 'Sea / Lake'}
OH_SLUG = {'grassland': 'grasslands', 'forest': 'forest', 'hills': 'hills-and-mountains', 'mountains': 'hills-and-mountains',
           'jungle': 'jungle', 'swamp': 'swamp', 'desert': 'desert', 'arctic': 'glacier', 'sea': 'sea-lake', 'lake': 'sea-lake'}


class Shadowdark:
    key, name = 'sd', 'Shadowdark RPG (Western Reaches travel)'
    hex_miles = 6
    travel = 'Walking 4 hexes a day, mounted 6, sailing 8; difficult terrain costs 2 (WR GM Guide p.40).'
    check = 'Roll 1-in-6 twice by day and twice by night (WR); on a hit roll the terrain table below.'
    ENC = {'grassland': 'sd.enc.grassland', 'forest': 'sd.enc.forest', 'jungle': 'sd.enc.jungle',
           'swamp': 'sd.enc.swamp', 'hills': 'sd.enc.mountain', 'mountains': 'sd.enc.mountain',
           'desert': 'sd.enc.desert', 'arctic': 'sd.enc.arctic', 'sea': 'sd.enc.ocean', 'lake': 'sd.enc.river-coast'}
    DISTRICT = {'Transient': 'sd.enc.slums', 'Common': 'sd.enc.low-district', 'Craft': 'sd.enc.artisan',
                'Mercantile': 'sd.enc.market', 'Affluent': 'sd.enc.high-district', 'Education': 'sd.enc.university',
                'Religious': 'sd.enc.temple', 'Military': 'sd.enc.castle', 'Spectacle': 'sd.enc.tavern',
                'Palace': 'sd.enc.castle'}

    def odds(self, terrain):
        return '1 in 6, ×2 day ×2 night'

    def encounter(self, R, terrain, river=False, coast=False, ruins=False):
        tid = 'sd.enc.river-coast' if (river or coast) and R.dice.chance(1, 3) else self.ENC[terrain]
        if ruins and R.dice.chance(1, 2):
            tid = 'sd.enc.ruins'
        r = R.roll(tid)
        return {'text': r['text'], 'cite': r['cite'], 'roll': r['roll']}

    def town_encounter(self, R, district):
        tid = self.DISTRICT.get(district.split()[0], 'sd.enc.low-district')
        r = R.roll(tid)
        return {'text': r['text'], 'cite': r['cite']}

    def dungeon_encounter(self, R, kind):
        tid = {'tomb': 'sd.enc.tomb', 'cave': 'sd.enc.cave', 'deep': 'sd.enc.deep-tunnels'}.get(kind, 'sd.enc.ruins')
        r = R.roll(tid)
        return {'text': r['text'], 'cite': r['cite']}


class OSE:
    key, name = 'ose', 'Old-School Essentials'
    hex_miles = 6
    travel = 'Base movement ÷ 5 = miles a day (120′ → 24 mi, 4 hexes); forest, hills, swamp ×⅔, mountains ×½; roads ×1½.'
    check = 'Roll once a day; encounter on the terrain odds below. Distance 4d6×10 yards; surprise as normal.'
    CHANCE = {'grassland': 1, 'forest': 2, 'hills': 2, 'desert': 2, 'sea': 2, 'lake': 2, 'jungle': 3, 'swamp': 3,
              'mountains': 3, 'arctic': 2}
    BY = {'grassland': 'grasslands', 'forest': 'forest', 'hills': 'mountains', 'mountains': 'mountains',
          'jungle': 'jungle', 'swamp': 'swamp', 'desert': 'desert', 'arctic': 'mountains', 'sea': 'ocean-sea',
          'lake': 'lake-river'}
    SUB = {'1': 'ose.enc.sub1', '2': 'ose.enc.sub2'}
    LETTER = {'B': 'ose.enc.B', 'C': 'ose.enc.C', 'D': 'ose.enc.D', 'F': 'ose.enc.F', 'G': 'ose.enc.G',
              'J': 'ose.enc.J', 'L': 'ose.enc.L', 'O': 'ose.enc.O', 'S': 'ose.enc.S'}

    def odds(self, terrain):
        return f'{self.CHANCE.get(terrain, 2)} in 6, once a day'

    def _resolve(self, R, by_tid):
        t = R.roll(by_tid)
        letter, _, kind = t['text'].partition('—')
        letter, kind = letter.strip(), kind.strip()
        sub = self.SUB.get(letter) or self.LETTER.get(letter)
        if not sub or sub not in R:
            return {'text': kind or t['text'], 'cite': t['cite']}
        tb = R.get(sub)
        col = next((c for c in (tb.cols or []) if c.lower().startswith(kind.lower()[:5])), None)
        if col is None and kind.lower().startswith('human') and tb.cols:
            col = next((c for c in tb.cols if c.lower().startswith('human')), tb.cols[0])
        res = R.roll(sub, col or 0)
        name = re.sub(r'\*$', '', res['text']).strip()
        return {'text': f'{name} ({kind.lower()})', 'cite': f"{t['cite']}, {res['cite']}", 'monster': name}

    def encounter(self, R, terrain, river=False, coast=False, ruins=False):
        key = self.BY[terrain]
        if (river or coast) and terrain not in ('sea', 'lake') and R.dice.chance(1, 3):
            key = 'lake-river'
        return self._resolve(R, 'ose.enc.by.' + key)

    def town_encounter(self, R, district):
        return self._resolve(R, 'ose.enc.by.city')

    def dungeon_encounter(self, R, kind):
        return {'text': 'Roll on the dungeon level table (OSE Referee’s Book, Dungeon Encounters)', 'cite': 'OSE'}


SYSTEMS = {'sd': Shadowdark(), 'ose': OSE()}
