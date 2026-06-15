# Game-formula change — authoring rule

Some patches rework an **important game formula** (Assist Gold, Experience,
bounty, comeback gold, etc.). Render the formula as a coloured **old → new**
block via `formula_change(...)`, not as two flat `li` rows ("OLD: …" / "NEW: …").
It mirrors the ability_change rework swap so formula changes read consistently.

## When to use

A change to a **named arithmetic formula** with an old and a new expression.
Examples: "Assist Gold Formula Reworked", "Experience formula changed".

Do NOT use it for a single value tweak (`b(old, new)`), or a non-formula description.

⚠ **`formula_change` is ONLY for true multi-variable game-economy formulas** (Assist
Gold, XP/bounty streak, comeback gold, armor) — a computation with named inputs like
`NumHeroes` / `VictimNetworth`. A **per-level value/stat change** — `X → Y + Z per
level` (e.g. "Health Restoration Reduction changed from 35% to 24.5% + 0.5% per
level", or "Courier respawn time decreased from 60s + 6s per Hero Level to 45s + 5s
per Hero Level") is **NOT** a game formula — render it inline with **`li_formula`**
(prefix + old/new strings + old_fn/new_fn for the per-level popover table; `l=True`
for timers). That keeps it a normal change row, not a big block.

## How

`formula_change(name, old, new, *, tag="REWORK")` returns a standalone block
`<div>` — emit it via `W()` (no surrounding `ul`, no separate summary `li`; it
carries its own `data-tag` so the filter chips surface it).

```python
W(formula_change(
    "Assist Gold Formula",
    "60 + ( ( VictimNetworth * 0.037 ) / NumHeroes )",
    "15 + ( ( 50 + ( VictimNetworth * 0.037 ) ) / NumHeroes )",
    vary=("NumHeroes", "Heroes", [1, 2, 3, 4, 5]),   # worked examples
    fixed={"VictimNetworth": 10000},
    unit="Gold",
))
```

- `name` is the formula's label (no need to append "Reworked").
- `old` / `new` are plain expression strings. `_fmt_formula` styles them: `*`→`×`,
  identifiers (`VictimNetworth`, `NumHeroes`) get `.f-var` colour, numbers get
  `.f-num` colour; parentheses/operators stay muted.
- `tag` defaults to `"REWORK"`; its badge sits on the **left** of the title (like a
  row tag) and is also the block's `data-tag` for filtering.
- **No "Old"/"New" labels on the panes** — the `→` already shows direction
  (general rule for any old→new arrow block; same as `cm_draft`).
- The formula is **centred** in each pane.

### Worked examples + live calculator (do this for every formula)

Pass `vary=(var, label, [values])` + `fixed={input_var: default}` + `unit="…"`
(and `lower_better=True` if a SMALLER result is the buff). Then:

- Each pane shows a **grid table** (faint lines) under the formula. OLD =
  `Heroes | <unit>`; NEW = `Heroes | <unit> | Δ%`. The **Δ%** (old→new change for
  that row) is **NEW-pane only** and is wrapped in `.badge-group` so it renders as
  **plain coloured text (no pill box)** — identical to the % at the end of normal
  patch rows (`gradient_class` colours). The number input has **no spinner arrows**.
- Input label: "Set " (normal text) + variable name (`.fx-vname`, var colour) + ":".
- A **number input** (`formula-input`) lets the reader type their own value for the
  `fixed` variable; `scripts.js` (`.formula-change[data-fx-old]`) re-evaluates every
  row live via `new Function(invar, varyvar, …)`. Empty input → the default. The
  default is shown only as the placeholder **"By default: <value>"** (no caption).
- Server-side render uses the default so it works without JS; `_eval_formula`
  (restricted `eval`) computes the initial cells, `_formula_pct_badge` the Δ%.
- **If a formula contains `NumHeroes`, give up to 5 rows (1–5 — max team size).**
- Pick a representative default for free variables — networth-style → **10000**.
- Rows: no per-cell hover highlight; row hover draws a dashed "ruler" (like the
  patch-note rows). A real chart could replace the table later.
- **`vary` without `fixed`:** if the only variable IS the row variable (e.g. a
  per-`Level` value like courier respawn `60 + 6*Level` → `45 + 5*Level`), pass
  `vary=("Level","Hero Lvl",[1,5,…,30])` and **no `fixed`** — then there's no
  input field and the table is static. `tag="BUFF"`/`"NERF"` work (mapped to the
  `*-text` badge classes); set `lower_better=True` for timers (faster = buff).

Helpers (`_fmt_formula`, `_eval_formula`, `_formula_pct_badge`) live in
`patch/elements.py`; styles in `styles.css` under "Game-formula change"; the live
recompute is in `src/scripts.js` ("Formula calculator").

First used in **7.40** General Changes (Assist Gold, higher gold = buff) — at
VictimNetworth 10,000: Old `430→134`, New `435→99` gold for 1→5 heroes
(Δ% +1.2% at 1 hero → −26% at 5).

## Formula changes to expect across patches (reference)

`data/patchnotes_english.txt` is a **consolidated multi-patch loc file** (keys like
`DOTA_Patch_7_27_*`, `7_31_*`, `7_33_*`), so as we author patches forward from 7.08
each of these gets a `formula_change` block. Known formula reworks (verify exact
strings against that patch's own notes when authoring):

| Patch | Formula | Old → New |
|---|---|---|
| 7.11 | AoE gold (losing team) | descriptive rework, not a clean expression — may stay prose |
| 7.27 | Armor | → `Armor * 0.06 / ( 1 + Armor * 0.06 )` |
| 7.27 | Assist gold | `45 + 0.033 * NW` → `30 + 0.038 * NW` |
| 7.31 | Bounty gold streak | `35*x - 5` → `5*x^2 + 5*x` (x = streak) |
| 7.31 | XP streak | `10*(x-1) * L` → `(x^2 - x + 8) * L` (x = streak, L = level) |
| 7.33 | Gold assist | `(30 + (VictimNetworth*0.038)) / NumHeroes` → `10 + ((50 + (VictimNetworth*0.037)) / NumHeroes)` |
| 7.40 | Assist gold | `60 + ((VictimNetworth*0.037)/NumHeroes)` → `15 + ((50+(VictimNetworth*0.037))/NumHeroes)` (done) |

Encoding notes for these:
- **`^` = exponentiation** (handled: `_eval_formula` and the JS evaluator map `^`→`**`).
- Write **implicit products explicitly**: `10 * (x-1)`, never `10(x-1)`.
- Choose the right `vary` var + sensible `fixed`: NumHeroes → 1–5; streak `x` →
  e.g. 1–6 (or the streak cap) with `L` fixed; pure-`NW` formulas (7.27 assist)
  vary nothing meaningful per row → vary NW itself (a few networth values) or use
  the input alone. Set `lower_better` per metric (gold/xp higher = buff).
