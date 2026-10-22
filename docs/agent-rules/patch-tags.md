# Patch-теги и строки изменений

Правила тегирования (`b()`/`t()`/`bf()`), порядка строк и канонических фраз для патч-страниц (`builders/build_patches.py`).

## Хелперы для строк изменений
- `b(old, new, l=False)` — числовой бейдж в %. `l=True`: меньше = лучше (cooldown, mana cost, BAT, gold cost, penalty, channel time, recharge, cast point)

**Overall direction для массивов (b() и bf()):** знаковое среднее по всем уровням/рангам включая нули. Нули включаются в знаменатель (честное среднее, не только non-zero пики).

**`bf()` — два бейджа** когда L1 и L30 дают разный знак: `start` / `end` лейблы. Левый тег по avg-знаку.

**Flatten rescale** (список → одно плоское значение): тег по сравнению плоского со средним старых. Flat ≥ avg → BUFF; flat < avg → NERF. l=True инвертирует. Перекрывает max-rank правило.
  - **Исключение**: «X Cooldown Reduction», «X Mana Cost Reduction», «Cooldown Advance» — это **значения талантов**, НЕ применять l=True
  - **Общий тег — по МАКС-уровню** (последний ненулевой ранг). Два авто-уточнения:
    - **Front-loaded рескейл:** макс-ранг — мелкий нерф (≤12%), но среднее знаковое % положительное (ранние баффы перевешивают незначительный поздний минус) → **бафф** (Riki Blink Strike 15/30/45/60→25/35/45/55 = +67/+17/0/−8).
    - **Back-loaded рескейл (зеркало):** макс-ранг — мелкий бафф (≤12%), но среднее знаковое % отрицательное (ранние нерфы перевешивают незначительный поздний плюс) → **нерф** (Kez Kazurai Katana DPS 5/7/9/11→3/6/9/12% = −40/−14/0/+9, avg −11.25%). Disseminate (−20/−4/+7/+14, макс +14 > 12%) остаётся баффом по макс-рангу.
    - **Сплющивание (список → ОДНО плоское значение):** скейл по уровню убран. Тег по сравнению плоского значения со **средним старых**: **бафф, если новое ≥ среднего** (тай → бафф — ранние уровни всё равно выросли: Drow Agility 4/8/12/16→10, среднее 10=10 но L1/L2 поднялись; SF MR 5/10/15→10). `l=True` инвертирует сравнение. Перекрывает макс-ранг для flatten (макс-уровень не вся картина, когда остальные уровни сдвинулись в другую сторону). Если плоское < среднего → нерф (Spirit Bear HP 1100/1400/1700/2000→1500: 1500<1550).
    - Обратный случай (ранний нерф/поздний бафф, Disseminate) не затронут. Вручную `force_overall="buff"/"nerf"` — переопределение. Пер-уровневые % не меняются.
- `br(old_min, old_max, new_min, new_max)` — для range-значений (по midpoint)
- `bf(old_fn, new_fn, formula_text)` — формульные изменения, возвращает `(trigger, badge, table)`
- `t("BUFF/NERF/REWORK/MISC/QoL/NEW/DEL")` — текстовые теги
  - `NEW` (фиолет): считается buff в фильтре (`data-overall=buff`)
  - `DEL` (красный с зачёркиванием): считается nerf в фильтре (`data-overall=nerf`). Для удалений: «Facets removed from the game», «Item removed from the game»
- `bstat_h(hero_display, field, patch_before, delta, l=False)` — авто-бейдж из stats DB. Если стат не найден — fallback на `t("BUFF/NERF")`
- `bstat_i(item_display, field, patch_before, delta, l=False)` — то же для предметов
- `note_box(text)` — бокс «NOTE: …» для авто-добавок (например «From 17 to 18» когда патчноут не указал базовое значение). Использовать через `extra=note_box(...)` в `li()`
- `subnote(text)` — мелкий серый текст со стрелкой ↳, для **официальных** доп. инфо из патча («Damage at level 1 unchanged at 49-59», «Pressing ALT key will show base value...»). Закрывает changes ul; после неё нужен `ul_open()` если будут ещё изменения
- `info_li`/raw `<li>` — НЕ использовать
- `attr_change(old, new)` — смена основного атрибута героя («Is now a Universal Hero»): `W(li(attr_change("Agility", "Universal"), t("REWORK")))` → «Main attribute changed from **Agility** → **Universal**»: названия жирным, шрифтом строки, в цвет атрибута (без иконок). Старый атрибут — из снапшота статов до патча (`data/stats/<prev>/heroes.json`, `AttributePrimary`); генератор делает это сам.
- `creep_ref(name, icon, count)` — юнит внутри строки: маленькая иконка + имя жирным.
- Состав **одного** лагеря — прямо в той же строке через `creep_ref`, без таблицы и без отдельной строки «The camp consists of»: `W(li("Prowlers have returned as an Ancient Neutral Camp: " + creep_ref("Ancient Prowler Acolyte", _NC_CDN + "prowler_acolyte.png", 2) + ", " + creep_ref(…), t("NEW")))`.
- Размеры лагерей называем как в игре (`DOTA_NeutralCamp_Name_*`): **Small / Medium / Large / Ancient**, не Easy/Hard (Valve в патчноутах пишет Easy/Hard — заменяем).
- `camp_table([(camp, [(count, name, icon), …]), …])` — **состав нескольких лагерей — лёгкой таблицей** с тонкими полупрозрачными линиями внутри строки (колонки крипов выровнены по вертикали), не списком в «?» и не строкой через запятую: `W(li("These camps consist of the following creeps" + camp_table([("Easy camp", [(3, "Pollywog", _NC_CDN + "tadpole.png")]), …]), t("NEW")))`.
- Карта-юниты со своей страницей (Roshan, Tormentor): `unit_header(..., general=False, track=True)` — трекаются и в General Updates; Roshan в Unit Changes → колонка Other, Tormentor — по карточке на structures.html.
- **Стрелки в контенте — только HTML-сущностью `&rarr;`**, никогда литеральным «→»: консоли PowerShell 5.1 / cp1251 его портят.

## Порядок строк внутри `ul` (системное правило)

Все `W(li(...))` внутри одного `ul_open()` … `ul_close()` блока **сортируются по типу тега** (любая сущность — герои, предметы, чары, способности, нейтралы). Порядок — один, ниже в «Авто-сортировке»: NEW → REWORK/SWAP → BUFF → NERF → DEL → QoL → MISC → без тега. (Старый список «числовые бейджи первыми, потом NEW…» устарел и убран 2026-10-16: код давно ставит NEW выше BUFF/NERF.)

Применять даже если в исходном патчноуте Valve порядок другой. Примеры в коде: Crippling Crossbow, Jidi Pollen Bag, Crude.

### Авто-сортировка (per-ability, не нарушать)

Канонический порядок `<li>` строк внутри **каждого** `ul_open()`/`ul_close()` блока (= внутри одной способности / talents subgroup / hero-stat ul; сортировщик НЕ пересекает границы способностей):

