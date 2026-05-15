# Workflow: adding a new patch

## Step 1 — Pull Valve's data

1. Download the patch's KV file from Valve (usually surfaces on GitHub or via the Dota 2 VPK).
2. Drop it into `data/patchnotes_english.txt` (replace existing or append new version).
3. If there's a Russian translation, drop into `data/patchnotes_russian.txt`.

## Step 2 — Generate the scaffold

```bash
python generate_patch_code.py 7.42
```

Writes `_generated_p_7.42.py` containing `W(li(...))`, `W(hero_header(...))`, etc. calls extracted from the KV.

Manually review:

- **Tag detection** is right ~80% of the time. Re-tag rows where the autodetector picked the wrong direction.
- **`l=True` placement** on cooldown / mana cost / BAT / penalty rows.
- **Formula rows** — `bf()` / `li_formula()` calls need accurate lambdas.
- **New heroes / items / abilities** missing from `HERO_SLUG` / `ITEM_SLUG`.

## Step 3 — Integrate into build_patch.py

1. Open `build_patch.py`.
2. Find the current-patch section (comment `# ===== PATCH 7.41c =====`).
3. Add a new section for the next version, paste the reviewed code from `_generated_p_7.42.py`.
4. Hand-fix any remaining tag / flag issues.

## Step 4 — Register new entities

New hero:

```python
# build_patch.py — HERO_SLUG
"New Hero": "new_hero_slug",

# generate_patch_code.py — load_hero_internal_to_display()
'new_hero_slug': 'New Hero',
```

New item:

```python
# build_patch.py — ITEM_SLUG
"New Item": "new_item_slug",
```

`generate_patch_code.py` reads `ITEM_SLUG` from `build_patch.py` automatically.

## Step 5 — Build and verify

```bash
python build_patch.py
```

Open the regenerated `patches/7.42.html` and confirm:

- Filters (BUFF / NERF / NEW / DEL / REWORK / MISC / QoL) hide and show the right rows.
- Per-level formula tables expand on click.
- Hero / item / ability icons load (404s fall back to the generic innate marker via `onerror`).
- No Python exceptions on the build run.

## Step 6 — Audit

```bash
python check_icons.py
```

Walks `_ability_icons.txt` and reports any URLs that don't resolve on Valve CDN. Missing icons aren't fatal — they fall back gracefully — but the report tells you which slugs to monitor.

## Step 7 — Deploy

Push to `main`. GitHub Pages serves `https://sikleq.github.io/Sloppy/`. The `build` workflow (`.github/workflows/build.yml`) re-runs `python build_patch.py` on every push and fails the build if syntax / audits regress.

## Common errors

| Error | Cause |
|---|---|
| `KeyError` in `t()` | Unknown tag — check the value against `TAG_OVERRIDES` |
| Icon 404 (in the page) | Wrong slug in `HERO_SLUG` / `ITEM_SLUG`, or Valve hasn't added the icon yet |
| Filter doesn't match the row | `data-tag` attribute missing or wrong — check the badge call |
| Formula table doesn't expand | `bf()` didn't return the table to `extra=table` in `li()` |
| BAT row shows wrong direction | Missing `l=True` on `b(old, new)` |
