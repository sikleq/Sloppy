# Sloppy Session Snapshot — 2026-06-13 (`d5619b3` follow-up)

Project: `C:\Users\sikle\Documents\Sloppy`

Latest pushed commit already on `main`:

- `d5619b3d` — `feat: 13 hero innates (Sven/Drow/Luna/Medusa/DK/LS/Ogre/Razor/Ursa/DS/KotL/BM/DP) + table-overlay/chest/mojibake fixes`

This file exists so Claude Code can resume without reverse-engineering that
commit by hand.

## What `d5619b3` added

### Hero Stats innate model
- Added patch-gated stat modeling for these innates:
  - `Sven` — Great Cleave damage
  - `Drow Ranger` — Marksmanship agility %
  - `Luna` — Lunar Blessing damage + night vision
  - `Medusa` — Mana Shield EHP integration
  - `Dragon Knight` — Dragon Blood HP regen + armor
  - `Lifestealer` — attack speed
  - `Ogre Magi` — no +2 INT handling
  - `Razor` — Unstable Current move speed
  - `Ursa` — Maul %HP damage
  - `Dark Seer` — Quick Wit AS / INT
  - `Keeper of the Light` — Bright Speed INT / night vision
  - `Beastmaster` — Inner Beast attack speed
  - `Death Prophet` — Witchcraft move-speed multiplier

### Hero Stats rules now in effect
- `Damage` column = average damage only.
- `Dmg min` / `Dmg max` = `Expanded` only.
- Mini innate icon appears next to hero name for heroes whose stat-affecting
  innate is modeled in Hero Stats.
- `ehp_phys` / `ehp_mag` include `Medusa` Mana Shield logic.
- Floored attributes are used for derived HP / MP / primary-attr damage.
- `Techies` mana-pool regen is part of Hero Stats.

### Table / overlay fixes
- Sticky divider overlay repositions on `.creeps-scroll` scroll, not just window.
- `heroes_dyn` `Hide old` now emits a refresh / re-anchor path so the divider
  follows the actual matrix state.

### Chest icon
- `icons/ui/gothic/icon_chest_open.png` regenerated again:
  - contiguous open burst `45–53`
  - cleaner settle into loop start
  - intro duration reported in commit message as `1044ms`

### Mojibake repair
- `scripts.js` underwent cp1251-roundtrip recovery in that Claude session.
- Purpose: restore broken arrows / dashes / Cyrillic snippets in comments and
- some user-visible strings, especially stat-history tooltip text like
  `60 → 54` instead of broken mojibake.

### Repo hygiene
- Removed `icons/gothic_pixel_ui_free_v_1-0-2.zip` from git history going
  forward (user had already deleted it locally).

## Files touched by `d5619b3`
- `build_heroes_stats.py`
- `scripts.js`
- `styles.css`
- `scripts/gen_chest_icon.py`
- `icons/ui/gothic/icon_chest_open.png`
- deleted: `icons/gothic_pixel_ui_free_v_1-0-2.zip`

## Current local-only follow-up after that commit
- `AGENTS.md` was updated again after `d5619b3` with:
  - `per level` vs `per level up` distinction
  - Hero Stats `Damage` avg-only rule
  - mini innate icon rule
  - sticky divider overlay rules
- These AGENTS changes are local right now unless separately committed later.

## Untracked local files still intentionally not part of repo
- `chest_all_frames_sheet.png`
- `chest_all_frames_sheet2.png`
- `icons/dyn_gems/`
- `scripts/gen_items_dynamics_icon.py`
- `patches/`
- older handoff docs

## Resume guidance
- Read `AGENTS.md` first.
- Then read:
  - `sloppy_session_snapshot_2026_06_12_heroes_stats_innates_and_overlays.md`
  - this file
- Do not `git add -A`.
- Generated HTML remains gitignored and rebuilt by CI.
