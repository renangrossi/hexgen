"""hexgen — roll a whole hexcrawl region from your table library.

  python3 -m hexgen region  [--system sd|ose] [--size 16x12] [--climate temperate|cold|hot|dry]
                            [--sea w|e|n|s|we|''] [--seed N] [--name "..."] [--out DIR] [--pdf] [--no-tables]
  python3 -m hexgen settlement --kind village|town|city|capital|trading-post|fortress [--coastal]
  python3 -m hexgen ship [--count N]
  python3 -m hexgen roll TABLE_ID [--times N]
  python3 -m hexgen list [PREFIX]
  python3 -m hexgen check            # every table rolls; report flagged ones
"""
import argparse, json, os, re, shutil, subprocess, sys
from .dice import Dice
from .tables import Registry
from .systems import SYSTEMS
from . import campaign, render
from .gen import settlement as S, ship as SH

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), 'data')


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def pdf(html_path, pdf_path):
    chrome = next((shutil.which(c) for c in ('chromium', 'google-chrome-stable', 'google-chrome', 'chrome') if shutil.which(c)), None)
    if not chrome:
        print('no Chrome/Chromium found; skipped PDF', file=sys.stderr); return False
    subprocess.run([chrome, '--headless', '--disable-gpu', '--no-pdf-header-footer', f'--print-to-pdf={pdf_path}',
                    'file://' + os.path.abspath(html_path)], check=True, capture_output=True)
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(prog='hexgen', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--data', default=DATA)
    ap.add_argument('--seed', type=int)
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('region'); r.add_argument('--system', default='sd', choices=SYSTEMS)
    r.add_argument('--size', default='16x12'); r.add_argument('--climate', default='temperate')
    r.add_argument('--sea', default='w'); r.add_argument('--name'); r.add_argument('--settlements', type=int)
    r.add_argument('--out', default='out'); r.add_argument('--pdf', action='store_true'); r.add_argument('--no-tables', action='store_true')
    s = sub.add_parser('settlement'); s.add_argument('--kind', default='village'); s.add_argument('--coastal', action='store_true')
    s.add_argument('--system', default='sd', choices=SYSTEMS)
    sh = sub.add_parser('ship'); sh.add_argument('--count', type=int, default=1)
    ro = sub.add_parser('roll'); ro.add_argument('table'); ro.add_argument('--times', type=int, default=1)
    ls = sub.add_parser('list'); ls.add_argument('prefix', nargs='?', default='')
    sub.add_parser('check')
    a = ap.parse_args(argv)

    R = Registry(a.data, Dice(a.seed))
    if a.cmd == 'region':
        w, h = (int(x) for x in a.size.lower().split('x'))
        reg = campaign.build(R, w, h, a.system, a.climate, a.sea, a.settlements, a.name)
        base = os.path.join(a.out, f"{slug(reg['name'])}-{a.system}-{reg['seed']}")
        os.makedirs(a.out, exist_ok=True)
        render.write_json(reg, base + '.json'); render.write_md(reg, base + '.md')
        render.write_html(R, reg, base + '.html', tables=not a.no_tables)
        print(base + '.html'); print(base + '.md'); print(base + '.json')
        if a.pdf and pdf(base + '.html', base + '.pdf'):
            print(base + '.pdf')
    elif a.cmd == 'settlement':
        st = S.settlement(R, SYSTEMS[a.system], a.kind.replace('-', ' '), a.coastal)
        print(json.dumps(st, ensure_ascii=False, indent=1, default=str))
    elif a.cmd == 'ship':
        print(json.dumps([SH.ship(R) for _ in range(a.count)], ensure_ascii=False, indent=1))
    elif a.cmd == 'roll':
        for _ in range(a.times):
            res = R.roll(a.table)
            print(f"[{res['roll']}] {res['text']}  ({res['cite']})")
    elif a.cmd == 'list':
        for t in R.find(a.prefix):
            tb = R.get(t)
            print(f"{t:60} {tb.die or '-':6} {tb.title[:50]}{'  [review: ' + tb.review + ']' if tb.review else ''}")
    elif a.cmd == 'check':
        bad = 0
        for t in sorted(R.tables):
            try:
                for _ in range(20): R.roll(t)
            except Exception as e:
                bad += 1; print('ERROR', t, e)
        flagged = [t for t in R.tables if R.tables[t].review]
        print(f'{len(R.tables)} tables roll; {bad} errors; {len(flagged)} flagged for review (python3 -m hexgen list shows why)')


if __name__ == '__main__':
    main()