1. **NEW** (rank 1) — `t("NEW")`
2. **REWORK / SWAP** (rank 2) — `t("REWORK")`, `t("SWAP")` (талант заменён другим) / raw `badge rework`
3. **BUFF** (rank 3) — `b()` / `bf()` / `bstat_h()` / `li_formula` с overall=buff, или `t("BUFF")`
4. **NERF** (rank 4) — numeric с overall=nerf, или `t("NERF")`
5. **DEL** (rank 5) — `t("DEL")`
6. **QoL** (rank 6) — `t("QoL")` (отдельный ранг ПЕРЕД MISC, чтобы QoL группировался, а не перемешивался с MISC)
7. **MISC** (rank 7) — `t("MISC")`
8. **Untagged** (rank 8) — структурные/описательные строки, остаются в хвосте

**Применяется автоматически** через `_sort_changes_li(html)` (в `save_html()` post-processing) → `_li_rank(li_html)`. Stable sort: внутри одного rank'а порядок исходника сохраняется (обычно Valve KV order). **Вручную переставлять `W(li(...))` не нужно** — пиши в удобном порядке, билд нормализует. Применяется ко всем патчам автоматически (7.08 → текущий).

Скипается для `<ul>` с `class="ability-row"` (Passive:/Active:/Toggle:/Aura: item-описания — там авторский визуальный порядок). `ability_change` panel получает `data-tag="new del rework"` отдельно (это `<div>`, не `<li>`).

## Группировка предложений из патчноутов в одну строку

Valve в KV-файле часто разбивает одно изменение на несколько последовательных ключей. Если несколько подряд идущих предложений описывают **одно изменение** или его уточнения — объединять в **один `<li>`** через ". " в desc, а не делать отдельные строки.

Главное правило: **subnote — это ИНФО (б)**, основная строка — это **change (а), может содержать несколько предложений**.

Пример из 7.41 Global Changes:
```python
# (а): три предложения, описывающие одно изменение innate ability scaling
W(li("All innate abilities that used to scale with other abilities now either provide unchangeable bonuses or improve on 'per level' basis. Abilities that improve with hero level have base value and increment value. Some also have amount of levels required for increment", t("REWORK")))
W(ul_close())
# (б): info — пояснение
W(subnote("Abilities that improve each level provide their increment value at level 1"))
```

Аналогично subnote сам может содержать несколько предложений из патчноута (например связанные «Now offlane... Safe lane... Both of these changes...» → один subnote).

## Свойства новой сущности — одна строка на каждое (системное правило)

Когда сущность (предмет, артефакт, чара, способность, фасет) **появляется новой** и её бонусы перечисляются в патчноуте через запятые («Provides X, Y, and Z» / «Bonuses: …») — каждое свойство должно быть **отдельным `W(li(...))`**, а не объединено в одну строку через запятые.

Дополнительно: **слово «Provides» в начале строки нужно убирать** — оно избыточно, строка и так показывает свойство.

Исключение: если «Provides» — часть предложения (не начальный prefix), оставить.

```python
# WRONG
W(li("Provides +5% Max Health, +1.5% Max Health Regen, -30% Attack Speed", t("NEW")))

# RIGHT
W(li("+5% Max Health", t("NEW")))
W(li("+1.5% Max Health Regen", t("NEW")))
W(li("-30% Attack Speed", t("NEW")))
```

Исключение: если «Provides» — часть естественного предложения внутри описания (например `"Tomo'kan Ringcap: Passively Provides +2 Intelligence. Can be consumed to…"`) — оставить.

