# Weights — how a patch row becomes a number

Living doc. Review with findings: [weights-review.md](weights-review.md). Decisions by Денис (2026-09-16):
**two scales** (net balance `w` + volume `v`), **hybrid magnitude** (Valve's typical step for base
stats, typical % per type otherwise).

## Formula (patch/weights.py)

```
row net    = weight(type) × context × direction × magnitude
row volume = weight(type) × context × magnitude          (reworks: magnitude 1, no sign)
w, v       = Σ rows of the entity in that patch  →  _dynamics.json patches[ver]["w"|"v"]
```

| Piece | Source | Notes |
|---|---|---|
| type | ordered regex table `CAT`, matched on the text **before the first verb** (increased/decreased/…); `replaced with …` rows use the new effect | bkb_pierce/chance demoted to the end; projectile before move_speed; `damage block` → armor |
| weight | `data/rules/valve_weights.json` → `final` | consensus rank shrunk to `other` (0.40) when < 3 signals: `respawn 0.97→0.59`, `chance 0.93→0.58`, `bkb_pierce 0.90→0.57`; `cost 0.45`, `turn_rate 0.2`, `other 0.4` are manual |
| context | `valve_weights.json` → `context` | ultimate 1.3 (slugs read from the latest KV `AbilityType ULTIMATE`, 151), ability/innate/scepter/base stat/item 1.0, shard 0.9, facet 0.8, talent 10/15/20/25 = 0.6/0.8/1.0/1.2 |
| direction | tags | buff +1, nerf −1, sole `new` +0.5, sole `del` −0.5, rework/misc/qol 0 |
| magnitude | hybrid | GENERAL rows: `|Δ| / typical_step` (MS 5, base dmg 3, stats 2, stat gain 0.2, armor 1, HP regen 0.5, mana regen 0.25 …). Other rows: `mean|%| / typical_pct[type]` (signal C medians: cooldown 17.7, damage 17.8, health 25, cast_point 42.9 …); 0% badges count; "Recipe … Total cost …" uses the total. Cap 3. No badge → 1.0 |

## Signal J — Valve's exchange rate (done 2026-09-16)

From the 3 865 buff↔nerf compensation pairs inside one (hero, patch) (`cde_dynamics.json`): if Valve gives
+b % of X and takes −n % of Y in the same breath, then `value(X)·b ≈ value(Y)·n`. Least squares on
`log u_X − log u_Y = log n − log b` (anchor: mean log u = 0), 200-sample bootstrap for the CI. `u` = value of
+1 % of the type. Stored in `valve_weights.json → J`.

| type | u | 95 % CI | | type | u | 95 % CI |
|---|---|---|---|---|---|---|
| base_damage | 2.80 | 2.30–3.31 | | stun | 0.97 | 0.82–1.13 |
| move_speed | 2.11 | 1.77–2.43 | | projectile | 0.93 | 0.73–1.14 |
| attack_speed | 1.47 | 1.24–1.70 | | armor | 0.82 | 0.67–1.01 |
| mana_cost | 1.42 | 1.26–1.61 | | slow | 0.78 | 0.66–0.91 |
| crit | 1.31 | 0.98–1.70 | | charges | 0.76 | 0.62–0.93 |
| range | 1.25 | 1.10–1.40 | | lifesteal | 0.69 | 0.48–1.04 |
| stats | 1.21 | 1.08–1.36 | | health | 0.64 | 0.55–0.73 |
| cooldown | 1.19 | 1.07–1.30 | | magic_res | 0.48 | 0.31–0.70 |
| damage | 1.06 | 0.98–1.16 | | cast_point | 0.46 | 0.40–0.53 |

**How it is used:** for every row with % badges the value is now `u[type] × mean|%| / 20` (a 20 % change of
a u = 1 type = 1.0) — this replaces `weight × magnitude` for those rows, because J measures exactly "how much
of X Valve trades for how much of Y". Base-stat rows (typical step), rows without numbers and types without
J keep the consensus weight. Talent multipliers lowered to 0.5/0.6/0.7/0.8 (talent bonuses are small
numbers, so their % swings are huge). Classifier: last-matching category in the trimmed parameter name
("Movement speed bonus **duration**" → duration), ties to the earlier category ("Bolt Speed" → projectile).

Re-checked after the change: revert backtest Q1→Q5 = 4.6 % → 11.2 %; `corr(w, buff−nerf)` 0.85 → 0.83.

## Items — gold scale (review E.6, done 2026-09-16)

Item rows that change a **priced stat** ("Mana Regen bonus +0.8 → +0.6") or the **total cost** are scored in
gold: `fraction = Δ × gold-per-unit / item cost`, where gold-per-unit comes from signal A per patch version
(`data/rules/item_stat_prices.json`, %-stats priced per 1 %) and the cost from `data/stats/<ver>/items.json`.
`net = 0.6 × sign × min(5 × fraction, 3)` (20 % of the item's value = 1.0; 0.6 = median hero type weight so
both scales line up). Other item rows (actives, cooldowns, % bonuses) use the hero formula.
Examples 7.41f: Infused Raindrops −0.2 mana regen = 99 g of a 225 g item → −1.32; Octarine +200 g of 5100 →
−0.12; Satanic lifesteal 30 → 25 % = 204 g of 5050 → −0.12.

