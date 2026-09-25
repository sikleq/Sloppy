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

First fit (2026-09-16; superseded 2026-09-25, see below): base_damage 2.80, move_speed 2.11,
attack_speed 1.47, mana_cost 1.42, crit 1.31, range 1.25, stats 1.21, cooldown 1.19, damage 1.06 … cast_point 0.46.

**Refit 2026-09-25 (`tools/fit_signal_j.py`):** the first fit pooled hero **base-stat** events with
ability/talent events. Base stats move in tiny % steps (+5 of 300 MS = 1.7 %, +3 of 55 damage = 5 %), so they
pushed `u` up for the types that also name spell parameters — but the site never applies J to base-stat rows
(those use the typical step). A spell's "Base Damage 270 → 240" was therefore valued 2.6× the same change
named "Damage". The refit types base-stat events separately (`base:<type>`, stored as `J.base_u` for
reference: base damage 3.81, base MS 5.30, base stats 1.36) — 3 728 pairs, types with ≥ 30 sides:

| type | u | 95 % CI | | type | u | 95 % CI |
|---|---|---|---|---|---|---|
| crit | 1.66 | 1.12–2.23 | | silence | 1.02 | 0.69–1.56 |
| mana_cost | 1.35 | 1.21–1.52 | | damage | 1.02 | 0.94–1.11 |
| attack_speed | 1.29 | 1.03–1.57 | | stun | 0.97 | 0.81–1.17 |
| base_damage | 1.23 | 1.01–1.53 | | projectile | 0.87 | 0.69–1.06 |
| range | 1.23 | 1.09–1.36 | | health | 0.87 | 0.75–0.98 |
| cooldown | 1.17 | 1.06–1.28 | | armor | 0.85 | 0.68–1.06 |
| move_speed | 1.12 | 0.96–1.32 | | slow | 0.78 | 0.66–0.94 |
| duration | 1.12 | 1.00–1.25 | | charges | 0.75 | 0.63–0.91 |
| cast_range | 1.09 | 0.91–1.27 | | stats | 0.72 | 0.59–0.93 |
| mana | 0.73 | 0.45–1.15 | | gold_xp | 0.69 | 0.46–1.01 |
| lifesteal | 0.67 | 0.50–0.99 | | magic_res | 0.53 | 0.35–0.80 |
| cast_point | 0.39 | 0.33–0.45 | | vision | — | < 30 sides, consensus weight |

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
Since 2026-09-25: a row is priced only when its parameter name IS the item's stat line ("Agility bonus",
"Bonus Damage", "Mana Regen"); "Glimmer Bonus Movement Speed", "Dominated Creep movement speed", "Arctic
Blast damage", "Corrosion armor reduction" go through the hero formula. Cost rows: "Total cost unchanged"
(in the row or its inline note) = 0; a basic item's "Cost A → B" and a lone "Recipe cost A → B" are gold
deltas like "Total cost A → B". Item property panes (`properties_change`) are scored as
"<Stat> bonus changed from A to B" with the pane's badge.
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

## Signal K — talents: what pros pick and why (2026-09-18)

Data: OpenDota explorer, pro matches, one query per patch window — **4.9 M talent picks with wins over 116
versions** (7.08 → 7.41e); talent pairs of every version from KV (56 512); per talent the modified ability
parameter and its base value (relative boost). Scripts `k_talent_*.py` live with the model in
`outputs/valve-revealed-weights-20260915/`.

**Can the "importance" of a talent be learned from features?** Bradley–Terry model
`P(A over B) = σ(f(A) − f(B))`, f linear in effect type, log relative boost, "modifies the ultimate",
pro skill priority of the modified ability, generic stat gold value. 4 672 matchups with ≥ 40 picks, time
split at 7.36:

| model | majority-side accuracy (test) | Spearman |
|---|---|---|
| coin flip | 0.46 | 0.03 |
| effect type only | 0.51 | 0.04 |
| full model | **0.56** | 0.12 |

