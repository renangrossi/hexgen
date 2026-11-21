"""OSE dungeon encounters (d4/d10 grid, PDF pp. 140–141) → data/gen/ose_dungeon.yaml as d40 tables."""
import os, re, subprocess, sys, yaml
pdf = sys.argv[1]; out = sys.argv[2]
tables = {}
for p in (140, 141):
    txt = subprocess.run(['pdftotext', '-q', '-f', str(p), '-l', str(p), '-layout', pdf, '-'], capture_output=True, text=True).stdout
    levels = []
    for ln in txt.splitlines():
        if 'd4/d10' in ln:
            levels = re.findall(r'Level\s+(\d+(?:[–-]\d+|\+)?)', ln); cur = {lv: [] for lv in levels}; tables.update({lv: cur[lv] for lv in levels}); continue
        m = re.match(r'\s*(\d)/(\d)\s+(.*)$', ln)
        if m and levels:
            cells = [c.strip() for c in re.split(r'\s{2,}', m.group(3).strip()) if c.strip()]
            n = (int(m.group(1)) - 1) * 10 + int(m.group(2)) + 1
            for lv, c in zip(levels, cells):
                tables[lv].append([str(n), c])
doc = {'source': {'id': 'OSE', 'title': "Old-School Essentials — Referee's Book (2026)"},
       'tables': {f'ose.dungeon.l{lv.replace("–", "-").replace("+", "plus")}': {'title': f'Dungeon encounters, level {lv}', 'die': 'd40', 'page': 138 if i < 3 else 139, 'rows': rows}
                  for i, (lv, rows) in enumerate(tables.items())}}
yaml.safe_dump(doc, open(out, 'w'), allow_unicode=True, sort_keys=False, width=200)
print({k: len(v) for k, v in tables.items()})
