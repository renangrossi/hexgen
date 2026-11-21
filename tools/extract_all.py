"""Run every extractor named in sources.yaml into raw/. Skips files already there
unless --force. RPG_ROOT defaults to three folders above this repo.

Usage: extract_all.py [--force] [key ...]
"""
import os, sys, subprocess, yaml

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
ROOT = os.environ.get('RPG_ROOT', os.path.abspath(os.path.join(REPO, '..', '..', '..')))
RAW = os.path.join(REPO, 'raw')
os.makedirs(RAW, exist_ok=True)
args = [a for a in sys.argv[1:] if not a.startswith('--')]
force = '--force' in sys.argv
S = yaml.safe_load(open(os.path.join(REPO, 'sources.yaml')))
py = [sys.executable, '-I']


def run(cmd):
    print('+', ' '.join(os.path.basename(c) if os.sep in c else c for c in cmd), file=sys.stderr)
    subprocess.run(cmd, check=True)


for key, s in S.items():
    if args and key not in args:
        continue
    out = os.path.join(RAW, key + '.json')
    if os.path.exists(out) and not force:
        continue
    pdf = os.path.join(ROOT, s['file'])
    if key == 'oh':
        run(py + [os.path.join(HERE, 'harvest_oh.py'), os.path.join(ROOT, 'Shadowdark/My Projects/tft-sd/oh-simple'), out])
    elif key == 'sea':
        run(py + [os.path.join(HERE, 'harvest_sea.py'), os.path.join(ROOT, 'Shadowdark/My Projects/sea-sd/build.py'), out])
    else:
        assert os.path.exists(pdf), f'missing source PDF: {pdf}'
        a, b = s['pages']
        run(py + [os.path.join(HERE, 'extract_pdf.py'), pdf, str(a), str(b), out,
                  '--cols', str(s.get('cols', 2)), '--offset', str(s.get('offset', 0))])
    if key == 'wwn':
        run(py + [os.path.join(HERE, 'extract_wwn_tags.py'), pdf, out, os.path.join(RAW, 'wwn_tags.json')])