**Покраска штрафа красным.** В property-листингах (строки с `t("NEW")` без числового badge'а) у негативных свойств **слова стата красим**, цифры оставляем обычным цветом:

```python
W(li("-1.5/2.25/3 <font color='#e03e2e'>Health Regen</font>", t("NEW")))   # penalty: красим Health Regen
W(li("-30% <font color='#e03e2e'>Attack Speed</font>", t("NEW")))          # penalty: красим Attack Speed
W(li("-20% <font color='#e03e2e'>Vision</font>", t("NEW")))                # penalty: красим Vision
```

Красить только **настоящий** штраф: `-18% Base Attack Time` это бафф (быстрее атаки) — оставить обычным; а вот `-20% Vision` — реальный минус, красить.

**Не красить** в строках с числовым `b()` badge'ом — там бейдж уже даёт цветовую индикацию (например `Intelligence Penalty increased from 5% to 6%` с `b(5, 6, l=True)` уже показывает красный `+20%` справа — повторная подкраска избыточна).

## Сводная таблица b() направления (l=True)

`l=True` применять к: cooldown, mana cost, gold cost, BAT, cast point, channel time, recharge, penalty/drawback, incoming damage, damage taken, damage vulnerability, building damage penalty.
Также (2026-09-18): disable range/radius/duration (радиус, где враг отключает пассивку), damage/attack interval,
flight time, self-stun, «X loss/reduction» (slow resistance loss, intelligence reduction), creep penalty, max mana
penalty, mana per second (расход), health cost, damage threshold. **Не** применять к вражеским значениям:
slow/DPS per cooldown, max slow, magic resistance bonus, search radius. `bstat_h` рисует свой бейдж: никогда
`t("MISC") + bstat_h(...)`, и версия в нём — предыдущий патч, не текущий.

**НЕ применять** к: damage dealt to enemies, durations (buff/debuff/stun на враге — longer = BUFF), talent value rows ("X Cooldown Reduction", "Cooldown Advance").

**Penalty-значения** (gold/XP reduction, lifesteal penalty, stack penalty) → `l=True`: higher penalty = worse for player = NERF.

**Durations** — стандартное направление (longer = BUFF) для buff/channel/summon/стан-на-враге. l=True только для self-debuff/drawback.

## Канонические фразы и спецслучаи тегов

### DEL vs NERF — базовое правило

`t("DEL")` — удаление фичи/эффекта/поведения. `t("NERF")` — количественное ослабление.

«No longer …» → всегда DEL. «Level N Talent X replaced with Y» → SWAP (с 2026-09-26). «No longer levels with X» (innate decoupling) → REWORK (эффект остаётся, только coupling убирается).

### Аудит 2026-10-05 (проверено на самом генераторе; правила в `CANONICAL_TAGS` / `LOWER_IS_BUFF`)
- «X is no longer affected / increased by AoE bonuses» → **DEL** для всего класса (было то NERF, то DEL).
- Время на игровых часах («First Spawn Time increased from 15:00 to 20:00», «siege creep timing 35:00 to 30:00») →
  **REWORK** без % («где и когда появляется объект»; процент от времени на часах ничего не значит).
- Время драфта («All Pick drafting time … 30s to 25s») → **MISC**: часы одни на обе команды.
- «Now costs N mana» → **NERF** (новая цена); «Now can't use more than N» → **NERF** (новый потолок).
- Меньше — лучше: forage time, Vanish Radius (Blur), «Time Until Max …»; награда за юнита героя (Spirit Bear,
  Tempest Double) — враг получает её за убийство. Награда нейтрала — больше = лучше. «Allied/Self Damage» (Luna) — не
  урон по себе.
- «Attack Damage Reduction» в генератор не внесено: у Jakiro (Double Trouble) это штраф себе (меньше — лучше), у
  дебаффов на врага — наоборот. Ставится руками.
- Рецепт изменился, итог тот же: бейдж «−9% / 0%» — `b([рецепт_было, итог], [рецепт_стало, итог], l=True,
  slash=True)`, серый 0% у итога, тег по рецепту (владелец 2026-10-05, Hydra's Breath 7.41f). Итог Valve не назвал
  (7.38b Heaven's Halberd) — берётся ItemCost из файлов игры.
- Списки разной длины в `b()`: b() сравнивает попарно и молча отбрасывает лишнее. Новый тир в конце («+125/135 →
  +125/135/145») — старый список дополняется последним значением (генератор делает сам). Тиры сдвинулись («4/5 → 2-4»)
  — бейдж по общему тиру + `inline_note` «Tier 4, the only tier in both». Бесплатный первый уровень (Night Stalker
  7.38) — сравнение по вложенным очкам. Тест `test_badge_lists_of_different_length_are_reviewed`.

### Снятое собственное ограничение → BUFF; добавленное → NERF (вычитка 2026-09-18)
«Toggling is no longer disabled by silence», «Can no longer be interrupted by casting X», «no longer interrupts
movement», «Now can be cast without cancelling X», «No longer has reduced/fixed X», «no longer freezes/loses X»,
«requirement … removed» → **BUFF**. Свой buff/debuff «no longer dispellable» → **BUFF**; «is now dispellable»,
«is now disjointable» → **NERF**. «Now only affects…», «now has a 0.3s cast point», «now ends if…», «may only
trigger…», «now disabled by roots» → **NERF**. «no longer stealable / benefits from / blinks / has an alt-cast» → **DEL**.
«Now an Agility Hero», «Now X's ultimate ability», «is now innate» → **REWORK**. Всё это в `CANONICAL_TAGS`
генератора и покрыто `tests/test_generator.py`.

### «No longer has a X penalty» — это BUFF, не DEL

Default-эвристика `no longer` → NERF/DEL **не работает** для строк, где удаляется **штраф** (penalty / downside / restriction / limitation). Удаление штрафа = бафф для героя.

Триггер-существительные: `penalty`, `downside`, `restriction`, `limitation`, `damage penalty`, `cost penalty`, `cooldown penalty`. Генератор `generate_patch_code_v2.py` это уже спецкейсит: в таблице регэкспов тегов BUFF-правило «removing a penalty» стоит раньше DEL.

Контр-примеры (остаются NERF/DEL): «no longer applies slow», «no longer grants invisibility», «removed from the game».

### KV-строки с суффиксом `_info` — это `inline_note`, не отдельный li

В `data/patchnotes_english.txt` Valve явно помечает уточняющие строки суффиксом `_info` (например `_talent_2_info` поясняет содержимое `_talent_2`). Такие строки **никогда** не должны эмититься как отдельный `W(li(..., t("MISC")))` — только как `extra=inline_note(...)` к предыдущей строке.

Реализовано в `generate_patch_code_v2.py` (поле `_info` → `inline_note` на текущей строке, см. докстринг в начале файла) для всех hero-веток (`hero_base`, `hero_ability`, `hero_talent`, `spirit_bear`, `spirit_bear_talent`, `general`, `item`). Если у предыдущей li уже есть `extra=inline_note(...)`, новый текст дописывается через `<br>`.

При написании руками: если две KV-строки идут подряд и вторая начинается с уточняющих оборотов («Same behavior as before», «1 X per Y», «Buff Duration: …», «Affects …», «Pressing ALT shows …», «Duration decreased as part of comprehensive Disables Reduction») — это `_info`, прицеплять `extra=inline_note(...)`.

### «Aghanim's Shard reworked» — суть реворка НЕ прятать в `inline_note`

Если строка изменения = только заголовок («Aghanim's Shard Reworked» / «Aghanim's Scepter reworked» и подобное), а **что именно** изменилось спрятано в `extra=inline_note(...)` — **вытащить описание в основной текст строки** и совместить через двоеточие:

```python
# WRONG — суть реворка спрятана в info
W(li("Aghanim's Shard Reworked", t("REWORK"), extra=inline_note("Applies 3 Fury Swipe stacks to each affected enemy")))

# RIGHT — описание в самой строке (каноничный вид, строчная "reworked")
W(li("Aghanim's Shard reworked: Applies 3 Fury Swipe stacks to each affected enemy", t("REWORK")))
```

Прятать содержимое реворка нелогично (Valve так делает в KV, но на странице это плохо читается). Канон по сайту — `"Aghanim's Shard reworked: <описание>"` (строчная `reworked`, см. ~15 героев в коде). `inline_note` оставлять только для **дополнительных** уточнений (edge-cases), не для самого описания реворка.

### Pool-style строки («X now consists of A, B, C») → показать kept + removed

Когда патч пишет «новый пул такой-то», текст скрывает что **удалили**. Перед написанием строки грепать прошлые патчи (facet-определения, прошлые пулы) и диффить — определить выпавшие элементы. Рендерить две группы chip'ов: в `inline_note` сначала «In pool:» с оставшимися, потом «Removed:» с выпавшими (с модификатором `.removed` — strike-through + красная рамка + grayscale иконки).

Helper: `souvenir_chip(name, slug, removed=False, tooltip=None)` → `<span class="enchant-chip souvenir-chip">` (pill с рамкой). `removed=True` → opacity 0.55 + grayscale **только на `> img` и `> span`** (НЕ на самом чипе, иначе tooltip popup `::after` тоже затемняется и становится плохо читаемым; явное правило `.removed::after { opacity: 0 }` + `.removed:hover::after { opacity: 1 }` сохраняет видимость подсказки). **Никакого strike-through.** Группы `.souvenir-group` — горизонтальный flex-ряд, разные группы на разных строках (каждая group block-level). Иконки — из `OneDrive/Desktop/panorama/images/spellicons/<slug>_png.png` → копировать в `Sloppy/icons/abilities/<slug>.png`. Пример: Ringmaster Dark Carnival Barker 7.41 (выбросили Crystal Ball + Weighted Pie).

**Фильтр:** если строка структурно REWORK, но содержит удаления (часть пула выпала), передавать `force_tag="rework del"` в `li(...)` — видимый бейдж остаётся REWORK, но строка попадает и в DEL фильтр для пользователей, отслеживающих удаления.

Главный текст строки описывает структурную суть («Souvenir pool unified across both Dark Carnival facets»), не перечисляет имена — это работа `inline_note`.

### «No longer has a separate value for incoming heal reduction» → MISC

Когда патчноут говорит, что заклинание `no longer has a separate value for incoming heal reduction` — это **MISC**, не DEL. Эффект не удалён, просто переехал в общую Health Restoration систему. Канон (Cold Attack, Soul Release, Pudge Rot и т.д.):

```python
W(li("X no longer has a separate value for incoming heal reduction", t("MISC"),
     extra=inline_note("Still reduces incoming heals due to Health Restoration changes")))
```

Использовать `inline_note` (на той же `<li>`), не отдельный `subnote`.

### Innate ability reworked

Когда патчноут говорит `"Innate ability reworked"` — это **обязательно** `ability_change(...)`, не две плоские `t("MISC")` строки. Старое описание лифтится из патча, который ввёл текущий innate (грепать `hero_innate_<entity>_<ability>` в `patchnotes_english.txt`). Генератор `generate_patch_code_v2.py` пишет маркер `# TODO[innate-swap]:` (когда innate сменился) — никогда не оставлять его в коммите.

### Иконки-чипы → нужны hover-тултипы (если рядом нет пояснения)

Когда строка показывает список иконок-чипов (предметы, способности, сувениры и т.п.), каждый чип должен нести `data-tooltip="..."` с описанием эффекта, **если** рядом с чипом нет inline-текста, объясняющего что он делает.

- **Тултип нужен**: чип = иконка + имя (Ringmaster Dark Carnival souvenirs — игрок не знает, что делает «Funhouse Mirror»).
- **Тултип НЕ нужен**: рядом уже есть текст эффекта (раздел **Enchantment Changes** — у каждой чары перечислены бонусы рядом с чипом).

HTML-escape тултип через `_html.escape(text, quote=True)`. CSS `.enchant-chip[data-tooltip]::after` уже стилизует popup.

## Новая механика целиком — метка в заголовке, без чипа NEW на каждой строке

Если блок описывает **совсем новую механику** (7.38 Wandering Waters, Shrines of Wisdom, Lotus Pools, крафт нейтралок, Flooded Camps), то пометку NEW ставят один раз, в заголовке:
`W(plain_header("Wandering Waters", new="New mechanic"))` или `W(subgroup("Lotus Pools", new="New mechanic"))`.
Строки при этом так и пишутся с `t("NEW")`: тег нужен фильтру и динамике. Но на странице NEW-строки блока показываются описанием механики: одна мягкая рамка, текст абзацами, без чипов и без маркеров-точек (`patch/page.py` `_new_mech_rows`, классы `mech-desc`). Строки с другими тегами (MISC, DEL, REWORK…) свой чип сохраняют — так видно, что в новой механике «не новое».

- Новый блок: `new="New objective"` для объектов карты (здания, святилища, руны, боссы — раздел Map Objectives), `new="New mechanic"` для остального. Генератор ставит метку сам (`_postprocess_new_block_label`), если первая строка блока объявляет новое («replaced with new buildings» и т.п.).
- Значение, растущее со временем игры (`36 + (9 per 5 minutes)`), в строке «from A to B» — `li_formula` с таблицей по минутам (`lambda M: 36 + 9 * (M // 5)`, `level_fmt=lambda M: f"{M}:00"`). Генератор: `_postprocess_minute_formula`.

## Уроки вычитки 7.38: объекты карты (правило → почему)
- **Старая подсказка способности — не выдумывать.** Брать из истории файлов игры: `dotabuff/d2vpkr`, `dota/resource/localization/abilities_english.txt` на коммите до выхода патча (`gh api repos/dotabuff/d2vpkr/commits?path=…&until=<дата патча>`). Старые числа сверять с историей вики. *Почему:* старая панель карточки должна совпадать с тем, что игрок видел в игре.
- **Изменение масштабирования способности** («X rescaled from A + (B per death) to C + (D per minute)») — карточка `ability_change(old, new, tag="rework")` в блоке Abilities, формулы как `scale_pill` с таблицей (`axis_label="deaths"/"time"`, `level_fmt`). В «?» у общей строки это не прячем. *Почему:* меняется сама способность; формулу без таблицы не прочитать.
- **Новая способность юнита/босса** («Alleviation: New ability. …») — карточка `ability_change(None, {...}, summary="New ability", tag="new")`, а не строка NEW. *Почему:* так же выглядят новые способности героев.
- **Переделанный объект** (все общие строки — REWORK, кроме NEW): `unit_header(..., new_mech="Reworked objective")`. Строки REWORK становятся блоком-описанием «как это работает теперь», строки NEW остаются изменениями ниже. *Почему:* это описание нового устройства, а не пять отдельных изменений — как у Shrines of Wisdom.
- **Где и когда появляется объект** (spawns repositioned, first spawn at 15:00, single active, day/night) — REWORK, не MISC. «Roshan no longer drops …» — DEL.
- **Строки ландшафта (Terrain Changes), канон 2026-10-03** (владелец: «всё под одним тегом, кашеобразно»): объект или
  кусок земли перемещён / переставлен / сдвинут / повёрнут / перестроен («has been moved / repositioned / shifted /
  adjusted / rotated / reduced to / decreased in width», «Moved …», «Extended …», «Lowered …», «expanded», «added and
  adjusted») → **REWORK**; добавлено новое (деревья, рампа, тропа: «has been added») → **NEW**; убрано → **DEL**
  (деревья — DEL, как и раньше); лагерь понижен («demoted», «can now only evolve once») → **NERF**, повышен / «evolve
  twice» → **BUFF**; исправления (dead spot, incorrect vision, pathing blockers, ward spot, «Touched up») → **MISC**.
  У строки ландшафта под текстом — микроскриншоты «было | стало» (data/terrain_spots.json →
  scripts/gen/terrain_shots.py → icons/terrain/, patch/elements.py `terrain_note`). Генератор:
  CANONICAL_TAGS «Terrain», тесты `test_terrain_canon`. **Показ:** с 2026-10-03 тег строки ландшафта на странице
  не виден — на месте чипа номер строки в её категории (с 1 в каждой), а картинки раскрывает название объекта в
  тексте («tier 1 safe lane towers», «several trees»; patch/terrain_notes.py `note_phrase`); владелец: «убираем
  кнопки SHOW внутри тегов… а сами строки просто нумеруем». Тег по канону всё равно ставится в контенте — он задаёт
  `data-tag` для фильтров и весов.
- **Вторая вычитка 7.38b–7.41e (2026-10-03), правило → почему** (генератор: CANONICAL_TAGS / LOWER_IS_BUFF,
  тесты `test_canonical_tags_from_the_second_audit`, `test_lower_is_better_from_the_second_audit`):
  - «Now granted by Aghanim's Scepter/Shard» → **REWORK** (+ «?» откуда было): способность переехала между
    улучшениями, она не новая (PA Fan of Knives 7.39, Treant Eyes In The Forest 7.40 — по KV `IsGrantedBy…`).
  - «Now is a basic ability» → **REWORK**; «Now is an innate ability» — **REWORK** и в карточке, если врождённой
    стала существующая способность (Earthshaker Slugger 7.39 был фасетом).
  - Своё «now undispellable» / «Now cannot be dispelled» → **BUFF**; «Now dispelled when …» → **NERF**;
    «No longer gets knocked off …» → **BUFF**; «now affected by negative Health Restoration», «now count as hero
    hits», «now has a 3s initial cooldown», «now only applied if …» → **NERF**; иллюзии / creep-heroes, по которым
    эффект «will not deal damage» → **DEL**; «…instead of only higher level heroes» (область расширена) → **BUFF**.
  - Фасетный талант «Facet: Level N Talent X replaced with Y» → **SWAP**, как и обычный.
  - `l=True` (меньше = лучше): attack rate (секунды на удар), attacks required, flight duration, «time for X
    application», урон своей иллюзии (illusion damage reduction). Только по смыслу, не словом: свой штраф к урону
    или скорости атаки (Focus Fire, Grow), потолок скорости врагов (Deluge), награда за своего варда, радиус, где
    союзник врага отключает пассивку (Desolate), — `l=True` ставится руками.
  - Опечатка Valve в числах (Techies Proximity Mines 7.41a «450», «225») — `wrong-word` + `note_box` с реальными
    значениями из KV, бейдж по KV. Valve пишет «decreased», а числа выросли — то же (Grimstroke 7.40c).
  - «per Spirit Bear level up» → формула `A + B*(L-1)` (Spirit Bear 7.40b, 7.41c), см. formula-tables.
  - 7.38 (вычитка 2026-10-03): «Aghanim's Scepter/Shard no longer decreases …» → **DEL**, и wind-up тоже (подсказка
    7.37e «Decreases wind-up time»; исключение «wind-up → BUFF» осталось только для строки фасета); «Now has 50%
    block value against creeps» → **NERF** (новый штраф по крипам); строка Valve под не той способностью (Quick Wit
    «Attack Speed per Intelligence 0.5 → 1» была под новой Aggrandize) уходит к своему фасету; «Ability Reworked» +
    описание в «?» → карточка `ability_change` со старой подсказкой (Silencer Arcane Curse, Last Word).
  - Слово Valve «improved» / «worsened» само задаёт направление: улучшено в сторону меньшего числа (или ухудшено в
    сторону большего) → `l=True` («Ghost spawn rate improved from 0.35s to 0.25s»). Генератор: `_said_lower_better`,
    оно сильнее списка слов. Сверка флагов `l=True` в 7.40–7.41 с генератором (2026-10-03) дала ещё слова: mana
    costs, mana/sec, capture time, formation time/delay, time to max effect, charge loss, explosion delay, fade time,
    self damage; и исключения: «… Reduction increased» у талантов (Manacost/Manaloss, Damage Taken, Time Reduction),
    «without a cooldown», «Incoming Damage Buff» Рошана, способность False Flight.
- **«X removed and replaced with new …: Y»** — строка DEL уходит под свой подзаголовок X над блоком Y. *Почему:* это изменение старой вещи, а не описание новой.
- **Строка без метки внутри описания нового объекта** (например, опыт от Shrines плюс «?») тоже входит в описание: метка NEW, чип скрывается.
- **Две соседние однотипные строки с одинаковым «?»** (Great / Greater Lotuses) — одна строка «…A, and B», одно «?». *Почему:* это одно изменение про два значения.
- Генератор делает всё это сам: `_postprocess_boss_blocks`, `_postprocess_new_block_label`, `_postprocess_merge_twin_rows` и CANONICAL_TAGS. Тесты лежат в `tests/test_generator.py`.

## Уроки вычитки 7.38: Lifesteal и списки в «?» (правило → почему)
- **Текст Valve не резать и не пересказывать.** Родительская строка идёт целиком, вместе с «Lifesteal mechanics are now consistent across every ability». Собственный «?» Valve у родителя тоже не теряем. *Почему:* пропадала часть смысла, а «?» у последней строки (Holding Alt…) был потерян совсем.
- **У вложенного пункта свой «?» Valve** («Examples: Cleave…») — в той же строке списка, приглушённо: `<span class="pop-note">(…)</span>`. Генератор делает это в `_nested_info_text`.
- **Раздел, где все строки REWORK** (кроме QoL/NEW, минимум 3), описывает переделанную механику: `plain_header(..., new="Reworked mechanic")`. Строки REWORK становятся описанием, подсказка про Alt (QoL) остаётся изменением. Под Map Objectives метка «Reworked objective».
- **Несколько строк в «?» — это список:** `info_tip` сам рисует золотой кружок на каждой строке, строка `&nbsp;&nbsp;– x` становится подпунктом. Одна строка остаётся обычным текстом. Работает на всём сайте, в контенте ничего менять не нужно.
- **Два «?» в конце одной строки → один** (2026-10-09, Earth Spirit 7.40: `note_box` «Now it's 25» + `inline_note` «Damage at level 1…»): `li()` склеивает их (`merge_tips`), заметки идут частями `.pop-part` через тонкую линию. Тест `tests/test_merge_tips.py`. *Почему:* два «?» подряд выглядят как ошибка.
- **General раскладывается по темам** (2026-10-16, 7.41 Global Changes: строки про врождённые, течения и лайн крипов стояли вперемешку). Генератор `_general_topics`: тема с двумя строками и больше получает свой подраздел в конце — «Scaling with Hero Level» (per level / hero level / innate abilities), «Lane Creeps» (строки, которым `_link_lane_creeps` дал `also_dyn` на лайн крипа); строки без темы и одиночные остаются сверху. Строка про ОДНОГО лайн крипа идёт под его карточку (`unit_header(..., page="flagbearer-creep")`, как у юнитов: Melee / Ranged / Flagbearer / Siege Creep, префикс имени снимается; **карточка всегда кликабельна** — `page=` ведёт на страницу юнита и даёт полосу патчей, тест `test_lane_creep_cards_link_their_unit_pages`), в «Lane Creeps» остаются общие (точка встречи). «<X> removed from the game» (7.41 Facets) — выделенная строка `li(…, major=True)`: только жирнее и ярче, размер, отступы и линия как у соседних строк (черта и крупный шрифт сбивали её с ряда), тег DEL остаётся (фильтр, веса); вводной фразой без тега было тускло и терялся DEL (владелец 2026-10-16). Выделяется ТОЛЬКО такая фраза — убрана целая система; «самое большое» по весам не выбираем. Разделы карты (Map / Terrain / Objectives) не трогаются: там порядок Valve. Поправлены 7.41 и 7.40. Тест `tests/test_general_regroup.py`.
- **Целая система изменилась — раздел «Reworked mechanic»** (2026-10-16, 7.41 «Scaling with Hero Level», по образцу 7.38 Lifesteal / 7.40 Invulnerability Targeting): строки и их «?» сводятся в несколько строк описания, без видимых тегов (QoL / MISC там читались как продолжение строки выше); свой тег строки — скрыто в `force_tag` (фильтры, веса). Генератор: тема из `_MECH_TOPICS` → `plain_header(…, new="Reworked mechanic")` после общего блока, строки REWORK (`_as_mech_row`); свести текст — при вычитке.
- **Бафф с числом в заметке — бейдж с процентом** (2026-10-16, 7.41 течения: «… bonus of 150», в «?» «other sections provided max bonus of 100» → `b(100, 150)` = +50%). Генератор: `_bonus_from_note`.
- **Способности существ — всегда блоками способностей** (2026-10-16): у боссов (Tormentor, Roshan) Valve пишет и без двоеточия («Unyielding Shield Base barrier increased…») — `_postprocess_boss_blocks` узнаёт имя и так, в строках с формулой тоже; у лайн крипов — `_lane_card_abilities` (7.40 Flagbearer Inspiration Aura; иконка из файлов игры, `scripts/fetch/extract_vpk_boss_icons.py`). Раздел General с именем босса (7.41e «Tormentor») — его карточка, не простой заголовок. Поправлены 7.41 Tormentor, 7.40 Flagbearer, 7.41e Tormentor (аудит всех патчей 10-16).
- **Лишний лайн крип раньше — BUFF, позже — NERF** (владелец 2026-10-16: «First +1 siege creep timing decreased from 35:00 to 30:00 — а не buff ли это? на 5 минут раньше»): больше этого крипа и раньше — его усиление; процента нет (процент от времени смысла не имеет). Время появления объектов и боссов («First Spawn Time 15:00 → 20:00», «Tier 1 availability 5:00 → 0:00») — по-прежнему REWORK. Канон в генераторе.
- **Рост со временем — таблица по минутам** (2026-10-16): «<X> upgrade per minute increased from A to B» → `li_formula` с минутами 0…60 (`_postprocess_per_minute`; 7.41 Tormentor Barrier upgrade). XPM и прочие скорости («Experience per Minute») — не рост, остаются строкой.
- **Первое появление босса переехало — снимком** (2026-10-16): «Spawn preference has switched» (Tormentor), «Pit preference has switched» (Roshan) — снимок карты, где золотым кольцом отмечено логово, с которого босс начинает, на старой и на новой карте, а на плашке — когда он там появляется: Tormentor 20:00 (с 7.39, было 15:00), Roshan 0:00 (`terrain_spots.json` ключ `first` с `label`, `terrain_shots._first`).
- **На карточке существа его имя в начале строки не повторяем** (владелец 2026-10-16): «Tormentor's spawn preference» → «Spawn preference» (`_postprocess_unit_possessive`); строка «Roshan's …» из общего списка уходит на карточку Roshan (`_postprocess_boss_rows_home`). Поправлены 7.41, 7.38.
- **Подраздел механики, где все строки REWORK, — тоже «Reworked mechanic»** (2026-10-16, 7.41 «Health Restoration», «Lifesteal and Damage Manipulations»): от двух строк, только в разделе механик (`_postprocess_new_block_label`); короткие «?» — в саму строку, списки затронутых способностей остаются в «?».
- **«Lifesteal … don't apply to reflected damage» — REWORK** (владелец 2026-10-16): так теперь работает отражённый урон, а не убранный эффект (`TAG_OVERRIDES`).
- **«… now affected by Area of Effect / AoE bonuses» — NEW** (владелец 2026-10-16, 7.41 Congregations of the Deep, Water Bubble (Large); были BUFF): новое свойство, зеркало «no longer affected …» → DEL. Канон в генераторе.
- **«… has switched» + «?» «Now …» — одной строкой** (2026-10-16, 7.41 Tormentor / Roshan: «Spawn preference has switched — now begins in the Bottom Chasm»): без заметки строка ничего не говорит (`_postprocess_switched_note`).
- **5 уровней и больше — проценты диапазоном** (владелец 2026-10-16, Dagon 7.41: «слишком много надписей»): бейдж показывает первый и последний уровень «−9% … −29%» (`patch/badges.py RANGE_FROM_LEVELS`), тег считается по всем уровням. 4 уровня (способности героев) — как раньше, каждый.
- **Карточка способностей предмета подсвечивает и одно убранное слово** (2026-10-16, Refresher Shard 7.41: «no longer refreshes items» = «all your items and abilities» → «all your abilities»), даже если слово слишком частое для обычного сравнения («items»).
- **Значение, которое подсказка игры не различает, дописывается в новое описание** (2026-10-16, Crimson Guard 7.41: «Guard base damage block rescaled from 70 for all units to 70 on melee heroes and buildings and 45 on ranged heroes» → «45 base damage block on ranged heroes.» цветом тега, строка уходит в карточку; `_IAB_TAILS` с числом из строки). Способность строки — та, с которой строка начинается («Guard …», не «Damage Block»).
- **Шапка карточки способности: 5 уровней — значение 1-го уровня пунктиром, все уровни в подсказке** (владелец 2026-10-17, Dagon 7.41: сначала «в шапке перезарядка, манакосты тоже с уровнями написаны… на будущее, когда на каком-то уровне что-то может поменяться», затем «показывай значение 1 уровня, но пунктиром подчеркни — в раскрывашке все уровни; касается старых и новых карточек»): «120» с подсказкой «Levels 1–5: 120 / 140 / 160 / 180 / 200» на обеих сторонах (`_iab_compact_levels`, тот же `RANGE_FROM_LEVELS`); изменённое значение окрашено целиком, а в подсказке при том же числе уровней цветом только изменившиеся уровни (`_iab_chip_mark`). 3–4 уровня пишутся целиком, изменившийся уровень — цветом прямо в шапке. Описание («Damage: 400/500/…») не трогается.
- **Два и больше изменений способности — карточка, даже если менялись только числа** (владелец 2026-10-17, Ash Legion Shield 7.41: «не надо сделать карточками, т.к. 2 изменения у способности?»): `tools/item_ability_text.insert_cards` рисует карточку, если про способность 2+ строки, кроме случая, когда описание то же и строки не про значения шапки (Block of Cheese 7.38 «Try me!» — две одинаковые половинки). Применено ко всем патчам: 34 карточки в 7.38–7.41f.
- **Предмет, который только убрали, — подпись цветом DEL на месте «Returning Tier 2 Artifact»** (владелец 2026-10-17): «Neutral Item cycled out» / «Neutral Item removed» в разделе нейтральных предметов, иначе «Item cycled out» / «Item removed», у чар «Enchantment removed» (`item_header(removed=…)`, `enchant_header(removed=…)`, генератор `_postprocess_removed_label`). Строка с DEL остаётся в странице скрытой — фильтр DEL её видит и показывает блок с подписью. Цвет в режиме дальтоников — из `gen_colorblind_css.py`. 27 блоков в 7.39–7.41.
- **Карточка способности без описания в игре — текст пишем сами, из файлов** (владелец 2026-10-17, Block of Cheese 7.38: подсказка в обеих версиях «Try me!»): числа из items.txt обеих версий, смысл значений — из кода игры (агент dota2-ida-researcher: «regen 100, idle 5» = +100 в секунду после 5 с без урона, «duration 5» = минуты), в коде контента комментарий — откуда каждое слово; чего нет ни в файлах, ни у Valve, не пишем (длительность щита в 7.37e). Чтобы строки уходили в такую карточку: кусок, разрезанный на «and», склеивается с соседним («Restores 3000 health and 2000 mana», `_iab_grow`), фраза начинается со слова строки и не повторяется на другой стороне (`_iab_phrase`: «Duration: 5 minutes», не «you Savory Shield»).
- **Прежде чем назвать число Valve ошибкой — патчноуты следующей буквы и сборка файла** (владелец 2026-10-17, Crude 7.41: я пометил «8/12/16%» как `wrong-word`, а 6/9/12% пришло в 7.41a — «worsened from 8/12/16% to 6/9/12%»). Локальный `items_history/7.41/items.txt` был побайтно равен `7.41a` (в d2vpkr между ними нет коммита): заменён настоящей сборкой 7.41 — 6728 из архива клиента (`DOTA2_CLIENT`, старый файл рядом как `items.7.41a-build-6743.txt`). Проверка всех снимков 7.37e–7.41e по номерам сборок: ошибался только этот. Из-за него были неверны Crude в подсказках, Consecrated Wraps 7.41 в `item_stat_lines.json` (12% вместо 15%) и не было карточки Hallowed 7.41a.
- **Чары — таблицей по тирам, «было → стало»** (владелец 2026-10-17, 7.41: «Vital почему-то так записан, как и Nimble… табличкой? карточкой? Mystical/Crude тоже» → вариант А): под шапкой каждой чары таблица как в 7.38 (`enchant_header` сам дорисовывает `_enchant_change` из `data/rules/enchant_tables.json`, собирает `scripts/gen/enchant_table.py <версия>`). Клетка «+30% → +20%» — новое значение цветом по тому, что оно даёт владельцу (штраф больше — красный, список штрафов `PENALTIES`: знак «−» сам не говорит, Manic «−18% Base Attack Time» — польза); тир, который появился, — золотой; пропавший — зачёркнут цветом DEL; целиком новый штраф — красный. Тиры «до» — из строки «Tiers changed from 4/5 to 2-4», иначе те же. Строки с числами и «Tiers changed» уходят в таблицу (`_ench_covered`), «guaranteed option …» и строки словами остаются. Удалённые чары (`removed=`) таблицу не получают.
- **Карточка состава: справа порядок левой стороны** (владелец 2026-10-17, Guardian Greaves 7.41: «1775 + 1400 → 1500 + 1775» читалось как подешевевший Mekansm): `_in_old_order` — каждый компонент под самим собой, новые в конце.
- **Строки, которые карточка показывает, уходят в неё** (владелец 2026-10-17, 7.41: «переведи в карточки»). Карточка берёт и строки с числами: «now also provides/grants +N …» (Drum / Boots of Bearing «+2.5 Health Regen», Mask of Madness «30% Slow Resistance», Weighted Dice «by 6»), «changed from A to B» (числа после «to»: Mask of Madness «+8%/12%»), «no longer provides N …» (Pipe). Окраска растягивается до числа строки в той же части фразы (`_iab_with_number`: сравнение текстов без чисел спаривает «2.5» с «8%»); уровень «15%/30%» считается числом; множественное = единственное («trees» = «tree»). Чего подсказка не говорит, дописывается хвостом: «now shares cooldown with X» → «Shares a cooldown with X.» (словами игры, как у Refresher), Harpoon «destroying all trees on the way» → «Destroys all trees on the way.» и новое предложение подсказки окрашено тоже (`_IAB_TAILS`, третий элемент `True`). Строка, которая говорит больше карточки и не укладывается в хвост (Bloodstone «no longer has a 30s self debuff…» с числом), остаётся.
- **Что старая подсказка не говорила, а теперь ушло, — после старого описания, красным** (владелец 2026-10-17, Pipe of Insight 7.41: строки Barrier — в карточку): строка «<способность> no longer <что>», одно предложение без чисел, слов которой нет в старом тексте → «<Что>.» в конец старого описания (Pipe «Affects units that have been affected by Barrier within Pipe of Insight's cooldown.», Dagon «Instantly kills non-ancient creeps.»). Значение шапки строки ищется после названия способности: «Reset Cooldowns mana cost …» — манакост, не перезарядка (Refresher Orb 7.41, новые 325 не красились).
- **Решения владельца по тегам 7.41, вторая партия** (2026-10-17, `TAG_OVERRIDES`): «… preference has switched» (Tormentor, Roshan) — REWORK, «влияет на геймплей»; Hand of Midas «Transmute no longer prevents camp-clearing Madstone Bundles…» — MISC; Radiance «Burn toggling no longer breaks invisibility nor stops channels» — QoL.
- **«Item moved (back) to … Shop» — REWORK** (владелец 2026-10-17, 7.41 Ring of Health / Void Stone; были NERF): где продаётся — перенос, как «Moved from Tier 4 to Tier 2». Канон в генераторе. **Crimson Guard «Guard base damage block rescaled …» — NERF** («значения меньше стали», `TAG_OVERRIDES`).
- **«Total cost unchanged» — в «?» строки цены** (владелец 2026-10-17: «по большинству единообразно»; 7.38–7.41 было 11 строк в «?» и 9 в тексте): «Recipe cost decreased from 600 to 400» + `inline_note("Total cost unchanged at 3900g (due to …)")`, и при «Recipe cost unchanged at 500» тоже. Карточка состава берёт такую строку с заметкой (причина «due to …» в тексте строки терялась — Solar Crest 7.41). Генератор: `_postprocess_recipe_cost_zero_net`; тест `test_an_unchanged_total_sits_in_the_rows_note`.
- **Тихое изменение — строкой с «?» «Not in the patch notes: found in the game files»** (владелец 2026-10-17, Crippling Crossbow 7.41: перезарядка Hobble 12 → 30 с в items.txt, Valve молчит): тег и бейдж как у обычной строки, комментарий в коде — откуда число (файл, версии).
- **Подсказки чипов чар — числа своей версии** (владелец 2026-10-17, 7.41: Vital в подсказке +2.25, в строке +2): `data/rules/enchant_values.json` из items.txt версии (`scripts/gen/enchant_values.py <версия>`), подписи из таблицы `_ENCHANT_DESC`; нет данных — таблица.
- **Раньше-не-было — в «?»** (2026-10-16): «second now occurs at 60:00» не говорит, как было; в «?» — что до 7.41 добавка была одна, на 35:00 (с 7.22). Если строка Valve называет только новое значение, найти старое (патчноуты, файлы игры) и вписать в «?».
- **Решения владельца по тегам 7.41** (2026-10-16, `TAG_OVERRIDES`): Mars Dauntless «no longer considers allies… outnumbered» — BUFF (реген включается чаще); BKB «Avatar duration changed from 9/8/7/6s to 9/8/7s» — BUFF (минимум 7 с вместо 6); Rubick «Stolen spells now have their cooldown decreased» — NEW (новое свойство вместо усиления дебаффов).
- **«… timing now occurs at 60:00» — NEW, своей строкой** (владелец 2026-10-16): второй таймер осадных крипов — новое свойство катапульты; не REWORK и не одна строка с «First … decreased from 35:00 to 30:00» (оба пробовали). Канон в генераторе; NEW по порядку тегов встаёт выше REWORK — так и задумано.
- **Уточняющая фраза Valve «All <тот же предмет> …» — в «?» строки выше** (2026-10-16: «Innate abilities no longer scale…» + «All innate abilities that used to scale… now either provide unchangeable bonuses…» → одна строка). Генератор: `_merge_all_followup`; своя заметка второй строки идёт следом в тот же «?».
- **Точка встречи лайн крипов — со снимком** (2026-10-16): в `data/terrain_spots.json` у 7.41 «Adjusted the meeting point of the lane creeps» — четыре кадра путей сложных линий (`show: ["lanes"]`; пути в файле карты 7.41 сдвинулись), слова «lane creeps» открывают снимки. Сама скорость крипов в файле карты не записана — на снимке пути, не скорость. Так же «All sections of currents …» — два кадра ручьёв, где зоны +100 стали +150 (`show: ["currents"]`, `scripts/gen/terrain_shots._currents`, цвета слоя течений Terrain).
- **Удалённый фасет — просто «Removed»** под `facet_header` (2026-10-09): заголовок уже называет фасет, группа Facets говорит, что это фасет; не «Resonance: Facet removed». Генератор пишет `li("Removed", t("DEL"))`, вес — как у целого фасета (`_WHOLE_DEL_RE` знает голое «Removed»). Тест `test_a_bare_removed_under_a_facet_header_is_a_whole_facet`.

## Новый предмет — карточка (общее правило, 7.38 Orb of Frost)
Порядок всегда один:
1. `item_header("X", new="New … Item")`: метка рядом с названием говорит, что предмет новый.
2. **Цена:** `item_cost(N)`, если предмет покупается целиком; `components(("A", 1000), …, recipe=("Recipe", 300), total=N)`, если собирается. У артефактов и нейтральных предметов цены нет. Если Valve цену не указала, берём `ItemCost` из KV патча.
3. **Бонусы:** `provides("+7 Armor, +125 Mana")` блоком, по строке на бонус. Если бонусов нет, блока нет: никакого «Provides no bonuses».
4. **Способности:** строки `Passive: Имя. …` / `Active: Имя. …` с `t("NEW")`, они сами оформляются рамкой способности.
5. **Описание и уточнения:** прочие строки с `t("NEW")`, детали в «?».
Генератор строит это сам (`_postprocess_new_item_card`). *Почему:* цена, бонусы и способности нового предмета — это его паспорт, а не список изменений.

## Уроки вычитки 7.38: метки (правило → почему)
- «No longer unbreakable» → **NEW**: у врага появилась новая возможность (сломать ауру).
- «X now restores …» (раньше не восстанавливал) → **NEW**. «Poison Attack now has a 9s cooldown» (раньше кулдауна не было) → **REWORK** (2026-09-28: способность теперь работает иначе; было NEW).
- «… now has a 5 minute duration» → **REWORK**: меняется то, как эффектом пользуются.
- «can no longer … However, … still …» → **REWORK**: потеря с оговоркой, а не просто удаление.
- «No longer refills / triggers / activates when …» → **DEL**.
- «Level increased from 5 to 6» у крипа → **MISC**: это классификация, а не сила. Уровень влияет только на то, кто может подчинить или съесть крипа.


## SWAP — талант заменён (2026-09-26)

Восьмой тег. «Level N Talent X replaced with Y» (и короткая форма «Level N: X replaced with Y») — это **SWAP**,
а не REWORK: в том же слоте дерева талантов один талант заменён другим, включая обмен уровнями.
REWORK теперь значит только настоящую переделку способности / предмета / механики.
- 455 строк 7.38–7.41f переведены (было 62% всего REWORK; в 7.41a/c/d/f REWORK целиком был из талантов).
- Бейдж: бирюзовый (`.badge.swap`), фильтр SWAP на страницах патчей и Changes, полоса в динамике.
- Вес: как у прежней строки REWORK таланта (сигнал K по доле выбора профи, иначе вес типа).
- Генератор: первая строка `CANONICAL_TAGS`.

### Судьба каждого таланта в строке замены (2026-10-21, Batrider 7.41)
В контенте строка остаётся `t("SWAP")` простым текстом — разметку делает сборщик (`patch/talent_marks.py`):
- старый талант ушёл из дерева → красным (цвет DEL);
- новый талант совсем новый → золотым; тег строки остаётся **SWAP** (с NEW замена считалась усилением:
  итог 7.38 уехал с +54 до +86, 2026-10-21);
- талант только сменил уровень (тот же талант без чисел стоит в другой строке замены этого героя в этом патче)
  → без цвета, подсказка «moved from / to Level N».
**SWAP на всех строках замены — решение владельца 2026-10-22.** Тег один на любую строку «X replaced with Y»:
и с переездом таланта между уровнями (185 строк 7.38–7.41f), и с простой заменой «убран + новый» (268), и для того же
таланта с другим числом (4). Отдельного тега для простой замены нет и REWORK туда не возвращать: в одной строке два
таланта с разной судьбой, её показывают цвета, а REWORK — только настоящая переделка способности.
Талант той же способности, но с бонусом другого вида (плоский → процент, «только при активации» → постоянный), —
**другой талант**: старый красным, новый золотым, не переезд. Так оставлены 9 спорных строк, сверенных по файлам игры:
Sniper 7.38 и 7.41, Earth Spirit 7.40 и 7.41f, Io, Lone Druid, Luna 7.40, Elder Titan 7.41, Venomancer 7.41c.
В `_KNOWN` их не добавлять.

Ограничение: сверка по тексту строк патча. Талант, который уже был в дереве и не упомянут в патчноуте, сборщик
сочтёт новым — такие случаи проверять по файлам игры (агент dota2-ida-researcher) и писать подсказкой.
Баг в игре рядом со строкой — `bug_note(...)` (жучок вместо «?»), не `inline_note`.

## Смена способа наведения + новое поведение (2026-10-21, Bane 7.41)
«Now a Unit Vector Target Spell», а следующей строкой — что теперь делает способность (`t("NEW")`) → строка про
наведение **MISC**: новинка одна, считается один раз, на строке поведения. Если строки поведения нет
(наведение и есть всё изменение, Grimstroke 7.39 «Point Vector Target … now enabled by default») → **NEW**.
Линтер знает оба случая.

## Карточка способности от Aghanim (2026-10-21, Clockwerk 7.41 Overclocking)
Текст карточки не начинается с «Active (Aghanim's Scepter upgrade).» / «Granted by Aghanim's Scepter.»:
Active/Passive уже в шапке карточки, а Aghanim сборщик сам переносит в строку итога («Ability reworked (Aghanim's
Scepter upgrade).» — в скобках перед точкой) с полоской. Писать в контенте можно как угодно — `ability_change` вырезает эти слова сам.

## Стрелка «старое → новое» уже всё сказала (владелец 2026-10-22, 7.41)
- Итог карточки не называет заменённую способность: «Inner Beast is now the innate ability.», не «… (replaces
  Rugged)»; «Slugger is now an innate ability.», не «Spirit Cairn removed; …»; «Innate reworked.», не «renamed and reworked».
- Под шапкой со стрелкой (`ability_change` с разными именами, `ability(old_title=)`) строки «X renamed to Y» нет.
  Переименованный предмет — тоже стрелкой: `item_header("Orb of Blight", old_title="Blight Stone")` (7.38), без
  строки «renamed to». Способность внутри предмета без своей шапки (Replenish Mana → Replenish 7.38, Magic Weakness →
  Spell Weakness 7.41) — строка MISC остаётся.
- Строка «Now also provides …» под реворк-карточкой: эта фраза в карточке крашется `hl(..., "new")`, числа —
  `hl(..., "nerf"/"buff")`, а строка скрывается `covered=True` (веса и фильтры её видят) — Dark Seer Quick Wit,
  Dragon Knight Elder Dragon Form, Void Spirit Intrinsic Edge 7.41, как Clockwerk Overclocking.
- Смена способа применения, после которой способность действует иначе («Now a no target ability that affects only
  Bloodseeker», Omniknight 7.41) — **REWORK**, не NERF.
Тест — `tests/test_fixes_1022.py`.


## Переключаемые способности (2026-09-27, решение владельца)

- **Toggle под silence / невидимостью → MISC.** «Toggling is no longer disabled by silence», «Toggling no longer
  breaks invisibility», «Now can be toggled while silenced», переключение стойки/оружия (Kez Switch Discipline
  «Can no longer be disabled by Silence») — для такой способности это геймплей не меняет. 11 строк 7.40b–7.41e.
  Касты НЕ-переключаемых способностей под root/silence остаются BUFF/NERF.
- **Тип урона — как было**: «Damage type changed» = REWORK, «classified as reflection damage» = MISC (владелец 2026-09-27).
- Генератор: первые правила `CANONICAL_TAGS`; тест `test_toggle_under_silence_or_invisibility_is_misc`.

## Решения владельца 2026-09-27 (разбор спорных тегов)

- Эффект перестал действовать на класс целей (Debuff Immune, иллюзии, неуязвимые): «doesn't affect Debuff Immune
  units» → **DEL** (как «is not applied if»). Исключение «не действует в фонтане» остаётся NERF.
- Индикатор / таймер в интерфейсе («overhead indicator», «Tormentor Timer near the minimap») → **QoL**.
- «Now levels up with / Now scales with <способность> / Now upgrades with …» → **REWORK** (зеркало «No longer levels with»).
- «Can no longer be cast while rooted» → **DEL** (Tusk 7.08 выровнен с 7.41c).
- Тест: `test_owner_decisions_2026_09_27_del_qol_rework`.
