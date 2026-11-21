"""Harvest every table the Overland Hexcrawl Simplified build prints.
Patches kit.table/pairup, runs the layout, dumps JSON. Usage: harvest_oh.py OH_DIR OUT.json"""
import sys, json, os, re, html
oh, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
sys.path.insert(0, oh); os.chdir(oh)
import kit
got = []
def strip(s):
    s = re.sub(r'<[^>]+>', '', str(s)); return html.unescape(s).strip()
orig = kit.table
def table(caption, die, cols, rows, *a, **kw):
    note = kw.get('note') or (a[0] if a else ''); src = kw.get('src') or (a[1] if len(a)>1 else '')
    got.append(dict(caption=strip(caption), die=strip(die), cols=[strip(c[0] if isinstance(c,(list,tuple)) else c) for c in cols],
                    rows=[[strip(c) for c in r] for r in rows], note=strip(note or ''), src=str(src or '')))
    return orig(caption, die, cols, rows, *a, **kw)
kit.table = table
import book1, book2, book3, layout
for m in (book1, book2, book3, layout):
    if hasattr(m, 'table'): m.table = table
for fn in (book1.part1, layout.part2, layout.part3, layout.part4, layout.part5, layout.part6):
    try: fn()
    except Exception as e: print('skip', fn.__name__, e, file=sys.stderr)
# de-dup by caption+first row
seen, uniq = set(), []
for t in got:
    k = (t['caption'], json.dumps(t['rows'][:1]))
    if k not in seen: seen.add(k); uniq.append(t)
json.dump(uniq, open(out, 'w'), ensure_ascii=False, indent=0)
print(len(uniq), 'tables')
