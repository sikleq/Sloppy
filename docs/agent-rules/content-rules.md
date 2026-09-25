# Правила контента патч-страниц

Правила тегирования спецслучаев, фраз, структуры секций, нейтральных предметов и перечислений.

## DEL vs NERF — базовое правило

- `t("DEL")` — **удаление фичи/эффекта/поведения/скейлинга**: «No longer …», «Removed …»
- `t("NERF")` — **количественное ослабление** без удаления механики

Строки с «No longer» → всегда DEL, не NERF. Строки «Level N Talent X replaced with Y» → REWORK (слот остаётся, контент меняется).

## «No longer has a penalty» → BUFF

«No longer» + **negative noun** (penalty, downside, restriction, limitation, damage penalty, cooldown penalty) = BUFF — удаление штрафа это хорошо для героя.

Контр-примеры (остаются NERF/DEL): «no longer applies slow», «no longer grants invisibility».

Расширенное правило: классифицировать по ПРИРОДЕ удалённого, не по «no longer»:
- Удалено **penalty/downside** → BUFF
- Удалено **beneficial mechanic** → NERF
- Удалена **фича целиком** → DEL
- **Consolidation** (отдельное значение влито в общую систему) → MISC

## «No longer levels with X» → REWORK

Innate decoupling от ultimate/talent = структурный реворк прогрессии, не удаление. Ничего не исчезает — только coupling убирается.

## Новая capability → NEW, не QoL

Добавление механической возможности, которой не было: `"Can now be disassembled"`, `"Can now be alt-cast"`, `"Now affects rooted targets"` → `t("NEW")`.

QoL — только для polish существующего действия (без добавления verb/action/option).

## «Can (no longer) be disassembled» → NEW / DEL

| Фраза | Тег |
|---|---|
| `"Can now be disassembled"` | `t("NEW")` |
| `"Can no longer be disassembled"` | `t("DEL")` |

Никогда не `t("MISC")` для этих фраз.

## «No longer has a separate value for incoming heal reduction» → MISC

Консолидация в Health Restoration систему — не удаление эффекта, он работает через unified механику:
```python
W(li("X no longer has a separate value for incoming heal reduction", t("MISC"),
     extra=inline_note("Still reduces incoming heals due to Health Restoration changes")))
```

## BAT — всегда l=True

Base Attack Time: меньше BAT = быстрее атаки = BUFF. Любой BAT row → `b(old, new, l=True)`.

Исключение: `"X Cooldown Reduction"`, `"Cooldown Advance"` — это ЗНАЧЕНИЯ ТАЛАНТОВ, не применять l=True.

## l=True — только для penalty/incoming/self-cost

`l=True` в `b()` = «меньше лучше». Применять только для: cooldown, mana cost, gold cost, BAT, cast point, channel time, recharge, penalty/drawback.

**Не применять** к damage-dealt-to-enemies. «Minimum Damage decreased» (урон по врагам) → `b()` без l=True.

**Применять** к penalty-значениям: «Gold/XP penalty increased from 15% to 20%» → `b(15, 20, l=True)` = NERF.

## Durations — стандартное направление, не l=True

Для большинства durations (buff/channel/summon/стан-на-враге): longer = BUFF → default `b()` без `l=True`. Только для self-debuff/drawback timers использовать `l=True`.

## Back-loaded rescale → NERF

Когда max-rank delta — маленький BUFF (≤12%), но среднее знаковое % по всем рангам отрицательное → **NERF** (авто в `b()`). Зеркало front-loaded правила.

Исключение (manual `force_overall="buff"`): только L1 упал, L2 равен, все последующие выросли.

## «Nx» multipliers → % badge + concrete values

Фраза «Now provides 1.2x the bonus» → `b(1.0, 1.2)` (= +20%) + `extra=inline_note("Self-bonus values: <b>X/Y/Z</b>")`.

## Badge separator

Когда после числа идёт inline badge (`b()` / `bf()` внутри `inline_note`), вставлять ` — ` (em-dash) перед badge:
```python
extra=inline_note("Cast Range increased to 675/700/725/750 — " + b(675, [675, 700, 725, 750]))
```
Не нужно: badge первый в inline_note (без предшествующего текста), badge в `(was X)` скобках, badge в топ-уровневом `li(text, badge)` (там он в своей колонке).

## «Damage at level 1» и «Damage gain per level»

- **Урон ИЗМЕНИЛСЯ** → отдельная видимая строка с `br(x1, x2, y1, y2)`. Не прятать в inline_note.
- **Урон НЕ ИЗМЕНИЛСЯ** → `extra=inline_note("Damage at level 1 unchanged at X")` на строке атрибута.
- **Damage gain per level** — consequence от изменения attribute gain → `extra=inline_note("Damage gain per level decreased...")` на строке атрибута.

## «As a result / Effectively / This means» → inline_note

