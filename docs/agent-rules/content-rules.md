# Правила контента патч-страниц

Правила тегирования спецслучаев, фраз, структуры секций, нейтральных предметов и перечислений.

## DEL vs NERF — базовое правило

- `t("DEL")` — **удаление фичи/эффекта/поведения/скейлинга**: «No longer …», «Removed …»
- `t("NERF")` — **количественное ослабление** без удаления механики

Строки с «No longer» → всегда DEL, не NERF. Строки «Level N Talent X replaced with Y» → SWAP (с 2026-09-26; слот остаётся, контент меняется).

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

- **Урон ИЗМЕНИЛСЯ** → в «?» той строки, из которой он следует (владелец 2026-10-04, сравнив Magnus 7.41 строкой и
  Broodmother 7.41b в «?»: «сделай с ?»): `extra=inline_note("Damage at level 1 increased from 55–63 to 56–64")` на
  последней строке Base Strength / Agility / Intelligence / Base Damage (Min / Max) / `attr_change` перед ней в списке,
  иначе на первой такой после неё (Invoker 7.39). У строки с `note_box` — `note_box(...) + inline_note(...)`; своя
  пометка строки урона («Damage spread …») идёт следом через `<br>`. **Остаётся строкой:** у героя с `hero_stat_card`
  (строки скрыты и питают карточку), строка с `wrong-word` и пометкой-поправкой (должна быть на виду), и список без
  такой строки-причины (тогда это и есть изменение). Делает генератор: `fold_damage_l1_src` /
  `_postprocess_fold_damage_l1` (generate_patch_code_v2.py); веса не меняются — `patch/elements._score_folded_damage`
  считает пометку как бывшую строку (без тега). Тесты: `tests/test_damage_l1_fold.py`.
  До 2026-10-04 правило было обратным («отдельная видимая строка», 2026-06-19; вычитка 2026-09-18 вернула строки).
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

## Cost-change rows: все бейджи в конце строки, тег по тому, что платит игрок

Правило владельца 2026-09-26 (образец Octarine Core 7.41f): процентов посреди строки больше нет — каждый бейдж в конце.
`l=True` всегда (цена: меньше = лучше).

| Случай | Строка | Тег |
|---|---|---|
| Recipe сдвинулся, Total не изменился | `b(recipe_old, recipe_new, l=True)` в конце; «Total cost unchanged» без своего % (в тексте или `extra=inline_note(...)`) | по **рецепту**: дешевле = BUFF, дороже = NERF |
| Изменились и recipe, и total | ОДИН бейдж `b([r_old, t_old], [r_new, t_new], l=True, slash=True)` → «+100% / +4%» | по **TOTAL**; `force_overall="buff"/"nerf"` только когда направления разные |
| Recipe не менялся, сдвинулся только total | обычный `b(total_old, total_new, l=True)` | по total |
| Не изменилось ничего | `t("MISC")` | — |

```python
W(li("Recipe cost decreased from 600 to 400. Total cost unchanged at 3900g", b(600, 400, l=True)))   # Battle Fury 7.41 = BUFF
W(li("Recipe cost decreased from 475 to 325. Total cost increased from 1400g to 1500g",
     b([475, 1400], [325, 1500], l=True, slash=True, force_overall="nerf")))                       # Arcane Boots 7.41
W(li("Recipe cost unchanged at 500. Total cost unchanged at 2575g (due to Pavise cost decrease)", t("MISC")))  # Solar Crest 7.41
```

Recipe cost decrease не BUFF, если total вырос. Всегда читать следующее предложение после «Recipe cost».
Код: `generate_patch_code_v2.py` (ветка recipe/total), тесты в `tests/test_generator.py`.

## Рецепт и общая цена — все проценты в конце строки (2026-09-26)

Процент посреди строки больше не ставим (владелец, образец — Octarine Core 7.41f).
- **Изменились рецепт и общая цена** → один значок в конце «рецепт / итог», тег — **по общей цене** (её
  платит покупатель): рецепт дороже, а итог дешевле = BUFF. `force_overall` пишется, только когда
  направления расходятся:
```python
W(li("Recipe cost increased from 200 to 400. Total cost increased from 4900g to 5100g", b([200, 4900], [400, 5100], l=True, slash=True)))
W(li("Recipe cost increased from 450 to 600. Total cost decreased from 4100 to 3900", b([450, 4100], [600, 3900], l=True, slash=True, force_overall="buff")))
```
- **Общая цена не изменилась** → процент рецепта в конце, тег по рецепту (дороже = NERF); у «Total cost
  unchanged» своего процента нет:
```python
W(li("Recipe cost increased from 450 to 800. Total cost unchanged at 2150g", b(450, 800, l=True)))
W(li("Recipe cost decreased from 1350 to 1250", b(1350, 1250, l=True), extra=inline_note("Total cost unchanged at 4500g")))
```
Генератор: `_postprocess_recipe_cost_zero_net` / `_recipe_total_badge`, тесты в `tests/test_generator.py`.
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
ни слова, — отдельная строка «Total cost decreased/increased from A to B» с `b(A, B, l=True)`, без
пояснения (Revenant's Brooch 7.38: 4900 → 3300; подпись «Read from the item's components» убрана 2026-09-27).
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
| Был обычным нейтральным предметом, «Now is a Tier N Neutral Artifact» (7.38) | `item_header("Name", new="Now a Tier N Artifact")` | Active/Passive — строками (как у соседей в списке), не в `inline_note` (владелец 2026-09-27; 17 предметов 7.38) |
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

`show_list(...)` в контенте не используется (0 вызовов в content/p*.py на 2026-10-04; хелпер остался в patch/elements.py). `tests/test_no_showlist_in_extra.py` падает на любом `extra=show_list(`.

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


## Врождённые способности — не в общем списке героя (2026-09-26)

Изменение врождённой («Sticky Fingers: …», «Septic Shock: …») — в её собственном блоке
`W(ability("<name>", slug=..., innate=True))` сразу после списка характеристик, не строкой в нём.
Удалённая врождённая + новая в том же патче → одна карточка `ability_change(old=<удалённая>, new=<новая>)`:
Mental Fortitude → Aggrandize, Mana Magnifier → Special Reserve (7.38), Barracuda → Essence Shift,
Gift Bearer → Summon Spirit Bear, Spectral → Desolate (7.40). Переделка на месте («Gift Bearer: Reworked»)
→ `ability_change` с одинаковым именем. Тексты old/new — из d2vpkr `abilities_english.txt` до/после патча,
числа — из `data/stats/<версия>` KV; не выдумывать. Генератор: `_postprocess_innate_rows_out_of_stats`
(переносит строки, для удаления ставит `# TODO[innate-swap]`).
