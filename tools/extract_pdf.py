"""Pull die-tables out of a PDF using word coordinates (pdftotext -bbox-layout).

A table starts at a header line whose first word is a die (d4 … d100, d00, 2d6, 1d12).
Rows are lines whose first word is a number or range (3, 61–64, 2-3, 00) sitting under
the die. Wrapped text is assigned to the nearest row number vertically, so rows whose
number is centred between two text lines come out whole.

Usage: extract_pdf.py PDF FIRST LAST OUT.json [--cols N] [--offset K]
  --cols    page columns to split (default 2)
  --offset  printed page = pdf page - offset (stored as 'page' alongside 'pdf_page')
"""
import sys, re, json, subprocess, html, argparse
from xml.etree import ElementTree as ET

DIE = re.compile(r'^(\d*)d(\d+|00)$', re.I)
NUM = re.compile(r'^(\d{1,3})(?:\s*[–—-]\s*(\d{1,3}))?\+?$')

def words(pdf, page):
    xml = subprocess.run(['pdftotext', '-q', '-f', str(page), '-l', str(page), '-bbox-layout', pdf, '-'],
                         capture_output=True, text=True).stdout
    xml = re.sub(r'<!DOCTYPE[^>]*>', '', xml).replace('xmlns="http://www.w3.org/1999/xhtml"', '')
    xml = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', xml)
    xml = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|#)', '&amp;', xml)
    try: root = ET.fromstring(xml)
    except ET.ParseError: return 612, 792, []
    pg = root.find('.//page')
    if pg is None: return 612, 792, []
    W, H = float(pg.get('width')), float(pg.get('height'))
    out = []
    for line in root.iter('line'):
        ws = [(float(w.get('xMin')), float(w.get('yMin')), float(w.get('xMax')), float(w.get('yMax')), html.unescape(w.text or ''))
              for w in line.iter('word')]
        if ws: out.append(ws)
    return W, H, out

def split_cols(lines, W, n):
    """Break each bbox line into per-column lines (a line may straddle a gutter)."""
    cols = [[] for _ in range(n)]
    for ws in lines:
        for c in range(n):
            lo, hi = W * c / n, W * (c + 1) / n
            part = [w for w in ws if lo <= (w[0] + w[2]) / 2 < hi]
            if part: cols[c].append(part)
    for c in cols:
        c.sort(key=lambda l: (round(l[0][1]), l[0][0]))
    return cols

def merge_rows(lines, tol=2.5):
    """Merge fragments that sit on the same baseline into one visual line."""
    merged = []
    for l in lines:
        if merged and abs(merged[-1][0][1] - l[0][1]) < tol:
            merged[-1] = sorted(merged[-1] + l, key=lambda w: w[0])
        else:
            merged.append(sorted(l, key=lambda w: w[0]))
    return merged

def text(ws): return ' '.join(w[4] for w in ws).strip()

def side_split(lines):
    """If any header line holds a second die after a gap, cut the column there."""
    for l in merge_rows(lines):
        if DIE.match(l[0][4]):
            for a, b in zip(l, l[1:]):
                if DIE.match(b[4]) and b[0] - a[2] > 12:
                    return b[0] - 4
    return None