## Backtest (docs/weights-review.md E.8.1) — 2026-09-16

11 408 numeric hero events 7.08→7.41e. "Reverted" = same parameter moved the other way within 8 patches (base rate 6.0 %).

| quintile of row score | revert rate |
|---|---|
| Q1 (≈0.15) | 4.2 % |
| Q3 (≈0.47) | 5.3 % |
| Q5 (≈1.35) | **10.3 %** |

Monotone, ×2.5 from Q1 to Q5; raw |%| alone gives 4.0 → 9.2 %, the type weight alone 4.6 → 7.2 %. So the
score carries real (if modest) information beyond the counter. `corr(w, buff−nerf)` per cell is still 0.85 —
the number is dominated by how many rows Valve wrote; volume `v` is the honest place for that.

## Agreement test (review E.8.2) — 2026-09-17

120 buff/nerf rows, stratified by |score| quintile, graded BLIND (no scores shown) on a 1–5 impact scale by
an independent judge (LLM analyst persona; Денис can re-grade the same file `outputs/agreement_blind.json`).
Grades: 1 ×23, 2 ×64, 3 ×29, 4 ×3, 5 ×1. **Spearman ρ(|score|, grade) = 0.21** — weak. Median |score| by
grade: 0.45 / 0.90 / 0.82 / 0.44 / 1.33 — no monotone rise above grade 2.

Where the model and the judge disagree most:
- **Tiny absolute changes with big %**: Riki slow 0.4 s → 0.5 s (+25 %) = 1.42, Luna/PA level-10 talents
  +0.1 s = 1.1–1.2 — judge: 1. The % scale has no notion of "0.1 s is nothing".
- **Core mechanics the text does not flag**: Meepo clone stats 85 → 90 % (+6 %) = 0.12, Morphling shift rate
  −20 % = 0.39, Underlord aura reduction +33 % = 0.37 — judge: 3–4.
- **Base stats**: Spectre BAT 1.7 → 1.8 = 0.52 (one Valve step), judge 4 (carry DPS all game).

Conclusion: the score measures *how large the edit is relative to the parameter*, not *how much the hero
changes*. The revert backtest says that is still predictive of Valve's own follow-ups (Q1→Q5 4.6 → 11.2 %),
but it is not "impact". Candidate fixes (need a decision): an absolute floor per unit (durations < 0.5 s,
talent deltas below one typical step → ×0.5); a per-ability importance prior (ultimates already ×1.3; core
passives/innates could get a manual list); re-grade by Денис to confirm the judge.

### Follow-up applied 2026-09-17 — absolute floor (decision delegated to Claude)

A big % of a tiny number is still tiny: rows whose max-rank change is **< 0.25 s → ×0.35**, **< 0.5 s → ×0.5**,
or **< 2 percentage points → ×0.5** (`_small_change_damp`). With the floor and the correct base-stat context
the same 120 rows give **ρ = 0.34** (was 0.21). A manual "core mechanics" list was rejected as subjective;
Денис re-grading the blind file remains the way to check the judge.

### Skill priority — objective "how central is the ability" (2026-09-17)

The fill-in table idea was dropped (Денис: inconvenient, should be math). Instead: how pros actually skill
the hero. `tools/fetch_skill_priority.py` asks the OpenDota explorer for the skill points put into each
ability within the first 10 upgrades (pro matches, last 120 days; 387 abilities, 127 heroes), and turns the
share among basic abilities into a multiplier `clamp(1 + 1.5·(share − 1/n), 0.7, 1.3)` →
`data/rules/ability_priority.json`. Examples: Anti-Mage Blink 1.18 / Mana Break 1.11 / Counterspell 0.72;
Meepo Poof 1.25 / Earthbind 0.70; Riki Smoke Screen 0.70. Ultimates keep ×1.3, innates/facets 1.0.
Effect on the blind-judge agreement: none (ρ 0.338 → 0.337) — kept because it is objective and cheap;
re-run the script after big meta shifts.

## Matrix chart (heroes_dyn / items_dyn)

One **step line** per row, the row is the zero axis: a touched patch is a flat plateau across its cell
(nothing is interpolated between patches), vertical risers at cell edges join neighbours (0 for an untouched
patch; the riser back to the axis is drawn in the next untouched cell). Colour follows the side of the axis
(above = green, below = red; a riser crossing the axis is split). **Linear per-row scale over the VISIBLE
columns only** (row max |w|, at least 1.5, = half cell): 2.0 is exactly twice as high as 1.0. Redrawn after
every layout pass ("Hide old", resize). History of rejected variants: bars v1, sqrt line, cumulative line, bars v2 with a volume band.

## Open / next
1. ~~Items in gold~~ done.
2. ~~Signal J~~ done (now the main source for % rows).
3. ~~Formula rows (F.6)~~ done: per-level rows take the |%| of the last non-zero level (max rank) when its direction agrees with the row's tag; when `b()` flipped the tag by the average (front-/back-loaded, early-game cut, flatten) all levels are averaged.
4. ~~Agreement test~~ done (ρ = 0.21, see above) — follow-ups pending decision.
5. Niche parameters hitting the cap (e.g. "invisibility linger 2s→1s" = −1.83 for Treant 7.41f): consider a lower cap or per-type caps.
