# ability_change — правила блока замены способностей

Правила для `ability_change(old, new)` — визуального 2-панельного блока замены/реворка способностей.

## Когда использовать

- Способность заменяется другой (разные имена) — `ability_change(old, new)`
- Innate reworked — ВСЕГДА `ability_change`, никогда не два плоских `t("MISC")`. Генератор (`generate_patch_code_v2.py`) пишет `# TODO[innate-swap]:` / `# v2-todo:` — никогда не оставлять в коммите.
- «Innate ability reworked» в патчноуте: лифтить OLD desc из патча, который вводил текущий innate (`hero_innate_<entity>_<ability>` в `patchnotes_english.txt`). **Никогда не придумывать** — спросить у пользователя, если KV-текст не найден.

## Unified layout (обязателен для всех блоков)

Каждый `ability_change` в 7.41+ использует `summary` + `tag`:

| Ситуация | summary | tag |
|---|---|---|
| old.name ≠ new.name, innate | `"New innate ability."` | `"new"` |
| old.name ≠ new.name, не innate | `"New ability."` | `"new"` |
| old.name == new.name, innate | `"Innate reworked."` | `"rework"` |
| old.name == new.name, не innate | `"Ability reworked."` | `"rework"` |

**Никогда** не писать `"New innate ability replacing X."` или `"<AbilityName> reworked."` — заголовок уже показывает оба имени.

## Layout-режимы

1. **`is-in-place`** — `old.name == new.name` И иконки совпадают. Правая шапка скрывается (показывается только левая). Одна шапка — всегда, когда имя+иконка одинаковые.
   - Sub-mode **`is-new-taller`** — если `new_rows > old_rows`: новая панель `align-self: start`, без лишнего padding-top. Контент плотно к верху.
2. **`compact-old` / `compact-new`** — разная identity И разница строк ≥ 2. Меньшая панель центрируется.
3. **Plain symmetric** — всё остальное.

## Что внутри / снаружи блока

**Внутри `old.desc` / `new.desc`:** только официальное описание способности (как в игре / KV). Никакой отсебятины («Self-buff nerfed:», «Pre-7.41 …»). Включать полный stat summary: Duration, Damage, CD, Mana Cost.

**Снаружи** (после `W(ability_change(...))`): числовые изменения через `W(ul_open())` / `W(li(...))`. Это stat deltas, пережившие реворк.

**Inline-note к новой механике** → приклеивать `+ inline_note(...)` к той строке `new.desc`, которую она поясняет (отдельный элемент `desc=[..., inline_note(...)]` рисуется пустой строкой с одним «?»). Никогда не `W(subnote(...))` после блока — это рендерится ВНЕ карточки.

```python
# WRONG — subnote вне карточки
W(ability_change(old=..., new=dict(desc=["..."])))
W(subnote("Movement slow is 100% for 0.2s."))

# RIGHT — clarification внутри
W(ability_change(old=..., new=dict(
    desc=["... slows movement by 100% for 0.2s ..." + inline_note("Effects linger even if the enemy dies.")])))
W(ul_open())
W(li("Cooldown decreased from 45 to 40", b(45, 40, l=True)))
W(ul_close())
```

## Dedup в desc: что убирать

Внутри `ability_change` desc убирать фразы, которые уже видны из unified-заголовка или innate-маркера:

1. `"Innate. Passive."` → `"Passive."` (маркер уже показывает "innate")
2. `, can't be leveled up` → убрать полностью
3. `, improves with <HeroName>'s level` → убрать когда есть `scale_pill`
4. `(promoted from a regular ability)` / `(promoted from the Aghanim's ability)` → убрать
5. `(reworked from the previous <X>)` → убрать
6. Числовые дельты `"Mana Cost: 50 (was 115)"` → убрать из desc, добавить снаружи как `li(..., b(115, 50, l=True))`

**Выделять жирным** ключевые цифры/термины в desc для визуальной иерархии.

## Per-level formula внутри vs снаружи

- **Внутри** пане — `scale_pill(...)` → `(pill, table)`, pill в текст, table в `tables=[...]`. Compact `levels=[1,5,10,15,20,25,30]` (полная сетка не влезает в полу-ширину).
- **Снаружи** — только текстовый `li("...", t("BUFF"))`, без таблицы.

