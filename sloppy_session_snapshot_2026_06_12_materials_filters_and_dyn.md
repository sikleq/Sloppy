# Sloppy Session Snapshot — 2026-06-12

## Scope

This snapshot is for handoff into Claude Code after the current Codex session.
The project is `C:\Users\sikle\Documents\Sloppy`.

Primary focus in this segment:

- patch-page tag/group filter behavior
- Hero Dynamics melee/ranged filters
- dyn-cell visual centering
- persistence of formatting/layout rules already agreed in this session

## What changed

### 1. Patch-page combined filters were fixed

File:

- `scripts.js`

Root issue:

- Patch-page tag filters (`.filter-btn`) and category/group filters (`.cat-filter-btn`) were working independently.
- That left empty patch cards on screen after filter intersections, or visible gaps between cards.

Implemented fix:

- Added `elementVisible(el)` and `refreshPatchFilterLayout()` in `scripts.js`.
- After either tag filter or category filter changes, the page now recomputes and collapses:
  - empty `ul.changes`
  - `h4.ability-title`
  - `.ability-block`
  - `.entity-block`
  - `h4.subgroup`

Important rule:

- The entity header itself must **not** keep an `entity-block` visible.
- A patch card only stays visible if it still has:
  - visible `ul.changes > li`
  - visible `.ability-change`
  - or visible real side panels (`.components-box`, `.components-change`, `.provides-box`, `.properties-change`)

This was the second-pass correction after an earlier overbroad implementation that incorrectly treated the entity header as visible content.

### 2. Hero Dynamics got melee/ranged filters

Files:

- `build_heroes_dyn.py`
- `dyn_matrix_common.py`
- `scripts.js`

What changed:

- `heroes_dyn.html` now uses the same melee/ranged toolbar filter pattern as Hero Stats.
- `build_heroes_dyn.py` now derives hero attack type from latest raw hero data:
  - imports helpers from `build_heroes_stats.py`
  - resolves `AttackCapabilities`
  - treats `Spirit Bear` as forced `melee`
- `dyn_matrix_common.py` now supports:
  - `attack_filter=True`
  - `row_meta_by_slug=...`
  - per-row `data-attack-type`
  - toolbar buttons for Melee / Ranged
- `scripts.js` dyn-matrix row filtering now respects `attackFilter`

### 3. Dyn-cell centering was adjusted

File:

- `styles.css`

Change:

- `.heroes-dyn-table td.hd-cell` now uses `line-height: 0;`

Why:

- Without that, dyn-cell pills were sitting slightly too high vertically inside the table grid.

## Memory / rules that must persist

These were explicitly agreed and should continue to be treated as project rules:

1. `HP/sec` and `MP/sec` in both Hero Stats and Neutral Stats:
   - no leading `+`
   - non-zero values shown with exactly two decimals
   - exact zero shown as `0`
   - exact zero tinted as a muted variant of the column color
   - numeric sorting stays separate from display formatting

2. Patch-page filtering:
   - tag and category/group filters must recompute layout together
   - entity headers do not count as visible content
   - empty cards must collapse fully

3. Hero Dynamics:
   - supports melee/ranged filtering like Hero Stats
   - row attack type comes from latest raw data
   - Spirit Bear is treated as melee

4. Dyn-cell alignment:
   - keep `line-height: 0` on `td.hd-cell` so pills stay centered

## Files modified in this handoff segment

- `C:\Users\sikle\Documents\Sloppy\AGENTS.md`
- `C:\Users\sikle\Documents\Sloppy\build_heroes_dyn.py`
- `C:\Users\sikle\Documents\Sloppy\dyn_matrix_common.py`
- `C:\Users\sikle\Documents\Sloppy\scripts.js`
- `C:\Users\sikle\Documents\Sloppy\styles.css`

Generated locally:

- `C:\Users\sikle\Documents\Sloppy\heroes_dyn.html`

Untracked local reference assets still present on purpose:

- `C:\Users\sikle\Documents\Sloppy\icons\dyn_gems\`

Patch HTML files under `patches\` are generated/ignored build artifacts and are not committed.

## Verification done

- `python build_heroes_dyn.py` completed successfully and regenerated `heroes_dyn.html`
- Playwright/browser check confirmed the patch-page gap issue was removed after the final filter fix
- Follow-up bug from the first filter fix was corrected so unrelated entity cards no longer remain visible

## Deployment note

Normal flow here is:

1. commit source changes
2. push to `main`
3. GitHub Pages CI rebuilds ignored generated pages from source

## Recommended next step in Claude Code

Open and read:

- `C:\Users\sikle\Documents\Sloppy\sloppy_session_snapshot_2026_06_12_materials_filters_and_dyn.md`
- `C:\Users\sikle\Documents\Sloppy\AGENTS.md`

Then continue from the latest user request after this deploy.
