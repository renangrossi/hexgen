"""Write a generated region as JSON, Markdown and a self-contained HTML gazetteer
(SVG hex map + every entry). The HTML prints straight to PDF."""
import html, json, math, os, re

COLORS = {'sea': '#7fa8c9', 'lake': '#9cc0dc', 'grassland': '#cfdc9a', 'forest': '#7fae6e', 'jungle': '#4f9a5c',
          'swamp': '#8fa58a', 'hills': '#c9b483', 'mountains': '#9c8c7a', 'desert': '#ead9a0', 'arctic': '#eef2f5'}
GLYPH = {'capital': '★', 'city': '■', 'town': '●', 'village': '•', 'trading post': '◦', 'fortress': '▲'}
E = lambda s: html.escape(str(s or ''))


# ------------------------------------------------------------------ JSON
def to_data(reg):
    M = reg['map']
    hexes = []
    for h in M:
        hexes.append({'id': h.id, 'terrain': h.terrain, 'river': h.river, 'road': h.road, 'coast': h.coast,
                      'settlement': h.settlement['name'] if h.settlement else None, 'contents': h.contents})
    return {'name': reg['name'], 'seed': reg['seed'], 'system': reg['system'].key, 'climate': reg['climate'],
            'size': [reg['w'], reg['h']], 'hexes': hexes,
            'settlements': [dict(h.settlement, hex=h.id) for h in reg['settlements']],
            'powers': reg['powers'], 'relations': reg['relations'], 'hooks': reg['hooks'],
            'rumours': reg['rumours'], 'ships': reg['ships'], 'problems': reg['problems']}


