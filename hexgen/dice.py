"""Dice: '2d6', 'd100', '1d8+4', '3d6-1', 'd00'. One seeded Random drives everything."""
import random, re

DICE = re.compile(r'^\s*(\d*)d(\d+|00)\s*([+-]\s*\d+)?\s*$', re.I)


class Dice:
    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.randrange(1 << 30)
        self.rng = random.Random(self.seed)

    def roll(self, expr):
        """Roll an expression; plain integers pass through."""
        if isinstance(expr, int):
            return expr
        m = DICE.match(str(expr))
        if not m:
            return int(expr)
        n = int(m.group(1) or 1)
        s = 100 if m.group(2) == '00' else int(m.group(2))
        mod = int(m.group(3).replace(' ', '')) if m.group(3) else 0
        return sum(self.rng.randint(1, s) for _ in range(n)) + mod

    def chance(self, n, d):
        """'n in d' check, e.g. chance(1, 6)."""
        return self.rng.randint(1, d) <= n

    def pick(self, seq):
        return self.rng.choice(list(seq))

    def shuffle(self, seq):
        seq = list(seq); self.rng.shuffle(seq); return seq

    def between(self, lo, hi):
        return self.rng.randint(lo, hi)

    def real(self):
        return self.rng.random()


def die_range(expr):
    """Lowest and highest result of an expression."""
    m = DICE.match(str(expr))
    if not m:
        raise ValueError(expr)
    n = int(m.group(1) or 1)
    s = 100 if m.group(2) == '00' else int(m.group(2))
    mod = int(m.group(3).replace(' ', '')) if m.group(3) else 0
    return n + mod, n * s + mod
