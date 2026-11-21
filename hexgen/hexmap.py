"""Hex grid, terrain, rivers, roads.

Flat-topped hexes in odd-q offset columns; (col, row) with col 0 at the west edge.
Hex ids are printed CCRR (0101 = top-left), the usual hexcrawl convention.

Terrain comes from two smoothed noise fields (height, wetness) plus a climate:
    sea · lake · swamp · grassland · forest · jungle · hills · mountains · desert · arctic
"""
import heapq, math

TERRAINS = ['sea', 'lake', 'grassland', 'forest', 'jungle', 'swamp', 'hills', 'mountains', 'desert', 'arctic']
MOVE = {'grassland': 1, 'forest': 2, 'jungle': 2, 'swamp': 2, 'hills': 2, 'mountains': 3, 'desert': 2,
        'arctic': 2, 'sea': 99, 'lake': 99}
CLIMATES = ('temperate', 'cold', 'hot', 'dry')


def hid(c, r):
    return f'{c + 1:02d}{r + 1:02d}'


def neighbours(c, r, w, h):
    odd = c & 1
    ds = [(0, -1), (0, 1), (-1, -1 + odd), (-1, odd), (1, -1 + odd), (1, odd)]
    for dc, dr in ds:
        cc, rr = c + dc, r + dr
        if 0 <= cc < w and 0 <= rr < h:
            yield cc, rr


def to_cube(c, r):
    x = c; z = r - (c - (c & 1)) // 2
    return x, -x - z, z


def distance(a, b):
    ax, ay, az = to_cube(*a); bx, by, bz = to_cube(*b)
    return max(abs(ax - bx), abs(ay - by), abs(az - bz))


class Hex:
    def __init__(self, c, r):
        self.c, self.r, self.id = c, r, hid(c, r)
        self.terrain = None
        self.height = 0.0
        self.wet = 0.0
        self.river = False        # a river runs through
        self.river_to = None      # (c, r) it flows into
        self.road = False
        self.coast = False        # land touching sea
        self.settlement = None    # Settlement dict
        self.contents = []        # list of dicts: kind, title, text, cites
        self.region = None

    @property
    def water(self):
        return self.terrain in ('sea', 'lake')


