# Captains Mode changes — authoring rule

Some patches change the **Captains Mode draft** (ban/pick order, number of
bans/picks, reserve time, phase structure). Valve writes these as flat prose
("First - Second - Second - First …"), which is hard to read. We render the
**order** changes as a coloured token board via `cm_draft(...)` instead of text.

In-game this is the pick/ban screen (the numbered Radiant/Dire slot column).
Background on the mode + historical order:
<https://dota2.fandom.com/wiki/Game_modes#Captains_Mode>.

## When to use `cm_draft`

Use it whenever a patch changes **the order in which teams ban or pick** (which
team acts at each step of a phase). Examples: "Changed order of the first and
third ban phases", "Swapped pick order in the second pick phase".

Do **not** force it for non-order CM tweaks — those stay normal `li(...)` rows:

| Change type | How to render |
|---|---|
| Draft **order** of a phase (who acts when) | `cm_draft(...)` board |
| Reserve / drafting **time** values | `li(... b(old, new, l=True))` (time → lower is better) |
| **Number** of bans/picks added/removed | `li(... t("NEW"/"DEL"))` |
| Hero **added to / removed from** CM pool | `li("Added to Captains Mode", t("NEW"))` |
| Whole phase added/removed/restructured | `li(... t("REWORK"))` + optionally a `cm_draft` board showing old vs new |

## How

Always pass the **WHOLE draft** (every phase, all 24 steps), not just the
changed phase(s) — the point is to show how the full draft flows Old vs New,
with the in-game step numbers (1..24). Unchanged phases render identically in
both boards; only the reordered steps land on a different side.

1. Keep a summary `li(...)` with the proper tag (usually `t("REWORK")`) inside
   the `ul` — it carries the filter tag + feeds the patch-dynamics tally, and is
   the plain-English "what changed" line.
2. Close the `ul`, then emit the board with `W(cm_draft(...))` (it's a block
   `<div>`, a sibling of the `ul`, never inside an `<li>`).

```python
W(plain_header("Captains Mode"))
W(ul_open())
W(li("Changed order of the first and the third ban phases", t("REWORK")))
W(ul_close())
W(cm_draft(                          # short titles (not drawn — just structure docs)
    ("Ban 1",  "FSSFSSF", "FFSSFSS"),   # changed this patch
    ("Pick 1", "fs",      "fs"),
    ("Ban 2",  "FFS",     "FFS"),
    ("Pick 2", "sffssf",  "sffssf"),     # snake order, NOT plain alternation
    ("Ban 3",  "FSSF",    "FSFS"),       # changed this patch
    ("Pick 3", "fs",      "fs"),
))
```

The board renders like the in-game pick/ban screen: **vertical**, step numbers
1..N down the centre, the acting team's slot on the **left (first-pick team)** or
**right (second-pick team)**. The first-pick team makes the FIRST hero pick
(step 8); the second-pick team picks at step 9 — encode `F`/`f` and `S`/`s`
accordingly.

Old and New sit **side by side**, each its own **light block** (styled like the
ability_change rework panes), with a `→` arrow between them (`.ability-change-arrow`);
no big outer box, no "Old"/"New" labels (the arrow implies direction). Column
headers ("First pick" / "Second pick") stay on one line.

Layout is **symmetric**: each step sits at the **same row in both boards**, so
only the reordered steps stand out (their slot is on the other side). **Bans** are
one fixed 1-row slot each — all identical size, narrow, with a faint bordeaux
crosshair. **Picks** pair up — two consecutive picks (one per side) share a 2-row
band and sit **facing each other**, reading taller and filling the lane; picks are
identical in Old/New so pairing keeps the two boards row-aligned. A long connector
ties each number to its slot (lanes sit well apart). **No colours, no legend, no
change-highlight, no hover tooltip.** Phase titles in the tuples document the
structure but are **not drawn**. `first_label` / `second_label` default to
`"First pick"` / `"Second pick"`.

> ⚠ The second pick phase is a **snake** (`sffssf` = 2nd,1st,1st,2nd,2nd,1st pick
> team), not plain alternation — verify pick order against the live in-game board.

### Sequence encoding

Each phase is `(phase_title, old_subseq, new_subseq)`. Concatenated in order the
phases form the full draft; tokens are numbered **continuously 1..N** (not reset
per phase). Each seq char is one action, in order:

| Char | Meaning |
|---|---|
| `F` | **Ban** by the first-pick team |
| `S` | **Ban** by the second-pick team |
| `f` | **Pick** by the first-pick team |
| `s` | **Pick** by the second-pick team |

- Slot **side** = team (left = first-pick team, right = second-pick team).
  No colours — side alone (plus the column header) identifies the team.
- Slot **size** = ban (small narrow box) vs pick (larger box filling the lane —
  like the hero-portrait slots in-game).
- The **number** down the centre is the in-game step number (1..N across the draft),
  tied to its slot by a thin connector that starts right at the digits.
- Old and New are separate, **row-aligned** boards — read/compare them directly; a
  reordered step simply appears on the other side at the same row.
- `first_label=` / `second_label=` override the column headers (default First pick / Second pick).
- `old`/`new` totals must be equal length (raises `ValueError` otherwise).

### The current full-draft structure (7.34+)

24 steps = **Ban×7 · Pick×2 · Ban×3 · Pick×6 · Ban×4 · Pick×2**
(sources: esports.gg / gosugamers, patch 7.34). Ban distribution: first-pick
team **3-2-2**, second-pick team **4-1-2** (7 bans each). Picks **1-3-1** per
team, alternating. If a later patch changes the structure itself, update the
phase tuples to match the in-game board.

