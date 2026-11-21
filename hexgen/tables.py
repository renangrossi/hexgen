"""Table registry: load data/*.yaml, roll by id, expand inline references.

A data file:
    source: {id: WWN, title: Worlds Without Number, file: ..., offset: 8}
    tables:
      wwn.village.rationale:
        title: Rationale for the Village's Existence
        die: d12            # omit for an even pick over the rows
        page: 137           # printed page
        cols: [Who Runs It?, Significant Locals]   # optional; row = [label, *cols]
        rows:
          - ['1', 'Once a garrison outpost of a nation']
          - ['2–4', '...']

Inline references inside row text are expanded when rolled:
    {wwn.ruin.kind}         roll that table (all columns joined)
    {ss.village.env#Name}   roll that table, take one column
    {2d6}                   a number
    {red|green|blue}        pick one
"""
import os, re, glob, yaml
from .dice import Dice, die_range

REF = re.compile(r'\{([^{}]+)\}')
LABEL = re.compile(r'^\s*(\d{1,3})(?:\s*[–—-]\s*(\d{1,3}))?\+?\s*$')


def parse_label(label, size):
    """'02–03' → (2, 3); '00' → (100, 100) on a d100; '8–0' → (8, 10) on a d10."""
    m = LABEL.match(str(label))
    if not m:
        return None
    lo = int(m.group(1)); hi = int(m.group(2)) if m.group(2) else lo
    if str(m.group(1)) in ('0', '00') and size in (10, 100):
        lo = size
    if m.group(2) is not None and m.group(2) in ('0', '00') and size in (10, 100):
        hi = size
    if hi == 0:
        hi = size
    if hi < lo:  # '97–00' style already handled; anything else, trust lo
        hi = lo
    return lo, hi


class Table:
    def __init__(self, tid, d, source):
        self.id, self.source = tid, source
        self.title = d.get('title', tid)
        self.die = d.get('die')
        self.page = d.get('page')
        self.cols = d.get('cols')
        self.note = d.get('note', '')
        self.review = d.get('review')
        self.rows = [r if isinstance(r, list) else [None, r] for r in d['rows']]
        self.ranges = None
        if self.die:
            lo, hi = die_range(self.die)
            self.ranges = []
            for r in self.rows:
                rg = parse_label(r[0], hi)
                if rg is None:
                    raise ValueError(f'{tid}: bad row label {r[0]!r}')
                self.ranges.append(rg)

    def cite(self):
        s = self.source.get('id', '?')
        return f"{s} p.{self.page}" if self.page else s

    def lookup(self, n):
        for (lo, hi), r in zip(self.ranges, self.rows):
            if lo <= n <= hi:
                return r
        # clamp off-the-end results (modifiers)
        return self.rows[0] if n < self.ranges[0][0] else self.rows[-1]


class Result(dict):
    """What a roll produced: text, the raw roll, the table and per-column values."""
    def __str__(self):
        return self['text']


class Registry:
    def __init__(self, data_dir, dice=None):
        self.dice = dice or Dice()
        self.tables, self.sources, self.extras = {}, {}, {}
        for path in sorted(glob.glob(os.path.join(data_dir, '**', '*.yaml'), recursive=True)):
            doc = yaml.safe_load(open(path, encoding='utf-8')) or {}
            src = doc.get('source', {'id': os.path.basename(path)})
            self.sources[src.get('id')] = src
            for tid, t in (doc.get('tables') or {}).items():
                if tid in self.tables:
                    raise ValueError(f'duplicate table id {tid} in {path}')
                self.tables[tid] = Table(tid, t, src)
            for tid, t in (doc.get('overrides') or {}).items():
                old = self.tables.get(tid)
                self.tables[tid] = Table(tid, t, old.source if old else src)
            for k, v in (doc.get('extras') or {}).items():
                self.extras[k] = v

    def __contains__(self, tid):
        return tid in self.tables

    def get(self, tid):
        try:
            return self.tables[tid]
        except KeyError:
            raise KeyError(f'no table {tid!r}') from None

    def find(self, prefix):
        return sorted(t for t in self.tables if t.startswith(prefix))

    def roll(self, tid, col=None, mod=0, depth=0):
        t = self.get(tid)
        if t.die:
            n = self.dice.roll(t.die) + mod
            row = t.lookup(n)
        else:
            n = None
            row = self.dice.pick(t.rows)
        cells = [self.expand(c, depth + 1) if isinstance(c, str) else c for c in row[1:]]
        names = list(t.cols or [None] * len(cells))
        for i, nm in enumerate(names):
            if nm and names[:i].count(nm):
                names[i] = f'{nm} {names[:i].count(nm) + 1}'
        values = {(names[i] if i < len(names) and names[i] else f'c{i}'): v for i, v in enumerate(cells)}
        if col is not None:
            key = col if col in values else list(values)[int(col)] if str(col).isdigit() else col
            text = values.get(key, '')
        else:
            text = ' — '.join(str(c) for c in cells if c not in ('', None))
        return Result(text=text, roll=n, table=tid, cite=t.cite(), values=values)

    def text(self, tid, col=None, mod=0):
        return self.roll(tid, col, mod)['text']

    def expand(self, s, depth=0):
        if depth > 8 or '{' not in s:
            return s

        def sub(m):
            inner = m.group(1).strip()
            if '|' in inner and not inner.startswith(('ref:',)):
                return self.dice.pick(inner.split('|'))
            if re.fullmatch(r'\d*d(\d+|00)([+-]\d+)?', inner):
                return str(self.dice.roll(inner))
            tid, _, col = inner.partition('#')
            if tid in self.tables:
                return self.roll(tid, col or None, depth=depth)['text']
            return m.group(0)
        return REF.sub(sub, s)
