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

## Open / next
1. ~~Items in gold~~ done.
2. ~~Signal J~~ done (now the main source for % rows).
3. ~~Formula rows (F.6)~~ done: per-level rows take the |%| of the last non-zero level (max rank) when its direction agrees with the row's tag; when `b()` flipped the tag by the average (front-/back-loaded, early-game cut, flatten) all levels are averaged.
4. Manual-annotation agreement test (100–150 rows, 3 grades) — review E.8.2.
5. Niche parameters hitting the cap (e.g. "invisibility linger 2s→1s" = −1.83 for Treant 7.41f): consider a lower cap or per-type caps.