Consequence-предложения прикрепить к родительскому `li` через `extra=inline_note(...)`, не отдельная строка.

Исключение: если consequence относится к нескольким предшествующим строкам из разных ul → оставить как standalone.

## Creep lifesteal penalty → quantify

«No longer has separate creep values. Follows global lifesteal rules» = NERF:
```python
W(li("...follows global lifesteal rules...", t("NERF"),
     extra=inline_note("Has a 40% penalty against creeps — " + b(100, 60))))
```

## Cost-change rows: тег по TOTAL, не recipe

| Случай | Тег |
|---|---|
| Recipe shifted, Total unchanged | `t("MISC")`, recipe % inline в тексте, total = inline_note |
| Both recipe and total changed | Тег по total badge (BUFF/NERF) |
| Only total changed | Обычный `b()` |

Recipe cost decrease не BUFF, если total вырос. Всегда читать следующее предложение после «Recipe cost».

## Recipe cost changed, total unchanged → BUFF/NERF, % inline (2026-09-25)

«Recipe cost increased from X to Y. Total cost unchanged at Z» → тег по направлению рецепта
(дороже = NERF, дешевле = BUFF), **процент рецепта — сразу после «X to Y»**, в конце строки процента
НЕТ (общая цена не изменилась). Тег — только слово `t("NERF"|"BUFF")`:
```python
W(li("Recipe cost increased from 450 to 800 " + b(450, 800, l=True) + ". Total cost unchanged at 2150g", t("NERF")))
W(li("Recipe cost decreased from 1350 to 1250 " + b(1350, 1250, l=True), t("BUFF"),
     extra=inline_note("Total cost unchanged at 4500g")))
```
Генератор делает это сам (`_postprocess_recipe_cost_zero_net`), тесты в `tests/test_generator.py`.
Рецепт *и* общая цена не изменились → `t("MISC")`.

## Числа способности предмета — строкой, не в карточках (2026-09-25)

Стоимость маны / перезарядка / длительность / радиус **активки или пассивки предмета** — это не
характеристика предмета. В карточки `properties_change` не попадают, остаются обычной строкой:
`W(li("Eternal Chains Mana Cost decreased from 200 to 100", b(200, 100, l=True)))` (Gleipnir 7.38).
Генератор: `_ABILITY_NUMBER_RE` в `_postprocess_properties_change`.

## Характеристики переделанного предмета — только карточками (2026-09-25)

