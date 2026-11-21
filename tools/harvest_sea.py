"""Harvest the tables in Sea Voyages (sea-sd/build.py) without running the build.
Reads every table(cap, head, rows, src) call whose arguments are literals.
Usage: harvest_sea.py BUILD.py OUT.json"""
import ast, sys, json, re

src = open(sys.argv[1]).read()
out = []
for node in ast.walk(ast.parse(src)):
    if isinstance(node, ast.Call) and getattr(node.func, 'id', None) == 'table' and len(node.args) >= 3:
        try:
            cap, head, rows = (ast.literal_eval(a) for a in node.args[:3])
        except Exception:
            continue
        srcarg = ''
        if len(node.args) > 3:
            try: srcarg = ast.literal_eval(node.args[3])
            except Exception: pass
        for k in node.keywords:
            if k.arg == 'src':
                try: srcarg = ast.literal_eval(k.value)
                except Exception: pass
        clean = lambda s: re.sub(r'<[^>]+>|\*\*|__', '', str(s)).strip()
        out.append({'caption': clean(cap), 'cols': [clean(h) for h in head],
                    'rows': [[clean(c) for c in r] for r in rows], 'src': clean(srcarg), 'line': node.lineno})
json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, indent=0)
print(len(out), 'tables', file=sys.stderr)