def write_json(reg, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(to_data(reg), f, ensure_ascii=False, indent=1, default=str)


# ------------------------------------------------------------------ SVG map
def svg_map(reg, s=26):
    M = reg['map']
    k = math.sqrt(3)
    cx = lambda c: 1.5 * s * c + s + 4
    cy = lambda c, r: k * s * (r + 0.5 * (c & 1)) + k * s / 2 + 4
    W = 1.5 * s * (M.w - 1) + 2 * s + 8
    H = k * s * (M.h + 0.5) + 8
    out = [f'<svg class="map" viewBox="0 0 {W:.0f} {H:.0f}" xmlns="http://www.w3.org/2000/svg">']
    for h in M:
        x, y = cx(h.c), cy(h.c, h.r)
        pts = ' '.join(f'{x + s * math.cos(math.radians(60 * i)):.1f},{y + s * math.sin(math.radians(60 * i)):.1f}' for i in range(6))
        link = f'#hex-{h.id}' if (h.contents or h.settlement) else None
        poly = f'<polygon points="{pts}" fill="{COLORS[h.terrain]}" stroke="#5b5b5b" stroke-width=".6"><title>{h.id} {h.terrain}</title></polygon>'
        out.append(f'<a href="{link}">{poly}</a>' if link else poly)
        out.append(f'<text x="{x:.1f}" y="{y - s * 0.55:.1f}" class="hid">{h.id}</text>')
    for h in M:   # rivers
        if h.river and h.river_to:
            t = M.at(*h.river_to)
            out.append(f'<line x1="{cx(h.c):.1f}" y1="{cy(h.c, h.r):.1f}" x2="{cx(t.c):.1f}" y2="{cy(t.c, t.r):.1f}" class="river"/>')
    for h in M:   # roads: join road hexes to road neighbours
        if h.road:
            for n in M.nbrs(h):
                if (n.road or n.settlement) and (n.c, n.r) > (h.c, h.r):
                    out.append(f'<line x1="{cx(h.c):.1f}" y1="{cy(h.c, h.r):.1f}" x2="{cx(n.c):.1f}" y2="{cy(n.c, n.r):.1f}" class="road"/>')
    for h in M:
        x, y = cx(h.c), cy(h.c, h.r)
        if h.settlement:
            st = h.settlement
            out.append(f'<text x="{x:.1f}" y="{y + 5:.1f}" class="town">{GLYPH.get(st["size"], "•")}</text>')
            out.append(f'<text x="{x:.1f}" y="{y + s * 0.78:.1f}" class="tname">{E(st["name"])}</text>')
        elif any(c['kind'] == 'ruin' for c in h.contents):
            out.append(f'<text x="{x:.1f}" y="{y + 5:.1f}" class="mark">⌂</text>')
        elif any(c['kind'] == 'lair' for c in h.contents):
            out.append(f'<text x="{x:.1f}" y="{y + 5:.1f}" class="mark">☠</text>')
    out.append('</svg>')
    return '\n'.join(out)


# ------------------------------------------------------------------ HTML pieces
def cite(c):
    return f' <span class="cite">{E(c)}</span>' if c else ''


def lines_html(lines):
    rows = []
    for l in lines:
        if not l or not l.get('text'):
            continue
        lab = f'<b>{E(l["label"])}.</b> ' if l.get('label') else ''
        rows.append(f'<li>{lab}{E(l["text"])}{cite(l.get("cite"))}</li>')
    return '<ul class="lines">' + ''.join(rows) + '</ul>'


def npc_html(n):
    return f'<div class="npc"><h5>{E(n["name"])} <i>— {E(n["role"])}</i></h5>{lines_html(n["lines"])}</div>'


def ship_html(sh):
    st = sh.get('stats')
    stats = (' · ' + ', '.join(f'{k} {v}' for k, v in st.items() if k != 'Boat')) if st else ''
    head = f'{E(sh["name"])} <i>— {E(sh["type"])}, {E(sh["purpose"].lower())}, {E(sh["attitude"].lower())}; crew of {E(sh["crew"].lower())}</i>'
    return f'<div class="ship"><h5>{head}<span class="cite">OSS p.3{E(stats)}</span></h5>{lines_html(sh["lines"])}</div>'


def settlement_html(h):
    s = h.settlement
    o = [f'<section class="settlement" id="hex-{h.id}"><h3>{E(s["name"])} <small>{E(s["size"])} · hex {h.id} · {E(s["terrain"])}{" · port" if s.get("port") else ""}</small></h3>']
    o.append('<h4>At a glance</h4>' + lines_html(s['wwn'] + s['pw']))
    if s.get('tags'):
        o.append('<h4>Tags</h4>')
        for t in s['tags']:
            o.append(f'<div class="tag"><b>{E(t["tag"])}.</b> {E(t["desc"])}{cite(t["cite"])}'
                     f'<ul class="lines"><li><b>Enemy.</b> {E(t["enemy"])}</li><li><b>Friend.</b> {E(t["friend"])}</li>'
                     f'<li><b>Complication.</b> {E(t["complication"])}</li><li><b>Thing.</b> {E(t["thing"])}</li>'
                     f'<li><b>Place.</b> {E(t["place"])}</li></ul></div>')
    o.append('<h4>The place</h4>' + lines_html(s['ss']))
    o.append(f'<h4>Districts <small>{E(s["oh_type"])}</small></h4><ul class="lines">')
    for d in s['districts']:
        o.append(f'<li><b>{E(d["name"])}.</b> {E(", ".join(d["stands"]))}. <i>On the street:</i> {E(d["encounter"]["text"])}{cite(d["encounter"]["cite"])}</li>')
    o.append('</ul>')
    o.append(f'<p><b>Shops.</b> {E(", ".join(s["shops"]))}. <span class="cite">OH</span></p>')
    t = s['tavern']
    o.append(f'<p><b>Tavern: {E(t["name"])}</b> ({E(t["class"])}) — known for {E(t["known_for"].lower())}. '
             f'On the menu: {E(t["menu"])}. House drink: {E(t["drink"])}.{cite(t["cite"])}</p>')
    if s.get('temple'):
        o.append('<h4>Temple</h4>' + lines_html(s['temple']))
    o.append('<h4>Now</h4>' + lines_html([s['event']] + s['rumours']))
    o.append('<h4>People</h4>' + ''.join(npc_html(n) for n in s['npcs']))
    if s.get('hirelings'):
        o.append('<h4>For hire</h4>' + ''.join(npc_html(dict(h, role='hireling')) for h in s['hirelings']))
    if s.get('jobs'):
        o.append('<h4>Work going</h4>' + lines_html(s['jobs']))
    if s.get('quests'):
        o.append('<h4>Quests</h4>' + ''.join(f'<div class="npc"><h5>{E(q["title"])}</h5>{lines_html(q["lines"])}</div>' for q in s['quests']))
    if s.get('extra'):
        o.append('<h4>More of the place</h4>' + lines_html(s['extra']))
    if s.get('layout'):
        o.append('<h4>Fortress layout</h4>' + lines_html(s['layout']))
    if s.get('port'):
        p = s['port']
        o.append(f'<h4>Port — {E(p["kind"])}</h4><p>{E(p["has"])}{cite(p["cite"])}</p>'
                 f'<p><b>Who rules the docks.</b> {E(p["rules"])}. <b>Trouble on the quay.</b> {E(p["trouble"])}{cite(p["rcite"])}</p>')
        ps = p['passage']
        o.append(f'<p><b>Passage.</b> {E(" · ".join(f"{k} {v}" for k, v in ps["ship"].items()))}; '
                 f'captain {E(" · ".join(f"{k} {v}" for k, v in ps["captain"].items()))}.{cite(ps["cite"])}</p>')
        o.append('<h5>At anchor</h5>' + ''.join(ship_html(x) for x in p['ships']))
    o.append('</section>')
    return '\n'.join(o)


def hex_html(h):
    feat = []
    for c in h.contents:
        areas = ''.join(f'<li><b>Area {a["n"]}.</b> ' + '; '.join(f'{E(l["label"])}: {E(l["text"])}' for l in a['lines']) + '</li>'
                        for a in c.get('areas', []))
        feat.append(f'<div class="item {E(c["kind"])}"><h5>{E(c["title"])}</h5>{lines_html(c["lines"])}'
                    + (f'<ol class="lines areas">{areas}</ol>' if areas else '') + '</div>')
    tags = [h.terrain] + (['river'] if h.river else []) + (['road'] if h.road else []) + (['coast'] if h.coast else [])
    return f'<section class="hex" id="hex-{h.id}"><h4>{h.id} <small>{E(", ".join(tags))}</small></h4>{"".join(feat)}</section>'


def play_tables(R, reg):
    """Print the tables a GM rolls at the table, for the terrains on this map."""
    M, sysp = reg['map'], reg['system']
    terrains = sorted({h.terrain for h in M})
    o = ['<h2 id="tables">Play tables</h2>', f'<p><b>Travel.</b> {E(sysp.travel)}</p>', f'<p><b>Encounters.</b> {E(sysp.check)}</p>']
    # weather (Overland Hexcrawl 2d6 by terrain)
    t = R.get('oh.daily-weather-by-terrain')
    cols = [c for c in t.cols if any(reg['weather_cols'][x] == c for x in terrains)]
    idx = [t.cols.index(c) + 1 for c in cols]
    o.append(f'<div class="keep"><h3>Daily weather <small>2d6 · 2–4 stormy, 10–12 excellent · 2 or 12: strange skies</small></h3><table><tr><th>2d6</th>'
             + ''.join(f'<th>{E(c)}</th>' for c in cols) + '</tr>')
    for r in t.rows:
        o.append(f'<tr><td>{E(r[0])}</td>' + ''.join(f'<td>{E(r[i])}</td>' for i in idx) + '</tr>')
    o.append('</table></div>')
    # encounter tables
    done = set()
    for ter in terrains:
        if sysp.key == 'sd':
            tid = sysp.ENC[ter]
        else:
            tid = 'ose.enc.by.' + sysp.BY[ter]
        if tid in done or tid not in R:
            continue
        done.add(tid)
        tb = R.get(tid)
        o.append(f'<div class="keep"><h3>{E(tb.title)} <small>{E(tb.die)} · {E(tb.cite())} · {E(sysp.odds(ter))}</small></h3><table class="enc">')
        if tid.startswith('tft.'):   # stat columns; Reactions stay in the rolled hex keys
            n = tb.cols.index('Reactions') + 1
            o.append('<tr><th>' + E(tb.die) + '</th>' + ''.join(f'<th>{E(c)}</th>' for c in tb.cols[:n - 1]) + '</tr>')
            for r in tb.rows:
                o.append('<tr>' + ''.join(f'<td>{E(x)}</td>' for x in r[:n]) + '</tr>')
        else:
            for r in tb.rows:
                o.append(f'<tr><td>{E(r[0])}</td><td>{E(" — ".join(str(x) for x in r[1:]))}</td></tr>')
        o.append('</table></div>')
    def full(tid, title=None):
        if tid not in R: return ''
        tb = R.get(tid)
        head = f'<tr><th></th>' + ''.join(f'<th>{E(c)}</th>' for c in tb.cols) + '</tr>' if tb.cols and len(tb.cols) > 1 else ''
        rows = ''.join('<tr>' + ''.join(f'<td>{E(x if x is not None else "")}</td>' for x in r) + '</tr>' for r in tb.rows)
        return f'<div class="keep"><h3>{E(title or tb.title)} <small>{E(tb.die or "")} · {E(tb.cite())}</small></h3><table class="enc">{head}{rows}</table></div>'
    extra = [full('oh.strange-skies', 'Strange skies — weather rolled 2 or 12'), full('oh.cause', 'Why the sky is strange')]
    if sysp.key == 'sd':
        extra += [full('sd.enc.cave'), full('tft.wl.underground'), full('sd.enc.deep-tunnels'), full('sd.enc.tomb'), full('sd.enc.ruins'), full('oh.rumours-wr')]
    else:
        extra += [full(t) for t in sorted(R.find('ose.dungeon.'))]
    if any(h.road for h in M):
        extra.append(full('oh.path-encounters', 'On the road'))
    if any(h.terrain == 'sea' for h in M):
        extra += [full('sea.weather', 'Weather at sea'), full('sea.wind-strength-roll-when-the-last-wind-en', 'Wind strength'),
                  full('sea.wind-direction-first-day-the-edge-it-blo', 'Wind direction'), full('sea.sea-event', 'Sea event'),
                  full('sea.denizens-4d6', 'Denizens'), full('oss.enc.low'), full('oss.enc.mid'), full('oss.enc.high'),
                  full('oss.hazard', 'Ship hazard'), full('oss.hazard.results', 'Ship hazard results'),
                  full('sea.reaction-2d6-cha', 'Reaction at sea'), full('sea.sea-treasure', 'Sea treasure')]
    extra += [full('uvg.p177.general-travel-misfortune-and-misery-a-c', 'Travel misfortune'),
              full('oh.quest-archetypes', 'Quest archetypes'), full('oh.patron', 'Patron'), full('oh.reward', 'Reward'),
              full('oh.acts-of-devotion-the-outcome', 'Downtime: devotion'), full('oh.combat-training-the-outcome', 'Downtime: training'),
              full('oh.magical-study-the-outcome', 'Downtime: study')]
    o.append('<h2>More tables for play</h2>' + ''.join(extra))
    if sysp.key == 'ose':
        for tid in sorted(t for t in R.tables if t.startswith('ose.enc.') and not t.startswith('ose.enc.by.')):
            tb = R.get(tid)
            o.append(f'<div class="keep"><h3>{E(tb.title)} <small>{E(tb.die)} · {E(tb.cite())}</small></h3><table class="enc"><tr><th></th>'
                     + ''.join(f'<th>{E(c)}</th>' for c in tb.cols) + '</tr>')
            for r in tb.rows:
                o.append('<tr>' + ''.join(f'<td>{E(x)}</td>' for x in r) + '</tr>')
            o.append('</table></div>')
    return '\n'.join(o)


CSS = """
:root{--ink:#222;--muted:#6b6b6b;--rule:#d8d2c4;--paper:#fffdf8;--accent:#7a3b1d}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:14px/1.45 Georgia,'Iowan Old Style',serif}
main{max-width:980px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:30px;margin:.2em 0 0;color:var(--accent)} h2{font-size:22px;border-bottom:2px solid var(--accent);margin-top:2em;padding-bottom:2px}
h3{font-size:18px;margin:1.4em 0 .3em} h4{font-size:15px;margin:1em 0 .2em;color:var(--accent)} h5{font-size:14px;margin:.6em 0 .1em}
small,.cite{color:var(--muted);font-weight:normal;font-size:.82em} .cite{margin-left:.35em;font-style:italic}
ul.lines{margin:.2em 0 .5em;padding-left:1.1em} ul.lines li{margin:.1em 0}
.map{width:100%;height:auto;background:#e9eef2;border:1px solid var(--rule);margin:12px 0}
.map .hid{font:6px sans-serif;fill:#333;text-anchor:middle;opacity:.7}
.map .town{font:15px sans-serif;text-anchor:middle;fill:#3b1e10} .map .mark{font:12px sans-serif;text-anchor:middle;fill:#3b1e10}
.map .tname{font:bold 6.5px sans-serif;text-anchor:middle;fill:#1b1b1b;paint-order:stroke;stroke:#fff;stroke-width:1.6px}
.map .river{stroke:#3c79b4;stroke-width:2.2;stroke-linecap:round} .map .road{stroke:#7b4a22;stroke-width:1.4;stroke-dasharray:3 2}
.legend span{display:inline-block;margin-right:10px;font-size:12px} .legend i{display:inline-block;width:11px;height:11px;border:1px solid #777;vertical-align:-1px;margin-right:3px}
section.settlement{border-top:1px solid var(--rule);margin-top:1.4em}
section.hex{break-inside:avoid;border-top:1px dotted var(--rule);padding-top:.2em}
.item{margin-left:.4em} .npc,.ship,.tag{margin:.3em 0 .6em .4em}
table{border-collapse:collapse;width:100%;margin:.4em 0 1em;font-size:12.5px;break-inside:avoid}
td,th{border-bottom:1px solid var(--rule);padding:2px 6px;text-align:left;vertical-align:top} th{background:#f1ebdd}
table.enc td:first-child{white-space:nowrap;width:3.5em;color:var(--muted)}
.cols{columns:2 320px;column-gap:28px} .keep{break-inside:avoid} h3,h4,h5{break-after:avoid}
nav a{margin-right:12px}
@media print{body{font-size:10.5pt} main{max-width:none;padding:0} h2{break-before:page} a{color:inherit;text-decoration:none}}
"""


def write_html(R, reg, path, tables=True):
    M = reg['map']
    sysp = reg['system']
    o = [f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
         f'<title>{E(reg["name"])}</title><style>{CSS}</style></head><body><main>']
    o.append(f'<h1>{E(reg["name"])}</h1><p><small>{E(sysp.name)} · {E(reg["climate"])} · {reg["w"]}×{reg["h"]} hexes of {sysp.hex_miles} miles · seed {reg["seed"]}</small></p>')
    o.append('<nav><a href="#region">Region</a><a href="#realm">Realm</a><a href="#adventures">Adventures</a><a href="#powers">Powers</a><a href="#settlements">Settlements</a>'
             '<a href="#hexes">Hex key</a><a href="#sea">At sea</a><a href="#tables">Play tables</a></nav>')
    o.append(svg_map(reg))
    o.append('<p class="legend">' + ''.join(f'<span><i style="background:{c}"></i>{t}</span>' for t, c in COLORS.items() if any(h.terrain == t for h in M))
             + '<span>★ capital ■ city ● town • village ◦ trading post ▲ fortress ⌂ ruin ☠ lair</span></p>')
    o.append('<h2 id="region">The region</h2>' + lines_html(reg['problems']))
    o.append('<h3>Hooks</h3>' + lines_html(reg['hooks']))
    o.append('<h3>Rumours <small>d10</small></h3><ol>' + ''.join(f'<li>{E(r["text"])}{cite(r["cite"])}</li>' for r in reg['rumours'] if r) + '</ol>')
    o.append('<h2 id="realm">The realm</h2>')
    for k, v in reg['realm'].items():
        o.append(f'<h3>{E(k)}</h3>' + lines_html(v))
    o.append('<h3>Faiths</h3>' + ''.join(f'<div class="npc"><h5>{E(f["title"])}</h5>{lines_html(f["lines"])}</div>' for f in reg['faiths']))
    o.append('<h2 id="adventures">Adventures</h2>' + ''.join(f'<div class="npc"><h5>Adventure {i}</h5>{lines_html(a["lines"])}</div>' for i, a in enumerate(reg['adventures'], 1)))
    o.append('<h3>Family lore for the PCs</h3>' + lines_html(reg['family']))
    o.append('<h2 id="powers">Powers</h2>')
    for p in reg['powers']:
        o.append(f'<h3>{E(p["name"])} <small>{E(p["kind"])}</small></h3>{lines_html(p["lines"])}')
    o.append('<h3>How they stand</h3><ul class="lines">' + ''.join(
        f'<li><b>{E(r["a"])} ↔ {E(r["b"])}:</b> {E(r["state"])} — {E(r["why"])}{cite(r["cite"])}</li>' for r in reg['relations']) + '</ul>')
    o.append('<h2 id="settlements">Settlements</h2>')
    for h in reg['settlements']:
        o.append(settlement_html(h))
    o.append('<h2 id="hexes">Hex key</h2><div class="cols">')
    for h in sorted(M, key=lambda x: x.id):
        if h.contents and h.terrain != 'sea':
            o.append(hex_html(h))
    o.append('</div><h2 id="sea">At sea</h2><div class="cols">')
    for h in sorted(M, key=lambda x: x.id):
        if h.contents and h.terrain == 'sea':
            o.append(hex_html(h))
    o.append('</div>')
    if reg['ships']:
        o.append('<h3>Ships abroad</h3>' + ''.join(ship_html(s) for s in reg['ships']))
    if tables:
        o.append(play_tables(R, reg))
    o.append('<h2>Sources</h2><ul class="lines">' + ''.join(
        f'<li><b>{E(k)}</b> — {E(v.get("title", ""))}</li>' for k, v in sorted(R.sources.items()) if k not in ('FIX',)) + '</ul>')
    o.append('</main></body></html>')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(o))


