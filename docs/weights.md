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
| context | `valve_weights.json` → `context` | ultimate 1.3 (slugs read from the latest KV `AbilityType ULTIMATE`, 151), ability/innate/scepter/base stat/item 1.0, shard 0.9, facet 0.8, talent 10/15/20/25 = 0.5/0.6/0.7/0.8 (lowered with signal J) |
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

## Items — gold scale (review E.6, done 2026-09-16; every stat since 2026-09-25)

Item rows that move **gold** are scored in gold: `fraction = gold / item cost`, where the gold comes from the
price list below (signal A v2, per patch version, `data/rules/item_stat_prices.json`, %-stats per 1 %) and the
cost is the mean of the item's cost before and after the patch (`data/stats/<ver>/items.json` of the version and
of the previous one; Heaven's Halberd 7.38: 3500 → 2600 = 3050). `net = 0.6 × sign × 5 × fraction` (20 % of
the item's value = 1.0; 0.6 = median hero type weight), **linear** — so the rows of one item add up to
Δ(stat value − cost) — with a safety cap at the whole item (5 × fraction ≤ 5, net ≤ 3.0; no row reaches it).
Until 2026-09-25 the cap was 3 (60 % of the item) and only a few stats were priced.
A row is priced only when its parameter name IS the item's stat line ("Agility bonus", "Bonus Damage", "Mana
Regen"); "Glimmer Bonus Movement Speed", "Dominated Creep movement speed", "Arctic Blast damage", "Corrosion
armor reduction" go through the hero formula. Cost rows: "Total cost unchanged" (in the row or its inline
note) = 0; a basic item's "Cost A → B" and a lone "Recipe cost A → B" are gold deltas like "Total cost A → B".
Items the shop does not sell (Roshan drops, neutral items: `not_for_sale`) have no price.
Examples 7.41f: Infused Raindrops −0.2 mana regen = 47 g of a 225 g item → −0.62; Octarine +200 g of 5000 →
−0.12; Satanic lifesteal 30 → 25 % = 250 g of 5050 → −0.15.

## Item prices — every stat in gold (2026-09-25)

Owner's request: find the gold price of every stat items have, value everything with it, count the item's
cost, decide how to count mana costs, and count a stat that is replaced by a passive (Heaven's Halberd 7.38 lost
+25 % Evasion and got Passive: Damage Block).

**Method** (`tools/fit_item_prices.py`, needs numpy + scipy; reads `data/stats/<v>/items.txt`, else the d2vpkr
history in the weights-model folder; 118 versions 7.08 → 7.41f, ~11 s):
1. *Which KV values are stats* — Valve's own tooltips: `DOTA_Tooltip_ability_<item>_<field>` = "+$armor",
   "%+Slow Resistance" is a line of the item's stat list, the label names the stat. Items no longer in the
   tooltips use the field-name map learned from the same tooltips. Melee/ranged variants (Phase Boots damage,
   Power Treads speed) count at their mean.