## OLD desc — источник и форматирование

OLD desc = финальное состояние способности до текущего патча (как реальный тултип). Источник: вводящий патч в `patchnotes_english.txt` + все последующие твики до этого патча. Убирать «Per 7.XX…» и исторические паравраты — только конечный tooltip.

## NEW desc — сохранять неизменённые компоненты

Workflow: **baseline − deltas**, не «написать из 7.41 KV». Всё что патч не удалил/не изменил — остаётся в NEW desc. Типичные упущения: Duration, Spell Lifesteal, пассивная компонента у passive+active способностей.

## Renamed ability + Aghanim's DEL

Когда `ability_change` переименовывает способность (old.name ≠ new.name), грепнуть:
```bash
grep "DOTA_Patch_<ver>_<hero>_<new_slug>" data/patchnotes_english.txt | grep -i "no longer upgraded with aghanim"
```
Если есть — добавить `W(li("No longer upgraded with Aghanim's Shard", t("DEL")))` в `ul` рядом с блоком.

## Slot displacement

Когда regular ability становится innate → другая ability занимает освободившийся слот → в `new.desc` этой способности явно написать:
```python
desc=["Active. Now occupying Inner Beast's old slot (Inner Beast moved to innate).", ...]
```

## Aghanim rows внутри ability_change

Для Aghanim в desc пане — использовать `aghs_line(text)` / `aghs_shard_line(text)` (возвращает full-width div со stripe). Обычный `ul.changes li.aghanim-scepter` auto-classifier не работает внутри swap-панели.

## Innate/facet субgruппа

Изменения innate и facet → всегда под `subgroup("Abilities")`, НИКОГДА под авто-категорией «Other» (первый ul после hero_header). Other — только для base-stat изменений.

**PURE ul** (только ability/facet/innate): `W(subgroup("Abilities"))` до `ul_open()`.
**MIXED ul** (base stats + removals): закрыть stats ul, потом `W(subgroup("Abilities"))` + новый ul.

## Innate-маркеры и версии патча

- **До 7.36** (patch < 7.36): все `ability(...)` → `innate=False` (innate-системы нет).
- **7.36–7.40** (до 7.41): 33 способности стали innate в 7.41 — добавить `innate=False` для этих slug'ов в pre-7.41 патчах.

Список slug'ов, ставших innate в 7.41:
```
ancient_apparition_bone_chill, axe_one_man_army, beastmaster_inner_beast,
centaur_horsepower, chen_zealot, crystal_maiden_glacial_guard,
elder_titan_momentum, enigma_event_horizon, gyrocopter_afterburner,
juggernaut_bladeform, keeper_of_the_light_bright_speed, lina_slow_burn,
meepo_geomancy, mirana_celestial_quiver, morphling_ebb_and_flow,
night_stalker_hunter_in_the_night, nyx_assassin_neuro_sting,
obsidian_destroyer_equilibrium, phoenix_dying_light, rubick_curiosity,
silencer_brain_drain, skywrath_mage_shield_of_the_scion, snapfire_boomstick,
spirit_breaker_bull_rush, sven_wrath_of_god, techies_mutually_assured_destruction,
templar_assassin_inner_peace, tiny_insurmountable, venomancer_poison_sting,
weaver_threads_of_fate, wisp_equilibrium, windrunner_tailwind,
winter_wyvern_eldwurms_edda
```

## Spirit Bear

Spirit Bear (`hero_id 1961`) — не отдельный герой, а юнит Lone Druid. Рендерить через `unit_header("Spirit Bear", ...)` ВНУТРИ секции Lone Druid, после талантов.

7.40 hero-promotion layout:
1. `unit_header(...)` + `kind="Creep-hero"`
2. Один NEW headline li ("Now a Universal melee hero instead of a creep")
3. `properties_change(old=[...], new=[...])` — стат-пейны
4. Umbrella li с `show_list(...)` всех hero-status consequences
5. Ability-order change li с `.ability-order-flow` extra

Merged Gold/XP Bounty строки с одинаковой формулой → один `li_formula("Gold/Experience Bounty changed", ...)`.