# ------------------------------------------------------------------ Markdown
def md_lines(lines):
    return '\n'.join(f"- **{l['label']}.** {l['text']}" + (f" _({l['cite']})_" if l.get('cite') else '')
                     if l.get('label') else f"- {l['text']}" for l in lines if l and l.get('text'))


def write_md(reg, path):
    M = reg['map']
    o = [f"# {reg['name']}", f"_{reg['system'].name} · {reg['climate']} · seed {reg['seed']}_", '',
         '## The region', md_lines(reg['problems']), '', '### Hooks', md_lines(reg['hooks']), '',
         '### Rumours (d10)'] + [f"{i}. {r['text']}" for i, r in enumerate(reg['rumours'], 1) if r] + ['', '## The realm']
    for k, v in reg['realm'].items():
        o += [f'### {k}', md_lines(v), '']
    for f in reg['faiths']:
        o += [f"### {f['title']}", md_lines(f['lines']), '']
    o.append('## Adventures')
    for i, a in enumerate(reg['adventures'], 1):
        o += [f'### Adventure {i}', md_lines(a['lines']), '']
    o += ['### Family lore', md_lines(reg['family']), '', '## Powers']
    for p in reg['powers']:
        o += [f"### {p['name']} ({p['kind']})", md_lines(p['lines']), '']
    o += ['### How they stand'] + [f"- **{r['a']} ↔ {r['b']}:** {r['state']} — {r['why']}" for r in reg['relations']] + ['', '## Settlements']
    for h in reg['settlements']:
        s = h.settlement
        o += [f"### {s['name']} — {s['size']}, hex {h.id}", md_lines(s['wwn'] + s['pw'])]
        for t in s['tags']:
            o.append(f"- **Tag: {t['tag']}.** {t['desc']} Enemy: {t['enemy']}. Friend: {t['friend']}. "
                     f"Complication: {t['complication']}. Thing: {t['thing']}. Place: {t['place']}.")
        o += [md_lines(s['ss']), '', f"**Districts ({s['oh_type']})**"]
        o += [f"- {d['name']}: {', '.join(d['stands'])}. On the street: {d['encounter']['text']}" for d in s['districts']]
        t = s['tavern']
        o += [f"\n**Shops:** {', '.join(s['shops'])}", f"**Tavern:** {t['name']} ({t['class']}), known for {t['known_for'].lower()}; {t['menu']}; {t['drink']}",
              md_lines([s['event']] + s['rumours']), '', '**People**']
        for n in s['npcs']:
            o += [f"- **{n['name']}** ({n['role']}): " + '; '.join(l['text'] for l in n['lines'])]
        for q in s.get('quests', []):
            o += [f"\n**Quest: {q['title']}**", md_lines(q['lines'])]
        if s.get('extra'):
            o += ['', md_lines(s['extra'])]
        if s.get('port'):
            p = s['port']
            o += [f"\n**Port — {p['kind']}.** {p['has']} Docks ruled by {p['rules'].lower()}; {p['trouble']}"]
            o += [f"- {x['name']}: {x['type']}, {x['purpose'].lower()}, {x['attitude'].lower()}; " + '; '.join(l['text'] for l in x['lines']) for x in p['ships']]
        o.append('')
    o.append('## Hex key')
    for h in sorted(M, key=lambda x: x.id):
        if not h.contents:
            continue
        o.append(f"### {h.id} ({h.terrain}{', river' if h.river else ''}{', road' if h.road else ''})")
        for c in h.contents:
            o += [f"**{c['title']}**", md_lines(c['lines'])]
            o += [f"{a['n']}. " + '; '.join(f"{l['label']}: {l['text']}" for l in a['lines']) for a in c.get('areas', [])]
        o.append('')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(o))