У предмета с блоком компонентов (`changed=True` / «Item Reworked» / «Recipe changed») ВСЕ изменения
его бонусных характеристик — в `properties_change`, не строками:
- «Now provides +8 Mana Regen instead of +50 Damage» → old `("DEL", "+50 Damage")`, new `("NEW", "+8 Mana Regen")` (Khanda 7.38);
- «Provides +35 Damage and +16% Spell Lifesteal» → new-карточка; старые значения — из подсказок игры
  прошлого патча (d2vpkr), генератор оставляет `# TODO` (Revenant's Brooch 7.38: было +70 / +20%);
- «No longer provides +6 Health Regen» → old `("DEL", ...)` (Nullifier 7.41).
В карточку идёт только настоящая характеристика (`_ITEM_STAT_NAME_RE`: Damage, Mana Regen, Spell Lifesteal…);
«Empower Spell bonus damage 150 → 250» — число способности, остаётся строкой.
У предметов без изменения рецепта характеристики по-прежнему идут обычными строками.

## Цена предмета, которой нет в патчноуте → своей строкой (2026-09-25)

Если у предмета с блоком компонентов итоговая цена изменилась в файлах игры, а в патчноуте про цену
ни слова, — отдельная строка «Total cost decreased/increased from A to B» с `b(A, B, l=True)` и
`inline_note("Read from the item's components")` (Revenant's Brooch 7.38: 4900 → 3300).
Генератор: `_postprocess_unstated_total_cost`; у 7.39c/7.41 KV-снимок до патча, поэтому новая цена
берётся из следующей версии (`_next_version`).
Число способности предмета («Cleave damage to heroes 70% → 60%», Battle Fury 7.38) — строкой, не в карточке.

## «does not stack with …» → в «?» строки Passive/Active (2026-09-25)

Пояснение «Armor reduction does not stack with its components, Desolator…» сразу после строки
«Passive: …» — это сноска к способности: `info_tip(...)` в конце её текста, отдельной MISC-строки нет
(Orb of Corrosion 7.38). Генератор: `_postprocess_stack_note_into_ability`.
У переделанного предмета старые/новые бонусные характеристики — карточками `properties_change`;
старые значения брать из подсказок игры тех лет (d2vpkr abilities_english), не выдумывать.

## Порядок строк в properties_change

Совпадающие строки (присутствуют в обоих пейнах old и new) — **первыми**. Строки только в old (DEL) или только в new (NEW) — после.

```python
# ПРАВИЛЬНО: совпадающая пара (+22→+35) первая, DEL-только строки после
properties_change(
    old=[("BUFF", "+22 All Attributes"), ("DEL", "+250 Health"), ("DEL", "+250 Mana")],
    new=[("",     "+35 All Attributes",  b(22, 35))])

# НЕПРАВИЛЬНО: DEL строки первыми, совпадающая пара в конце
properties_change(
    old=[("DEL", "+250 Health"), ("DEL", "+250 Mana"), ("BUFF", "+22 All Attributes")],
    new=[("",    "+35 All Attributes", b(22, 35))])
```

Если строки только в new (NEW-only), добавлять `None` в old для выравнивания не нужно — паддинг автоматический. `None` используется только для ручного сдвига строки вниз (редкий случай).

## Drop «Now requires X» после auto_components_change

После `W(auto_components_change(name, version))` убирать текстовые строки «Now requires X», «No longer requires X», «Now requires X instead of Y» — они дублируют визуальную components-change панель. Оставлять только cost-summary строки.

## Порядок секций патча

```
1. section("General Updates")
2. section("Item Updates")
3. section("Neutral Creep Updates")     ← creeps ДО neutral items
4. section("Neutral Item Updates")
5. section("Hero Updates")
```

## Нейтральные артефакты — заголовок

| Случай | Вызов | Body строки |
|---|---|---|
| Новый (никогда не был) | `item_header("Name", new="New Tier N Artifact")` | Active/Passive → `t("NEW")` |
| Возвращается | `item_header("Name", new="Returning Tier N Artifact")` | Active/Passive → `t("NEW")` |
| Уже в ротации, твик | `item_header("Name")` без `new=` | Обычные теги |
| Выходит из ротации | `item_header("Name")` + DEL строка | |

**Dormant Curio строки** — всегда `extra=inline_note(...)` на соответствующей строке, никогда отдельным `li`.

## Нейтральные крипы — ability() блоки

Изменения способностей крипов рендерить через `ability()` (как hero abilities), не плоским текстом:
```python
W(unit_header("Satyr Mindstealer", _NC_CDN + "satyr_soulstealer.png"))
W(ability("Mana Burn", icon_url="../icons/abilities/satyr_soulstealer_mana_burn.png", innate=False))
W(ul_open())
W(li("Target's intelligence multiplier decreased from 2/2.5/3/4x to 1/1.5/2/2.5x",
     b([2,2.5,3,4],[1,1.5,2,2.5])))
W(ul_close())
```

Убирать префикс с именем способности из li() текста — он уже в заголовке.

Теги с POV крипа (не игрока): Mana Burn intelligence multiplier ↓ = крип ослаблен = NERF.

**Иконки крипов** (известные): `alpha_wolf_command_aura.png`, `satyr_soulstealer_mana_burn.png`, `satyr_trickster_purge.png`, `dark_troll_warlord_raise_dead.png`.

## Perечисления → info_tip (не inline_note)

Списки именованных сущностей (способности, предметы, фасеты, герои) → `info_tip(...)` с заголовком:
```python
extra=inline_note(info_tip("Facet A", "Facet B", "Facet C", header="Affected facets:"))
```

`show_list` помечен как устаревший на 7.41 патче — используется только для Spirit Bear consequences (одно исключение).

## Tag-order сортировщик — per-UL, merge related uls

Сортировщик `_sort_changes_li` работает per-`<ul>`. Если родственные строки разделены на несколько ul без subgroup между ними, тег может «застрять» между чужими. Фикс: объединить в один ul.

Оставить раздельные ul только для реально разных топиков (кладбище / курьер / иллюзии; Roshan vs Tormentor subgroup'ы).

## Aghanim upgrade строки — merge

Когда KV разбивает Aghanim upgrade на title + description:

| Title строка | Правильная li |
|---|---|
| `"Now upgraded with Aghanim's Scepter"` + description | `"Aghanim's Scepter: <description>"` + `t("NEW")` |
| `"Aghanim's Scepter upgrade reworked"` + description | `"Aghanim's Scepter reworked: <description>"` + `t("REWORK")` |

Tag всегда `t("NEW")` для новых; `t("REWORK")` для reworked. Multi-sentence details → join с `. ` в один li. Уточнения → `extra=inline_note(...)`.

## Aghanim rework — не прятать desc в inline_note

```python
# WRONG
W(li("Aghanim's Shard Reworked", t("REWORK"), extra=inline_note("Applies 3 Fury Swipe stacks…")))

# RIGHT
W(li("Aghanim's Shard reworked: Applies 3 Fury Swipe stacks to each affected enemy", t("REWORK")))
```

`inline_note` — только для ДОПОЛНИТЕЛЬНЫХ уточнений, не для самого описания реворка.