So only weakly — Valve builds pairs to be close, and the choice is mostly hero- and game-specific. What the
model does explain (logit units, +0.4 ≈ 60/40):
- **target_priority +0.66** — a talent that boosts the ability pros max first is picked far more;
- liked types: cast range +0.61, charges +0.23, attack speed +0.19; disliked: slow −0.37, move speed −0.29,
  lifesteal −0.28, armor/evasion −0.22, base damage −0.21;
- **size of the relative boost ≈ 0** — numbers inside a pair are already balanced by Valve;
- **pick share ≠ strength**: over 2 319 pairs with ≥ 100 picks a side, corr(pick share, win-rate gap) =
  **−0.28**; the less popular talent wins more (it is taken when it fits), mean |gap| 4.2 pp.

**What is used on the site:** not the model, but measured / structural facts per changed talent tier
(`data/rules/talent_tiers.json`, 2 469 tiers in history, 282 in annotated patches):
1. **Measured share shift** (single-side replacements, ≥ 30 pro picks before and after; 1 542 in history, 225
   annotated): shift of the pro pick share of the replaced slot against the unchanged sibling;
   `net = 0.4 × talent context × sign × min(|Δshare| / 0.2, 3)`.
2. **Level moves** (422 tiers, 104 annotated): the new talent existed in the previous version at another
   level with the same meaning (same effect type and ability — Valve reuses talent slugs, so the meaning is
   checked): earlier = the hero gets the effect sooner = buff, later = nerf; `0.5 × type weight` per level
   step, capped at ±1.5. Used when (1) is missing, which covers replacements of **both sides** (13 annotated).
3. The tier total is split between the tier's "replaced with" rows (1 or 2).
Still 0: both sides replaced by brand-new talents (266 in history, 33 annotated tiers with nothing), and thin
data (Chaos Knight 7.40 level 25: 17 picks after).

**Rejected absolute measures** (tested so both-side replacements could be scored): (a) *tier pick timing* — the
average upgrade number at which the tier's talents are taken, relative to all heroes in the same window; (b)
*tier win rate* relative to the hero's level-10 tier. Validation on 900 talent VALUE buffs/nerfs with
unchanged slugs: after a buff the tier is taken earlier in 52 % of cases vs 51 % after a nerf, and the
relative win rate rises in 47 % vs 53 % — no signal in pro data, so neither is used.

## 2026-09-18 — second blind sample, soft ceiling, data sources

**Second agreement test.** New non-overlapping stratified sample of 120 rows, two independent blind judges
(different models, different personas): model vs judge A ρ = 0.40, vs judge B ρ = 0.37, vs their mean
**0.43**; judge A vs judge B **0.55**. So the model reaches about three quarters of the agreement two human-
style judges have with each other. First sample (one judge): 0.34.

**Soft ceiling for one row** (`_compress`): linear up to 1.0 (a typical change), logarithmic above —
1.5 → 1.41, 2 → 1.69, 3 → 2.10, 6 → 2.79; replaces the hard cap 3 for % rows. A halved niche parameter no
longer outweighs a real nerf (Treant 7.41f −7.2 → −6.0). Agreement unchanged (0.33 → 0.35, 0.44 → 0.43).

**Can we live without OpenDota? Mostly.** DEMOS (own replay parses, Tier 1–2, 2024+) has `ability_builds`.
Skill priority from DEMOS vs OpenDota: r = 0.97 on common abilities (120 d). Talent picks for one window
(7.39e): r = 0.87, but DEMOS has ~9× fewer picks (20.8 k vs 181.7 k), so fewer talent tiers pass the
≥ 30-pick threshold. Two limits: DEMOS starts in 2024 (history before that stays on the cached OpenDota
pull, one-off), and DEMOS currently records builds for only 97 of 127 heroes (parser gap, tracked there) —
until fixed, those 30 heroes are topped up from OpenDota. Refresh: `tools/refresh_weights_data.py`
(workflow Step 2c).