class HexMap:
    def __init__(self, w, h, dice, climate='temperate', sea_edges='w'):
        self.w, self.h, self.dice, self.climate = w, h, dice, climate
        self.hexes = {(c, r): Hex(c, r) for c in range(w) for r in range(h)}
        self.sea_edges = sea_edges or ''
        self._terrain()
        self._rivers()

    def __iter__(self):
        return iter(self.hexes.values())

    def at(self, c, r):
        return self.hexes.get((c, r))

    def nbrs(self, hx):
        return [self.hexes[p] for p in neighbours(hx.c, hx.r, self.w, self.h)]

    # ------------------------------------------------------------------ noise
    def _field(self, scale, octaves=3):
        """Value noise on a coarse lattice, bilinear, summed over octaves → 0..1."""
        total = {k: 0.0 for k in self.hexes}
        amp, norm = 1.0, 0.0
        for o in range(octaves):
            step = max(1.5, scale / (2 ** o))
            gw, gh = int(self.w / step) + 3, int(self.h / step) + 3
            grid = [[self.dice.real() for _ in range(gh)] for _ in range(gw)]
            for (c, r) in self.hexes:
                x, y = c / step, (r + 0.5 * (c & 1)) / step
                i, j = int(x), int(y); fx, fy = x - i, y - j
                fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
                a = grid[i][j] * (1 - fx) + grid[i + 1][j] * fx
                b = grid[i][j + 1] * (1 - fx) + grid[i + 1][j + 1] * fx
                total[(c, r)] += amp * (a * (1 - fy) + b * fy)
            norm += amp; amp *= 0.5
        lo, hi = min(total.values()), max(total.values())
        return {k: (v - lo) / (hi - lo or 1) for k, v in total.items()}

    def _terrain(self):
        H = self._field(max(self.w, self.h) / 2.5)
        Wt = self._field(max(self.w, self.h) / 3)
        for k, hx in self.hexes.items():
            c, r = k
            # push the chosen edges down into sea
            edge = 1.0
            for e in self.sea_edges:
                d = {'w': c, 'e': self.w - 1 - c, 'n': r, 's': self.h - 1 - r}[e]
                span = {'w': self.w, 'e': self.w, 'n': self.h, 's': self.h}[e]
                edge = min(edge, min(1.0, d / max(2.0, span * 0.22)))
            hx.height = H[k] * (0.35 + 0.65 * edge)
            hx.wet = Wt[k]
        cl = self.climate
        for hx in self:
            h, wet = hx.height, hx.wet
            if h < 0.22 and self.sea_edges:
                t = 'sea'
            elif h > 0.84:
                t = 'mountains'
            elif h > 0.68:
                t = 'hills'
            elif wet > 0.78 and h < 0.40:
                t = 'swamp'
            elif wet > 0.52:
                t = 'jungle' if cl == 'hot' else 'forest'
            elif wet < 0.18:
                t = 'desert' if cl in ('hot', 'dry') else 'grassland'
            else:
                t = 'grassland'
            if cl == 'cold' and t in ('grassland', 'swamp') and h > 0.45:
                t = 'arctic'
            if cl == 'dry' and t in ('grassland',) and wet < 0.35:
                t = 'desert'
            hx.terrain = t
        # sea must reach a sea edge; cut-off low ground becomes lake (small) or marsh
        edge_hex = lambda h: (('w' in self.sea_edges and h.c == 0) or ('e' in self.sea_edges and h.c == self.w - 1)
                              or ('n' in self.sea_edges and h.r == 0) or ('s' in self.sea_edges and h.r == self.h - 1))
        seen, stack = set(), [h for h in self if h.terrain == 'sea' and edge_hex(h)]
        while stack:
            h = stack.pop()
            if h.id in seen: continue
            seen.add(h.id)
            stack += [n for n in self.nbrs(h) if n.terrain == 'sea' and n.id not in seen]
        for h in self:
            if h.terrain == 'sea' and h.id not in seen:
                h.terrain = 'lake' if h.wet > 0.45 else ('swamp' if h.wet > 0.3 else 'grassland')
        # a lake or two in low, wet basins
        basins = sorted((hx for hx in self if hx.terrain in ('grassland', 'forest', 'swamp', 'jungle')
                         and all(n.height >= hx.height for n in self.nbrs(hx))), key=lambda x: x.wet, reverse=True)
        for hx in basins[:max(1, (self.w * self.h) // 160)]:
            hx.terrain = 'lake'
        for hx in self:
            hx.coast = not hx.water and any(n.terrain == 'sea' for n in self.nbrs(hx))

    # ------------------------------------------------------------------ rivers
    def _rivers(self):
        springs = [hx for hx in self if hx.terrain in ('mountains', 'hills') and hx.wet > 0.35]
        self.dice.rng.shuffle(springs)
        n = max(1, (self.w * self.h) // 90)
        made = 0
        for s in springs:
            if made >= n:
                break
            path, cur, seen = [s], s, {s.id}
            while True:
                nxt = min((x for x in self.nbrs(cur) if x.id not in seen), key=lambda x: x.height, default=None)
                if nxt is None:
                    path = []; break
                path.append(nxt); seen.add(nxt.id)
                if nxt.water or nxt.river:
                    break
                cur = nxt
                if len(path) > self.w + self.h:
                    path = []; break
            if len(path) >= 4:
                for a, b in zip(path, path[1:]):
                    if not a.water:
                        a.river = True; a.river_to = (b.c, b.r)
                made += 1

    # ------------------------------------------------------------------ roads
    def road(self, a, b):
        """Cheapest land path between two hexes; marks it as road. Rivers are fords (+1)."""
        def cost(h):
            return 1 if h.road else MOVE[h.terrain] + (1 if h.river else 0)
        start, goal = (a.c, a.r), (b.c, b.r)
        frontier = [(0, start)]; came = {start: None}; g = {start: 0}
        while frontier:
            _, cur = heapq.heappop(frontier)
            if cur == goal:
                break
            for nb in neighbours(*cur, self.w, self.h):
                h = self.hexes[nb]
                if h.water and nb != goal:
                    continue
                ng = g[cur] + cost(h)
                if nb not in g or ng < g[nb]:
                    g[nb] = ng; came[nb] = cur
                    heapq.heappush(frontier, (ng + distance(nb, goal), nb))
        if goal not in came:
            return []
        path, cur = [], goal
        while cur:
            path.append(self.hexes[cur]); cur = came[cur]
        for h in path:
            if not h.water:
                h.road = True
        return path[::-1]
