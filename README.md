# hexgen

Rolls a whole hexcrawl region from your table library: map, settlements and ports, roads
and rivers, every hex keyed, ruins, lairs, powers and their feuds, ships, rumours, hooks.
It writes a printable gazetteer (HTML → PDF), Markdown and JSON. Every line cites its book
and page. It supports **Shadowdark** (Western Reaches travel) and **Old-School Essentials**.

```sh
python3 -m hexgen region                        # Shadowdark, 16×12, sea to the west
python3 -m hexgen --seed 7 region --system ose --climate cold --sea n --size 20x14 --pdf
python3 -m hexgen settlement --kind city --coastal
python3 -m hexgen ship --count 3
python3 -m hexgen roll pw.discovery --times 5
python3 -m hexgen list wwn.p183                 # browse table ids
make test                                        # every table rolls, both systems render
```

Output goes to `out/<region>-<system>-<seed>.{html,md,json,pdf}`. The same seed gives the
same region.

## What feeds what

| Part | Richest source first |
|---|---|
| Map, terrain, rivers, roads | own procedure (noise + downhill rivers + cheapest-path roads); WR movement costs |
| Region name | Perilous Wilds region names, terrain word matched to the map |
| Settlement profile | **Spectacular Settlements**: the full chapter for that size (trading post, village, town, city, capital, fortress) |
| Why it exists, who runs it, problem, who needs the PCs, what it offers | **WWN** pp. 145–147 |
| Community tags with enemy/friend/complication/thing/place | **WWN** pp. 148–162 (200 tags extracted) |
| Feature and problem | Perilous Wilds steadings, pp. 50–51 |
| Districts, shops, tavern, menu, drinks, events, rumours | Overland Hexcrawl (GC, SG, core inside) |
| Street encounters per district | **SD core** settlement d100s pp. 142–185 · OSE City table |
| Temple | WWN p. 139 · NPCs: WWN pp. 380–387 · hirelings: WWN Montfroid p. 29 |
| Trade jobs | UVG p. 180 |
| Port, harbour master, quay trouble, passage, captains | Sea Voyages · Overland Hexcrawl |
| Ships | **Of Ships & the Sea** screen (type, purpose, attitude, crew, name, disposition, emergency) + OH vessel/crew/story + SV boat stats |
| Hex stocking | OH content roll → OH hazards / lore / situations / creatures; OH points of interest by terrain; OH landmarks (SG Landmarks); PW discovery |
| Wilderness tags | WWN pp. 202–216 |
| Ruins | WWN ruin chapter p. 183 + ruin tags + PW dungeon + OH dungeon type, size, quirk + WWN hazards, enigmas, treasure spots |
| Lairs | system encounter + WWN lair complications p. 229 + PW lair + OH treasure |
| Creatures | **SD**: core terrain d100s (pp. 142–185) · **OSE**: Referee's Book d8 terrain → sub-tables (pp. 142–147) |
| Sea hexes | Sea Voyages uncharted hex, finds, islands; OH sea points of interest |
| Powers | WWN courts pp. 163–167 + court tags; OH faction generator; OH domain relations |
| Weather (play tables) | OH 2d6 by terrain (WR odds) |

## How the data is built

```
PDFs ──tools/extract_pdf.py──▶ raw/*.json ──tools/curate.py──▶ data/gen/*.yaml ─┐
OH, Sea Voyages build scripts ──harvest_*.py──▶ raw/                             ├─▶ Registry
hand transcriptions (Perilous Wilds grids, Of Ships screen, fixes) ─ data/hand/ ─┘
```

- `make data` rebuilds everything (`extract` → `curate` → `check`). `sources.yaml` lists each
  book, its path under `RPG_ROOT`, page offset and page columns.
- `extract_pdf.py` reads word coordinates, splits page columns and side-by-side tables,
  finds sub-columns from the gutters, and joins wrapped rows. It runs on any PDF with die
  tables; add a book to `sources.yaml` and re-run.
- Table ids are `<book>.p<printed page>.<title slug>`; `python3 -m hexgen list` shows them.
  Tables with gaps in their die ranges are kept but marked `review`, and generators skip them.
- `data/hand/overrides.yaml` replaces a mangled table without touching the extractor.

## Data file format

```yaml
source: {id: PW, title: The Perilous Wilds}
tables:
  pw.discovery:
    die: 1d12
    page: 48
    rows:
      - ['1', 'Unnatural feature: {pw.discovery.unnatural}']   # {id} rolls another table
      - ['2–4', 'Natural feature: {pw.discovery.natural}']     # {2d6} rolls dice, {a|b} picks
```

## Not wired in (yet)

Cities Without Number (cyberpunk; NPC tables are curated but unused), most of UVG (setting-specific
misfortunes), Ruinous Explorations (a solo oracle, not tables), and the Philip Reed decks,
Raging Swan and Ashworth books in `Solo Gaming Assets/02 Random Tables` — add them to
`sources.yaml` to pull their tables in.

The extracted text comes from books you own. Keep this repository private.