## Audit 2026-09-25 — bugs fixed

Every scored row of the 20 annotated patches (7.08, 7.38 → 7.41f; 6 273 scored records) was dumped with its
type, context and score and read by type, by largest score and at random. Fixed:

| symptom | cause | fix |
|---|---|---|
| Tormentor "First Spawn Time 15:00 → 20:00" ×1.3; enchantment rows ×0.76–1.3 | `current_ability_slug` was reset only by `hero_header`: units / items / enchantments / Spirit Bear inherited the previous hero's last ability (ultimate ×1.3 or skill-priority multiplier); 47 scored rows | every entity block resets it (`_open_block`); `ability_change` sets the slug of its own ability |
| reworked abilities, new / reworked facets, item property panes moved neither `w` nor `v` (Solar Crest 7.41, Mage Slayer 7.38: no score at all) | `ability_change`, `new_facet`, `facet_change`, `properties_change` tallied tags with scores (0, 0) — 260 records | scored like the equivalent `li()` rows (`_dyn_record_card`) |
| "Cooldown 30/25/20/15s → 24/21/18/15s" damped ×0.35 as a "tiny change" | the absolute floor read the LAST level (unchanged), the magnitude the last CHANGED level | floor uses the last level that changed |
| "Recipe cost 600 → 400. Total cost unchanged" = ±1.26 (Battle Fury, Orchid, Glimmer 7.41, Witch Blade, Skadi, Halberd …) | total unchanged → recipe % on the hero formula | 0 |
| "Cost 50 → 60" (Clarity) 1.07 vs "Total cost 50 → 60" 0.50 | basic-item cost and recipe-only rows missed the gold scale | same gold delta |
| Glimmer active MS priced as the item's MS stat (−1.10), dominated creep speed (−0.47), Arctic Blast damage (+1.13), Corrosion armor reduction (−0.80) | gold pricing matched the stat keyword anywhere in the parameter name | only the item's own stat line is priced |
| spell "Base Damage" / ability "Move Speed" valued ~2× | signal J inflated by hero base stats (see Signal J refit) | refit |
| "Turn/Cast Speed Manipulation" → move speed, "Attack Rate" → other, a spell's "Health Cost" → gold cost (5 % typical) | classifier gaps | turn_rate / cast_point / attack_speed / health |
| matrix, "Hide old" on: the first visible cell drew a riser from the hidden column's (clipped) level | `dynDrawRowLines` read hidden neighbours | hidden neighbour = axis |

Checked and fine: ultimates are read correctly from the 7.41f KV layout (151 = every
`ABILITY_TYPE_ULTIMATE` in the files, same as 7.41e); every `_dynamics.json` entity is in its roster and every
patch key is in the patch list; signs come from the page tags and agree with `b()`.

**Measured** (blind-judge samples, Spearman ρ of |score| vs grade; judge mean for sample 2):

| | sample 1 (1 judge) | sample 2 (2 judges) |
|---|---|---|
| before | 0.346 | 0.426 |
| J refit only | 0.377 | 0.452 |
| all fixes | **0.402** | **0.461** |

`corr(w, buff − nerf)` per cell 0.839 → 0.850 (the property panes add buff/nerf rows that were 0 before).
Tried and **not** applied (no clear gain): "barrier" → health (ρ +0.003 / 0), count words ("number of",
"bounces", "jumps", "targets") → charges (ρ −0.009 / +0.011). The unclassified share of buff/nerf rows is 4.2 %.

Known data gaps (not code): `data/stats/7.39c|7.41/items.json` are pre-patch copies (17 "Total cost" rows
disagree with the note), so item costs of those versions are the old ones; `talent_tiers.json` has no 7.41f
tiers yet (run `tools/refresh_weights_data.py`).

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