### Reading the order from a Valve patchnote

Valve lists each phase's order as "First - Second - …" where **First = team with
the first pick**, **Second = team with the second pick**. Map each entry to
`F`/`S` (bans) or `f`/`s` (picks). For phases the patch did NOT touch, fill in
the current order from the structure above / the live in-game board so the full
draft is accurate. Verify counts per phase (e.g. first ban phase = 7 chars).

## Reusing this for other patches

The helper is **fully general** — it does not know about 7.40. To document any
patch's CM order change you supply the whole draft as phase tuples (old + new).
Steps to author a new one:

1. Find the patch's CM note. It states only **what changed** (e.g. a phase's
   order old→new). CM order changes are rare, so this is usually 1–2 phases.
2. Reconstruct the **full draft as of that patch** — the unchanged phases too.
   Take the structure/order from the wiki or the in-game board *for that era*
   (the draft has been restructured before, e.g. 7.34 set the current
   Ban7·Pick2·Ban3·Pick6·Ban4·Pick2). For older patches read it "backwards":
   apply the change to get the new order, and the pre-change order is the old.
3. Encode each phase as `(title, old, new)` with `F/S/f/s` and call `cm_draft`.

**Known limitations (be honest about these):**
- The patch note alone is **not enough** — you must know the full draft structure
  for that era and fill in the unchanged phases. Verify against the live/era board.
- Symmetry (row-aligned Old vs New) holds because only **ban** sides change while
  **picks stay identical**. If a patch reorders the **pick** phases, the pick
  pairing can differ Old vs New and the boards may no longer be row-aligned —
  acceptable, but revisit the layout if that ever happens.
- If a patch changes the **structure itself** (counts per phase), just pass the
  new phase tuples; nothing else needs changing.
- New action kinds (a neutral/extra step) would need a new char + a `.cm-token.*`
  style.

Helper lives in `patch/elements.py` (`def cm_draft`); styles in `styles.css` under
"Captains Mode draft board".

## Historical draft-order changes (reference)

The full per-patch history IS recoverable — Liquipedia's **Game Modes /
Changelog** lists each change as an old→new diff, so chaining the diffs
reconstructs the exact draft for any era (you don't have to guess). Source:
<https://liquipedia.net/dota2/Game_Modes/Changelog> (verify before shipping — this
is a third-party wiki summary). Timeline of order/structure changes:

| Patch | Change to the draft |
|---|---|
| 6.55 | Captains Mode introduced |
| 6.78 | Captains Mode reworked |
| 7.15 | Round time 30s→35s; **2nd ban phase** order `2nd/1st/2nd/1st` → `1st/2nd/1st/2nd` |
| 7.25 | Ban count per round `3/2/1` → `4/1/1`; added the 50%-chance auto-roll ban system |
| 7.27 | Ban count `4/1/1` → `2/3/2`; round 35s→30s; **1st pick phase** `R/D/D/R` → `R/D/R/D`; **3rd ban phase** `D/R` → `R/D/R/D` |
| 7.29 | **1st pick phase** `R/D/R/D` → `R/D/D/R` |
| 7.30 | **2nd pick phase** `D/R/D/R` → `D/R/R/D` |
| 7.34 | Bans `2-3-2` (both) → **`3-2-2` first-pick / `4-1-2` second-pick**; 1st ban time 30s→15s. This sets today's structure: Ban7·Pick2·Ban3·Pick6·Ban4·Pick2 |
| 7.40 | **1st ban phase** `FSSFSSF`→`FFSSFSS`; **3rd ban phase** `FSSF`→`FSFS` (implemented here) |

Notes:
- `R/D` = Radiant/Dire in a reference game where Radiant has first pick; map to
  `First/Second` (= our `F/S` · `f/s`) when encoding.
- The structure (counts per phase) itself changed at **7.25** (ban counts
  `3/2/1`→`4/1/1`), **7.27** (`4/1/1`→`2/3/2`) and **7.34** (`2/3/2`→`3-2-2`/`4-1-2`,
  and picks → `1-3-1`). So the *skeleton* differs by era, not just the order.

### Building automatically as we author 7.08 → present

We author patches **forward in version order** (the site starts at 7.08), so the
clean approach is to keep a **running "current CM draft" state** and apply each
patch's diff as you reach it — no need to precompute every era:

1. Establish the **7.08-era full draft** once (the state *before* 7.15's change),
   from 7.08's own notes / the wiki for that era.
2. For each later patch you author: if its notes touch CM order, the note states
   the exact `old → new` for the changed phase(s). Set `old` = running state,
   apply the diff to get `new`, render `cm_draft(old…, new…)`, then **adopt `new`
   as the running state** for the next patch.
3. Patches that don't touch CM order leave the running state unchanged.

This is reliable because each patch's **own** notes (which we have in the repo
data when we author it) give the authoritative diff — we never guess. The table
above is just the map of *which* patches to expect a CM change in.

⚠ Do **not** hard-code the older full sequences from the wiki summary above — it
is lossy (third-party, model-parsed). Lock each patch's exact order from that
patch's real notes at authoring time.

- Only **7.40** is implemented on the site so far. The earlier CM-changing patches
  (7.15, 7.25, 7.27, 7.29, 7.30, 7.34) will get their `cm_draft` when those pages
  are authored on the way up from 7.08.
