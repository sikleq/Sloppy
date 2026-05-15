# Contributing to Sloppy

Thanks for taking the time to contribute. This document covers what's worth working on, the editing workflow, and the conventions the project enforces.

## What's worth contributing

- **Patch ports for older versions.** Anything pre-7.33 currently lacks the stats DB layer and renders with text-tag fallbacks. Backfilling stats and rewriting affected rows with `bstat_h(...)` adds material value.
- **Tag corrections.** The autodetector in `generate_patch_code.py` mislabels ~10–20% of rows. Spot-check the rendered HTML against the original Valve patchnote and PR fixes.
- **Icon mirror updates.** When Valve adds an innate ability icon that we currently fall back to the generic marker for, the audit script in [docs/data-format.md](docs/data-format.md) downloads it locally.
- **New helpers / patterns.** If you find a recurring pattern that requires hand-editing every patch, extract a helper into `build_patch.py` and document it in `docs/`.

## Editing workflow

1. **Find the patch section.** Each patch lives under a `# ===== PATCH 7.41c =====` comment in `build_patch.py`. The body is a sequence of `W(hero_header(...))`, `W(ability(...))`, `W(li(...))`, etc. calls.
2. **Make the edit.** Conventions for tags, badges, and structural blocks are documented in [docs/data-format.md](docs/data-format.md).
3. **Rebuild and verify.**
   ```bash
   python build_patch.py
   ```
   Open the regenerated `patches/<version>.html` in a browser. Click filters (BUFF / NERF / DEL / NEW / REWORK / MISC) to confirm the row surfaces in the expected categories.
4. **Run the audits** (CI runs these too, but it's faster to catch them locally):
   ```bash
   # Per-hero ul_open / ul_close balance
   python - <<'PY'
   import re, sys
   src = open('build_patch.py', encoding='utf-8').read().splitlines()
   depth, last_hero, problems = 0, None, []
   for i, line in enumerate(src, 1):
       if re.search(r'W\((hero|item|unit|plain|enchant)_header\(', line):
           if depth > 0: problems.append((last_hero, depth))
           depth = 0
           m = re.search(r'_header\("([^"]+)"', line)
           last_hero = m.group(1) if m else '?'
       if 'W(ul_open())' in line: depth += 1
       if 'W(ul_close())' in line: depth -= 1
   print(problems or 'OK')
   PY
   ```

## Conventions enforced by the project

These are the rules CI validates and that reviewers will flag:

- **`l=True` on lower-is-better stats.** Cooldown, mana cost, BAT, gold cost, channel time, cast point, recharge, penalty. Without it, the badge direction inverts (e.g. `b(1.7, 1.5)` renders +11.7% buff only with `l=True`).
- **Per-level rows must use `li_formula(...)` or `scale_pill(...)`.** Plain `b()` or `t("MISC")` for a `X + Y per level` row hides the scaling.
- **`"No longer levels with X"` is REWORK, not DEL.** The 7.41 mass-decouple of innates from ult / talent levels is a restructure, not a removal.
- **Aghanim's Scepter / Shard upgrade rows are merged into one li.** `Now upgraded with Aghanim's X` + the description rows collapse into `Aghanim's X: <description>` tagged NEW. The blue stripe auto-applies.
- **Subnotes belong inside the row they explain.** A `W(subnote(...))` immediately after `W(ability_change(...))` renders OUTSIDE the swap card — that's a bug. Move it into `new.desc=[..., inline_note("...")]`.
- **Trailing whitespace inside `W(li("text ", ...))` is rejected.**

Full set of conventions: [CLAUDE.md](CLAUDE.md) (the project's working notebook of every rule discovered while building).

## Commit hygiene

- One logical change per commit. A "fix Aghanim's Scepter row on Pudge" should not also bump three other heroes' tag corrections.
- Commit messages explain *why*, not just *what*. The mechanical diff is already in the patch.
- `python build_patch.py` must succeed before commit. CI fails otherwise.

## Filing issues

Include:

- Patch version (`7.41c`, `7.40e`, etc.).
- Hero / item / ability name as it appears on dota2.com.
- What you expected the row to show vs what's rendered (screenshot helps).
- If it's a tag classification dispute, link the Valve patchnote line you're comparing against.
