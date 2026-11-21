"""Pack every table and extra into docs/data.json for the in-browser generator (GitHub Pages)."""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from hexgen.tables import Registry
R = Registry(os.path.join(os.path.dirname(__file__), '..', 'data'))
out = {'sources': {k: {'id': v.get('id'), 'title': v.get('title')} for k, v in R.sources.items()},
       'tables': {}, 'extras': R.extras}
for tid, t in R.tables.items():
    d = {'s': t.source.get('id'), 'r': t.rows}
    if t.die: d['d'] = t.die
    if t.page: d['p'] = t.page
    if t.cols: d['c'] = t.cols
    if t.title != tid: d['t'] = t.title
    if t.review: d['x'] = 1
    out['tables'][tid] = d
p = os.path.join(os.path.dirname(__file__), '..', 'docs', 'data.json')
json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(p, os.path.getsize(p))
