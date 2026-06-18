# Workflow: adding a new patch

## Step 1 — Pull Valve's data

1. Download the patch's KV file from Valve (usually surfaces on GitHub or via the Dota 2 VPK).
2. Drop it into `data/patchnotes_english.txt` (replace existing or append new version).
3. If there's a Russian translation, drop into `data/patchnotes_russian.txt`.

## Step 2 — Generate the scaffold

```bash
python generate_patch_code_v2.py 7.42
```

Reads the cached datafeed JSON (`data/7.42_datafeed.json`) and writes
`_generated_p_7.42_v2.py` containing `W(li(...))`, `W(hero_header(...))`, etc.
calls built on the `patch/` helper API.

Manually review:

- **Tag detection** is right ~80% of the time. Re-tag rows where the autodetector picked the wrong direction.
- **`l=True` placement** on cooldown / mana cost / BAT / penalty rows.
- **Formula rows** — `bf()` / `li_formula()` calls need accurate lambdas.
- **New heroes / items / abilities** missing from `HERO_SLUG` / `ITEM_SLUG`.

## Step 3 — Save as a content module

1. Review and hand-fix `_generated_p_7.42_v2.py`.
2. Save the reviewed body as `content/p742.py`, wrapping it in `def build():`.
3. Register it in `builders/patch.py`:
   ```python
   import content.p742
   # in __main__ (oldest → newest):
   content.p742.build()
   ```

## Step 4 — Register new entities

New hero / item — add the display-name → engine-slug mapping in `patch/images.py`:

```python
# patch/images.py — HERO_SLUG
"New Hero": "new_hero_slug",

# patch/images.py — ITEM_SLUG
"New Item": "new_item_slug",
```

(`generate_patch_code_v2.py` resolves names from the cached `data/herolist.json`
/ `data/itemlist.json` datafeeds, so the generator itself needs no manual map.)

## Step 5 — Build and verify

```bash
python builders/patch.py
```

Open the regenerated `patches/7.42.html` and confirm:

- Filters (BUFF / NERF / NEW / DEL / REWORK / MISC / QoL) hide and show the right rows.
- Per-level formula tables expand on click.
- Hero / item / ability icons load (404s fall back to the generic innate marker via `onerror`).
- No Python exceptions on the build run.

## Step 6 — Audit

```bash
python scripts/audit/check_icons.py
```

Walks `_ability_icons.txt` and reports any URLs that don't resolve on Valve CDN. Missing icons aren't fatal — they fall back gracefully — but the report tells you which slugs to monitor.

## Step 7 — Deploy

Push to `main`. GitHub Pages serves `https://sikleq.github.io/Sloppy/`. The `build` workflow (`.github/workflows/build.yml`) runs the tests, then `python builders/patch.py` (+ the other builders) on every push and fails the build if tests / audits regress.

## Common errors

| Error | Cause |
|---|---|
| `KeyError` in `t()` | Unknown tag — check the value passed to `t(...)` (BUFF/NERF/REWORK/MISC/QoL/NEW/DEL) |
| Icon 404 (in the page) | Wrong slug in `HERO_SLUG` / `ITEM_SLUG`, or Valve hasn't added the icon yet |
| Filter doesn't match the row | `data-tag` attribute missing or wrong — check the badge call |
| Formula table doesn't expand | `bf()` didn't return the table to `extra=table` in `li()` |
| BAT row shows wrong direction | Missing `l=True` on `b(old, new)` |