def parse_column(lines, depth=0):
    cut = side_split(lines) if depth < 3 else None
    if cut:
        left = [[w for w in l if w[2] <= cut + 2] for l in lines]
        right = [[w for w in l if w[2] > cut + 2] for l in lines]
        return parse_column([l for l in left if l], depth + 1) + parse_column([l for l in right if l], depth + 1)
    lines = merge_rows(lines)
    tables, i = [], 0
    while i < len(lines):
        l = lines[i]; m = DIE.match(l[0][4])
        if not m or len(l) < 2:
            i += 1; continue
        die = l[0][4].lower().replace('d00', 'd100')
        size = int(m.group(2)) if m.group(2) != '00' else 100
        dx = l[0][0]
        title = text(l[1:])
        # numbers: left edge near die x; text: further right
        nums, texts, j = [], [], i + 1
        last_y = l[0][3]
        while j < len(lines):
            L = lines[j]; first = L[0]
            gap = first[1] - last_y
            if gap > 14: break                      # paragraph break ends the table
            if DIE.match(first[4]) and len(L) > 1: break
            isnum = NUM.match(first[4]) and first[0] < dx + 22
            if isnum:
                nums.append((first[1], first[3], first[4], L[1:]))
                if len(L) > 1: texts.append(((first[1]+first[3])/2, L[1:]))
            elif first[0] > dx + 8 or (nums and first[0] > dx - 4):
                texts.append(((first[1]+first[3])/2, L))
            else:
                break
            last_y = L[0][3]; j += 1
        if len(nums) >= 2:
            # sub-columns: header words separated by wide gaps
            hdr = l[1:]; starts = [hdr[0][0]]; titles = [[hdr[0]]]
            for a, b in zip(hdr, hdr[1:]):
                if b[0] - a[2] > 9: starts.append(b[0]); titles.append([b])
                else: titles[-1].append(b)
            ncol = len(starts)
            bounds = []
            if ncol > 1:
                allw = [w for _, ws in texts for w in ws]
                x0 = min(w[0] for w in allw); x1 = max(w[2] for w in allw)
                cov = [0] * (int(x1 - x0) + 2)
                for w in allw:
                    for x in range(int(w[0] - x0), int(w[2] - x0) + 1): cov[x] += 1
                gaps, run = [], None
                for x, c in enumerate(cov):
                    if c == 0 and run is None: run = x
                    elif c and run is not None:
                        gaps.append((x - run, x0 + (run + x) / 2)); run = None
                gaps = sorted(g for g in gaps if g[0] >= 4)
                bounds = sorted(g[1] for g in gaps[-(ncol - 1):]) if len(gaps) >= ncol - 1 else []
                if len(bounds) != ncol - 1:
                    bounds = [st - 6 for st in starts[1:]]
            def cells(ws):
                if ncol == 1: return [text(ws)]
                out = [[] for _ in range(ncol)]
                for w in ws:
                    out[sum(1 for b in bounds if (w[0] + w[2]) / 2 > b)].append(w)
                return [text(c) for c in out]
            inline = sum(1 for n in nums if n[3]) >= len(nums) * 0.8
            rows = {k: [] for k in range(len(nums))}
            centres = [(a + b) / 2 for a, b, _, _ in nums]
            tops = [a for a, _, _, _ in nums]
            for y, ws in texts:
                if inline:
                    k = max([k for k in range(len(tops)) if tops[k] - 3 <= y] or [0])
                else:
                    k = min(range(len(centres)), key=lambda k: abs(centres[k] - y))
                rows[k].append((y, ws))
            out = []
            for k, (_, _, lab, _) in enumerate(nums):
                parts = sorted(rows[k], key=lambda t: t[0])
                cs = [''] * ncol
                for _, ws in parts:
                    for c, tx in enumerate(cells(ws)):
                        if tx: cs[c] = (cs[c] + ' ' + tx).strip()
                cs = [re.sub(r'(\w)- (\w)', r'\1\2', re.sub(r'\s+', ' ', c)) for c in cs]
                out.append([lab.replace('-', '–')] + cs)
            allx = [w for _, ws in texts for w in ws] + l
            t = {'die': die, 'size': size, 'title': title, 'rows': out,
                 '_box': (min(w[0] for w in allx), l[0][1], max(w[2] for w in allx), lines[j-1][0][3])}
            if ncol > 1: t['cols'] = [text(c) for c in titles]
            tables.append(t)
        i = max(j, i + 1)
    return tables

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf'); ap.add_argument('first', type=int); ap.add_argument('last', type=int); ap.add_argument('out')
    ap.add_argument('--cols', type=int, default=2); ap.add_argument('--offset', type=int, default=0)
    a = ap.parse_args()
    res = []
    for p in range(a.first, a.last + 1):
        W, H, lines = words(a.pdf, p)
        split = [t for c, col in enumerate(split_cols(lines, W, a.cols)) for t in parse_column(col)]
        whole = [t for t in parse_column(split_cols(lines, W, 1)[0]) if a.cols > 1
                 and t['_box'][0] < W / a.cols - 10 and t['_box'][2] > W / a.cols + 10 and 'cols' in t]
        keep = whole + [t for t in split if not any(u['_box'][1] - 3 <= t['_box'][1] <= u['_box'][3] for u in whole)]
        for t in keep:
            t.pop('_box'); t.update(pdf_page=p, page=p - a.offset); res.append(t)
    json.dump(res, open(a.out, 'w'), ensure_ascii=False, indent=1)
    print(len(res), 'tables', file=sys.stderr)

if __name__ == '__main__':
    main()