2. *Pure items* — purchasable, no active, no ability heading in the tooltip (Aghanim's Scepter's "Ability
   Upgrade"), every non-zero value is a stat line: all basic items, Sange / Yasha / Kaya and their pairs,
   Aether Lens, Octarine Core, Dragon Lance, Butterfly, Vanguard … (67 items in 7.41f, 64 in 7.38). An item
   with an active or another passive carries value we cannot see, so it is not used.
3. *Damage block is a stat*: chance × (melee block + ranged block) / 2 = expected damage blocked per attack
   (Vanguard 60 % × (50 + 25) / 2 = 22.5; Halberd 7.38 60 % × (60 + 30) / 2 = 27).
4. `cost = Σ price × amount` over the pure items: non-negative least squares, squared misses weighted 1/cost.
   Upgrades price what only exists on upgrades: Sange's recipe pays for slow resistance + health restoration.
5. *Weak prior*: a stat that a single-stat basic item sells gets a quarter-weight virtual item at that item's
   rate (Ogre Axe 100 g per Strength …); %-stats without one get the median rate of the anchored %-stats. It
   only decides what the data cannot — the Sange / Kaya families always bring their %-stats together, so only
   the family total is identified and the split is the prior's.
6. Confidence: **anchor** (a single-stat basic item sells it), **fit** (≥ 2 pure items identify it),
   **single** (one pure item), **prior** (only the family total is identified). Unidentified or zero → no
   price → the row keeps the old per-type weight.

| stat | unit | 7.38 | 7.41f | confidence (7.41f) | priced by |
|---|---|---|---|---|---|
| strength | per point | 75.1 | 75.0 | anchor | Gauntlets / Belt / Ogre Axe / Reaver |
| agility | per point | 67.2 | 66.9 | anchor | Slippers / Band / Blade / Eaglesong |
| intelligence | per point | 70.9 | 72.4 | anchor | Mantle / Robe / Staff / Mystic Staff |
| all_stats | per point | 151.3 | 151.3 | anchor | Circlet / Crown / Diadem / Ultimate Orb |
| damage | per point | 56.7 | 56.5 | anchor | Blades / Broadsword / Claymore / Mithril / Demon Edge / Relic |
| armor | per point | 116.8 | 118.8 | anchor | Ring of Protection / Chainmail / Splintmail / Platemail |
| attack_speed | per point | 26.5 | 25.9 | anchor | Gloves / Blitz Knuckles / Hyperstone |
| attack_speed_pct (base) | per 1 % | 25.7 | 18.0 | single | Butterfly |
| move_speed | per point | 15.0 | 15.0 | anchor | Wind Lace |
| move_speed_pct | per 1 % | 31.1 | 32.6 | fit | Yasha, Sange and Yasha, Yasha and Kaya |
| boots_move_speed | per point | 11.1 | 11.1 | anchor | Boots of Speed (does not stack, sold cheaper) |
| health | per point | 2.38 | 2.62 | anchor | Fluffy Hat / Vitality Booster |
| mana | per point | 3.62 | 3.21 | anchor | Wizard Hat / Energy Booster |
| health_regen | per point | 135.8 | 141.1 | anchor | Ring of Regen / Ring of Health / Ring of Tarrasque |
| mana_regen | per point | 217.4 | 234.3 | anchor | Sage's Mask / Void Stone / Tiara |
| magic_res | per 1 % | 40.0 | 48.0 | anchor | Shawl / Cloak |
| evasion | per 1 % | 53.9 | 64.2 | anchor | Talisman of Evasion |
| lifesteal | per 1 % | 50.0 | 50.0 | anchor | Morbid Mask |
| spell_lifesteal | per 1 % | 58.3 | 43.3 | anchor | Voodoo Mask |
| spell_amp | per 1 % | 9.35 | 24.8 | prior | Kaya family |
| slow_res | per 1 % | 17.6 | 19.9 | prior | Sange family |
| status_res | per 1 % | 30.3 | 31.0 | prior | Sange and Yasha |
| restoration_amp (health restoration, "health and lifesteal amp") | per 1 % | 17.6 | 19.5 | prior | Sange family |
| mana_regen_amp | per 1 % | 11.4 | 20.3 | prior | Kaya family |
| manacost_reduction | per 1 % | 25.4 | 25.3 | prior | Kaya and Sange |
| cast_speed | per 1 % | 27.7 | 25.9 | prior | Yasha and Kaya |
| cooldown_reduction | per 1 % | 35.9 | 45.8 | single | Octarine Core |
| cast_range | per point | 2.86 | 3.23 | single | Aether Lens |
| attack_range | per point | 0.94 | 1.90 | single | Dragon Lance |
| aoe_bonus | per point | — | 22.5 | anchor | Chasm Stone (from 7.41) |
| damage_block | per expected blocked damage | 21.9 | 18.2 | single | Vanguard |

Upgrades are more gold-efficient than basic items (Ogre Axe sells Strength at 100 g, the fit says 75 g), so
stats that only exist on upgrades look cheap — most of all **attack range**: Dragon Lance's recipe barely pays
for its extra Strength / Agility, so 10 range ≈ 19 g (Dragon Lance −10 range 7.41: −0.43 → −0.02). No
stable price: `primary_attribute` (Power Treads has an active), `max_mana_pct` (only Null Talisman).

**Applied to item rows** (`patch/weights.py → _item_gold`):
- a priced stat changed ("Strength bonus 26 → 30"), added or removed — property-pane sides ("+20 Strength"
  DEL), "Provides +8 Agility", "No longer provides +12 Health Regen, +6 Mana Regen, or +20 Damage", an aura's
  "now also provides +2.5 Health Regen" (the wearer's share, a lower bound) — `amount × price`;
- "Now provides +8 Mana Regen instead of +50 Damage" (REWORK) — both sides, signed by the gold (Khanda 7.38
  −0.59); a rework row that names only the new side stays sign-less;
- a **Damage Block** passive gained / lost — its chance × block × the damage-block price; numbers from the row,
  else from the KV (`damage_block` in the price file; the previous patch for a removed block). So Halberd 7.38
  counts both sides: −25 % Evasion (−1.32) and +Damage Block (+0.58);
- the **components panel** (`components_change` / `auto_components_change`): the total A → B is scored as a
  "Total cost" row when the item block ends, unless an li() row of the block states the cost itself ("Total
  cost A → B", "Total cost unchanged", "Cost A → B") — that row wins, nothing is counted twice. Not tallied as
  a tag. 7 panels score in the 20 annotated patches (the other 36 have a cost row, an unchanged total or are
  new items);
- an active's **mana cost** — see below.
Everything else (actives, cooldowns, conditional bonuses) keeps the hero formula / NEW-DEL card weight.

**Mana costs — rule**: `gold = |Δmana| × gold per max mana` (last level that changed; "now has a 50 mana
cost" = 50), on the item gold scale. The mana a cheaper active saves is mana you need in the pool when you
press the button — the same thing Valve sells as max mana (3.2 g per point in 7.41f). Items without a price
(neutral items) are measured against `ref_cost`, the median cost of purchasable items with an active (3788 g).
Why not the % (signal J, 1.35 per 1 %): J is Valve's rate for hero spells; applied to "Disarm 75 → 25"
(−67 %) it gave +2.51, the heaviest row of the Halberd rework — worth 1.5 × the item's whole price cut. Data:
- Valve's own price of cheaper spells: Kaya and Sange's 25 % mana cost reduction = 25 × 25.3 = 630 g. A hero
  spends ~500 mana per rotation (median max-level spell 100 mana × 4 spells + an item active, median 100):
  25 % of it ≈ 125 mana ≈ 400 g at the max-mana price — same order as Valve's 630 g. The %-rule valued 25 %
  off ONE item active at ≈ 1.5 (≈ 45 % of a 3000 g item ≈ 1400 g), more than Valve charges for 25 % off
  everything;
- the 18 item mana-cost rows of the annotated patches: median |score| 1.98 → 0.14 (other item rows 0.48); 11
  of the 46 largest item rows were mana costs, now none. Hero spells keep J.

**Heaven's Halberd 7.38** (`w` +0.70 → **−1.43**, volume 8.31 → 9.10):

| row | before | after |
|---|---|---|
| DEL +20 Strength | −0.24 | −1.48 |
| DEL +25 % Evasion | −0.30 | −1.32 |
| DEL +25 % Slow Resistance | −0.27 | −0.43 |
| DEL +25 % Health and Lifesteal Amp | −0.36 | −0.43 |
| NEW +275 Health | +0.21 | +0.64 |
| NEW +6 Health Regen | +0.21 | +0.80 |
| NEW +5 All Attributes | +0.24 | +0.74 |
| NEW Passive: Damage Block (60 % × 60 / 30) | +0.29 | +0.58 |
| components panel: total cost 3500 → 2600 | — | +0.89 |
| Disarm can now be dispelled (NERF) | −0.48 | −0.48 |
| Disarm mana cost 75 → 25 | +2.51 | +0.18 |
| Disarm duration on ranged 5 s → 4 s | −1.11 | −1.11 |

The stat swap plus the price cut nets ≈ 0 (stats −912 g, price −900 g: Valve priced the rework fairly); the
item is a nerf because of the Disarm changes.

**Largest moves** (item cells, net `w`, 20 annotated patches; 147 of 583 item cells change, no hero cell):

| patch | item | before | after | why |
|---|---|---|---|---|
| 7.38c | Pollywog Charm | +2.79 | +0.12 | mana cost 40 → 0 (neutral, vs ref cost) |
| 7.39 | Rod of Atos | −3.17 | −0.53 | mana cost 50 → 100 |
| 7.39d | Outworld Staff | −2.43 | −0.07 | mana cost 40 → 65 |
| 7.41d | Witchbane | +4.29 | +2.04 | mana cost 150 → 50 |
| 7.39 | Gleipnir | −2.41 | −0.26 | mana cost 100 → 150 |
| 7.38 | Heaven's Halberd | +0.70 | −1.43 | see above |
| 7.41e | Veil of Discord | +2.22 | +0.14 | mana cost 50 → 25 |
| 7.38 | Gleipnir | +2.65 | +0.81 | chains mana cost +200 → +100 in gold; +200 Mana priced |
| 7.38b | Glimmer Cape | −4.00 | −2.21 | mana cost 90 → 125 |
| 7.38c | Crippling Crossbow | +1.80 | +0.07 | mana cost 75 → 50 |
| 7.39d | Pavise | +2.00 | +0.32 | mana cost 100 → 60 |
| 7.38 | Abyssal Blade | +1.01 | −0.27 | pane in gold: +16 Str vs −250 HP, −10 regen, −block |
| 7.40 | Ethereal Blade | +0.03 | −1.16 | lost +300 Mana, +3 regen, +250 cast range (priced) |
| 7.38 | Revenant's Brooch | +0.09 | +1.26 | components panel 4900 → 3300 (old stats not listed) |
| 7.41 | Refresher Orb | +2.08 | +0.98 | mana cost 400 → 325 |

**Blind-judge agreement** (Spearman ρ of |score| vs grade, `outputs/agreement*.json`): sample 1 **0.402 →
0.406**, sample 2 (mean of two judges) **0.461 → 0.417**; item rows only: 0.64 → 0.72 (n = 15), 0.51 → 0.27
(n = 21). The sample-2 loss is three item rows the judges grade 2–2.5 that moved from the J scale to the much
quieter gold scale (Pollywog mana 40 → 0: 2.79 → 0.12; Yasha and Kaya mana regen amp −10 %: 1.08 → 0.14;
Abyssal health restoration −4 %: 0.87 → 0.04). Scale, not price: Valve's typical item stat change is 6.4 % of
the item's cost (median of 748 KV changes 7.08 → 7.41f; cost changes 4.0 %), which the 20 % = 1.0 scale turns
into 0.19 while a typical hero change is ~1.0. Calibrating the scale to it (typical change = 1.0, K = 15.6)
gives 0.397 / 0.437 — no clear gain, not applied (open question).

## Items — one scale for stats and actives (2026-09-26)

Two fixes to the item gold scale above (owner: "fix these weak spots yourself").

**1. Actives on the gold scale.** Before, an item row without a gold price (Disarm duration, "can be
dispelled") was scored on the hero scale, ~4x louder than the gold-priced stat rows of the same item, so
Heaven's Halberd 7.38 was "−1.43" almost only because of two Disarm rows. Now such rows are multiplied by
`ITEM_ABILITY_F`. The cost-minus-stats residual cannot measure what an active is worth: upgrades sell their
stats cheaper than basic items (Halberd 7.38: stats 2818 g, item 2600 g; median residual share 0.15, a
quarter of items negative). So K and F were swept on the two blind-judge samples (mean Spearman ρ):

| K \ F | 1 | 0.75 | 0.6 | 0.45 | 0.3 |
|---|---|---|---|---|---|
| 5 (old) | 0.425 | | 0.437 | | 0.421 |
| 7.5 | | | 0.442 | 0.443 | |
| 10 | 0.432 | 0.441 | **0.445** | 0.445 | 0.428 |
| 12.5 | | 0.440 | 0.445 | | |
| 15.6 | 0.431 | | 0.443 | | 0.425 |

A flat plateau (K 7.5–15.6, F 0.45–0.75); the centre K = 10, F = 0.6 is used. It reads as "20 % of an
active = 20 % of half the item" (0.2 × 0.5 × K × W = 0.6). After the price pooling below: sample 1
0.414 → 0.406, sample 2 0.436 → **0.482**, mean 0.425 → 0.444.

**2. No "prior" prices on the site's patches.** Sange/Kaya/Yasha stats (slow resistance, restoration amp,
spell amp, mana regen amp, mana-cost reduction, cast speed, status resistance) always come together in one
patch, but the family ratios change between patches. `fit_item_prices.py` now re-fits such a stat on the
pure items of this and the 3 / 6 / 10 / 15 earlier patches (older items weigh 0.85^age) until the split is
identified — confidence `pooledN`. Every version from 7.35b on is fully identified; "prior" is left only in
7.08–7.35 (not on the site). 7.41f: restoration amp 19.5 → 15.6, mana regen amp 20.3 → 15.6, mana-cost
reduction 25.3 → 18.9, spell amp 24.8 → 28.4, slow res 19.9 → 20.3 g per 1 %.

**Heaven's Halberd 7.38 now**: stats −4.2 g-rows + new +5.5 + price cut +1.77 ≈ +0.1 (the swap is fair),
Disarm dispellable −0.29, mana cost +0.36, ranged duration −0.67 → **−0.49**, a mild nerf.
Largest moves: Orb of Venom 7.38 +3.90 → +0.94, Drum 7.38 −4.71 → −2.76, Crippling Crossbow 7.41 −4.45 → −2.67,
Gleipnir 7.38 +0.81 → +2.17 (priced +200 Mana now counts next to the active), Khanda 7.38 −0.64 → −1.76.

**Row cap = the whole item.** `ITEM_ROW_CAP` is now a share of the item's cost (1.0 = |gold| = cost), not a
score: at K = 10 the old cap (5.0 score) clipped half an item, so Orb of Corrosion 7.38's "+8 Agility" and
"−25 Attack Speed" both read 3.00 and cancelled out (net −3.04 → −3.84).

**3. Against what pros did** (OpenDota Explorer, pro matches `leagueid > 0`, final inventory; 21-day window
before vs after each patch, min 14 days, capped by the neighbouring patch; 18 patches 7.38–7.41f; data and
query in `~/outputs/item-winrate-20260926/`). Item cells with ≥ 30 games on both sides, |score| > 0.05:

| | n | ρ(score, Δlog pick share) | ρ(score, Δ win rate) | same sign, |score| ≥ 1 and share moved ≥ 20 % |
|---|---|---|---|---|
| K 5 / F 1 (before) | 277 | +0.208 | −0.052 | 0.65 (n 31) |
| K 10 / F 0.6 (now) | 285 | +0.203 | −0.057 | 0.62 (n 16) |

Every K/F of the sweep lands at +0.19…+0.22: pro pick share cannot choose the scale, it only confirms the
direction (weakly, p ≈ 0.001). Win rate of the item's holders says nothing (a nerfed item is bought only
where it wins). Where pros disagree most — Heaven's Halberd 7.38 (−0.49, pick share ×4.4), Orb of Corrosion
7.38 (−3.84, ×3.3), Crippling Crossbow 7.41 (−2.67, ×2.1) — the model prices stats and price in gold at
parity, while pros reward a cheaper item that fits more builds, and a reworked passive/active (REWORK row)
scores 0. That is what the score measures (power per gold), not popularity; the gap is documented, not tuned.

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
1. ~~Items in gold~~ done; every stat priced 2026-09-25 (section "Item prices").
2. ~~Signal J~~ done (now the main source for % rows).
3. ~~Formula rows (F.6)~~ done: per-level rows take the |%| of the last non-zero level (max rank) when its direction agrees with the row's tag; when `b()` flipped the tag by the average (front-/back-loaded, early-game cut, flatten) all levels are averaged.
4. ~~Agreement test~~ done (ρ = 0.21, see above) — follow-ups pending decision.
5. Niche parameters hitting the cap (e.g. "invisibility linger 2s→1s" = −1.83 for Treant 7.41f): consider a lower cap or per-type caps.
6. Item gold scale vs hero scale: a typical Valve item change (6.4 % of the item) scores 0.19, a typical hero
   change ~1.0 — within one item an active's J-scored row outweighs its stat rows 4:1. Decide whether to
   calibrate (K = 15.6) or keep 20 % = 1.0.
7. Reworked items whose old stats the notes do not list (Revenant's Brooch 7.38) count only the price cut from
   the components panel; the KV has both stat sets (`tools/fit_item_prices.py` parses them) if a KV-based value
   change is wanted.
