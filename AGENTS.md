# Sloppy — Dota 2 patch notes site

## Старт сессии — прочитай это

**Язык общения:** отвечай пользователю на русском (триггер `session_go` и работа над Sloppy в целом).

Чтобы сразу быть в контексте, в начале сессии прочитай:
- `AGENTS.md` (этот файл) — общая структура, source of truth, запуск.
- `docs/architecture.md`, `docs/workflow.md`, `docs/data-format.md` — конвейер **патч-страниц** (`build_patch.py`).
- `docs/tables.md` — подсистема **таблиц** (Neutral Creeps + вложенная Neutral Abilities / Mana Items: `build_creeps.py`, `build_mana_items.py`, sticky/overlay-архитектура, история ячеек, грабли).
- `docs/captains-mode.md` — правило оформления изменений **Captains Mode** (порядок драфта → визуальный токен-борд `cm_draft`, а не текст).
- `docs/formula-change.md` — правило для важных **игровых формул** (Assist Gold, Experience…): блок old→new `formula_change`, а не два `li`.

Сайт = две подсистемы: (1) аннотированные патчноуты и (2) сортируемые таблицы под разделом Materials. Общие `styles.css` / `scripts.js`.

## ВАЖНО: source of truth

`build_patch.py` — **главный файл патч-страниц**. CSS и JS читаются с диска при старте: `styles.css` и `scripts.js` — это **source files**, редактируются напрямую.
- `scripts.js` и `styles.css` — единственный источник правды для стилей и поведения всех страниц (включая `index.html` и `calendar.html`). Редактируй напрямую — IDE/linter работают нормально.
- Сгенерированные HTML (`patches/7.41c.html` и т.д.) — результат запуска `python build_patch.py`, не редактируй вручную.
- Все патч-файлы лежат в `patches/` (не в корне), поэтому их CSS/JS подключаются через `../styles.css`, `../scripts.js`.

### Patch-page visual layering

Патч-страницы должны использовать Valve-style continuous slab layout:
- `body.patch-page::before` держит общий `featured.jpg` фон.
- `.cat-panel` — один непрерывный content slab под заголовком категории: blue/black translucent gradient + broad black glow. Не возвращать старую модель большой скруглённой карточки с opaque фоном.
- `h2.section` — отдельная orange-to-transparent полоса с left orange border и glow; после неё нужен явный шов перед content slab.
- `.entity-block` внутри `.cat-panel` не должен быть отдельной карточкой/slab. Между героями/предметами/сущностями не должно быть “пропастей”; только тонкая full-width hairline, которая доходит до dyn-cells справа, чтобы было понятно, к какой сущности они относятся.
- Внутренние `item-cost-box`, `provides-box`, `properties-change`, `components-change`, `ability-block`, `patch-dynamics` должны оставаться одной ширины внутри entity-block. Если меняешь отступы, обязательно проверить Chasm Stone и соседние items в `patches/7.41.html`.

## Структура проекта

```
build_patch.py            ← ГЛАВНЫЙ. CSS, JS, HTML-хелперы, данные всех патчей
generate_patch_code.py    ← KV → Python-код. Запускать перед добавлением нового патча
scripts/apply_stats.py    ← Постпроцессор: t("BUFF")→bstat_h() где есть БД
data/
  patchnotes_english.txt  ← Сырые патчноуты Valve (KV формат)
  patchnotes_russian.txt  ← Русский перевод
  stats/{version}/
    heroes.json           ← Стоты героев (npc_heroes.txt → нужные поля)
    items.json            ← Стоты предметов (items.txt → нужные поля)
patches/                  ← Финальные HTML, генерируются build_patch.py
docs/
  architecture.md, data-format.md, workflow.md
```

Внешние скрипты (в `D:\Sloppy Patches`):
- `extract_patchnotes.py` — выкачивает свежие patchnotes_*.txt и npc_*.txt из локального VPK + заливает в репо
- `fetch_stats.py` — скачивает npc_heroes/items.txt из muk-as/DOTA2_CLIENT за каждый патч (с 7.33), парсит → JSON
- `upload_stats.py` — заливает JSON-файлы в репо

## Как запустить

```bash
python build_patch.py        # пересобирает все patches/*.html и calendar.html
python build_heroes_stats.py # heroes_stats.html — таблица статов героев (после build_patch)
python generate_patch_code.py 7.42   # → _generated_p_7.42.py (вставлять в build_patch.py)
python scripts/apply_stats.py          # упгрейдит t() → bstat_h() где можем
python scripts/fetch_itemlist.py       # обновляет data/itemlist.json из датафида Valve
                                        # (имена предметов + ТЕКУЩИЙ ПУЛ НЕЙТРАЛОВ для items_dyn).
                                        # Запускать с выходом нового патча, затем build_patch.py —
                                        # добавленные/выведенные нейтралы подхватятся автоматически.
python scripts/extract_shops.py        # извлекает scripts/shops.txt из VPK → data/shops.txt
                                        # (КАТЕГОРИИ магазина для фильтра items_dyn: Consumables/
                                        # Attributes/Weapons…). Локально (нужен `pip install vpk`).
                                        # Запускать с выходом патча (Valve тасует категории), затем
                                        # build_patch.py — перемещения категорий подхватятся сами.
```

## Ключевые концепции

### Хелперы для строк изменений
- `b(old, new, l=False)` — числовой бейдж в %. `l=True`: меньше = лучше (cooldown, mana cost, BAT, gold cost, penalty, channel time, recharge, cast point)
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

### Свойства новой сущности — одна строка на каждое (системное правило)

Когда сущность (предмет, артефакт, чара, способность, фасет) **появляется новой** и её бонусы перечисляются в патчноуте через запятые («Provides X, Y, and Z» / «Bonuses: …») — каждое свойство должно быть **отдельным `W(li(...))`**, а не объединено в одну строку через запятые.

Дополнительно: **слово «Provides» в начале строки нужно убирать** — оно избыточно, строка и так показывает свойство.

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

### Порядок строк внутри `ul` (системное правило)

Все `W(li(...))` внутри одного `ul_open()` … `ul_close()` блока **сортируются по типу тега** в этом порядке (применимо к любой сущности — герои, предметы, чары, способности, нейтралы и т.д.):

1. **Числовые бейджи** — `b()`, `br()`, `bf()`, `bstat_h()`, `bstat_i()` (BUFF / NERF / %-дельты). Внутри группы порядок берётся из патчноута.
2. **`t("NEW")`** — добавление нового поведения/свойства/эффекта.
3. **`t("REWORK")`** — структурные изменения (смена тира, ограничение доступности, изменение механики).
4. **`t("DEL")`** — удаления.
5. **`t("QoL")`** — удобство/quality-of-life (сгруппировано перед MISC).
6. **`t("MISC")`** — всё прочее, в хвосте.

Применять даже если в исходном патчноуте Valve порядок другой — переставлять при наполнении блока. Примеры в коде: Crippling Crossbow, Jidi Pollen Bag, Crude.

### Группировка предложений из патчноутов в одну строку

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

### Заголовки сущностей
- `hero_header(name)` — `/heroes/{slug}.png`. Slug из `HERO_SLUG` или fallback titlecase
- `item_header(name)` — `/items/{slug}.png`. Slug из `ITEM_SLUG`
- `enchant_header(name, slug)` — для нейтральных enchantments. URL = `/items/enhancement_{slug}.png`. Использовать вместо `plain_header` для Crude/Greedy/Tough и т.д.
- `unit_header(name, icon_url)` — отдельный юнит (Spirit Bear) с кастомным URL
- `plain_header(name)` — без иконки (Mechanics, Tormentor, Roshan, Map Objectives и т.п.)
- `ability(name)` — `<h4>` название способности. **БЕЗ префикса героя** в имени! «Penitence», не «Chen Penitence». Generate_patch_code.py делает это автоматически — fallback titlecase берёт только bare ability name (после `entity_` префикса)
- `subgroup(name)` — `<h4>` подгруппа («Talents», «Abilities», «Spirit Bear»)
- **Категория «Other»** — первый `ul_open()` сразу после `hero_header` авто-оборачивается в подгруппу «Other» (базовые/прочие статы героя, как Base Intelligence у Jakiro). Если в блоке ровно одна строка, общая иконка меняется на иконку под стат (`STAT_ICONS`/`STAT_DETECT_RULES`). **Изменения обзора героя (day/night vision) → иконка `icons/vision.png`** (детект по «night vision»/«day vision»/«vision»). Не делать vision/прочие статы отдельной `ability(...)` — это категория Other.

### Структура changes-блока
```python
W(hero_header("Abaddon"))
W(ul_open())
W(li("Base Intelligence increased by 1", bstat_h("Abaddon", "AttributeBaseIntelligence", "7.41b", 1),
     extra=note_box("From 18 to 19")))
W(ul_close())
W(subnote("Damage at level 1 unchanged at 49-59"))
W(subgroup("Talents"))
W(ul_open())
W(li(...))
W(ul_close())
```

### Captains Mode (порядок драфта) → `cm_draft`

Изменения **порядка** банов/пиков в Captains Mode оформляются визуальным
токен-бордом `cm_draft(...)`, а не текстом «First - Second - …». Передавать **весь
драфт целиком** (все фазы, 24 шага) — шаги нумеруются сквозно 1..24 (как в игре).
Текстовую строку `li(... t("REWORK"))` оставлять. Краткий канон:

```python
W(plain_header("Captains Mode"))
W(ul_open())
W(li("Changed order of the first and the third ban phases", t("REWORK")))
W(ul_close())
W(cm_draft(                          # F/S=бан first/second-pick team, f/s=пик; titles не рисуются
    ("Ban 1",  "FSSFSSF", "FFSSFSS"),    # изменено в 7.40
    ("Pick 1", "fs",      "fs"),
    ("Ban 2",  "FFS",     "FFS"),
    ("Pick 2", "sffssf",  "sffssf"),      # ЗМЕЙКА (не чередование!)
    ("Ban 3",  "FSSF",    "FSFS"),        # изменено в 7.40
    ("Pick 3", "fs",      "fs"),
))
```

Борд = игровой экран пик/бана: вертикально, номера 1..24 по центру, слот действующей
команды слева (first-pick team — пикает первой, шаг 8) или справа (second-pick team — шаг 9);
доски Old и New рядом со стрелкой, БЕЗ цветов (команда — по стороне). Бан = узкий слот, пик =
большой. Шаги, где сменилась команда, — тусклая золотая рамка. Дефолт заголовков First pick /
Second pick. Структура 7.34+: Бан7·Пик2·Бан3·Пик6·Бан4·Пик2 (баны 3-2-2 / 4-1-2; пик-фаза 2 — змейка).
Полное правило (когда применять, кодировка `F/S/f/s`, что НЕ оборачивать) —
`docs/captains-mode.md`.

## База статов (stats DB)

Файлы `data/stats/{version}/heroes.json` и `items.json` — поля из npc_heroes.txt / items.txt. Покрытие: с 7.33 (источник muk-as/DOTA2_CLIENT). Для патчей старше 7.33 БД нет, fallback на t().

Ключи из npc_heroes.txt: `ArmorPhysical`, `AttackDamageMin/Max`, `AttackRate`, `MovementSpeed`, `AttackRange`, `AttributeBaseStrength/Agility/Intelligence`, `AttributeStrengthGain/AgilityGain/IntelligenceGain`, `StatusHealth`, `StatusMana`, `StatusHealthRegen`, `StatusManaRegen`.
Ключи из items.txt: `ItemCost`, `ItemCooldown`, `AbilityManaCost`.

## Маппинг описаний → поля БД (HERO_STAT_MAP в generate_patch_code.py)

При паттерне `"увеличено/уменьшено на N"` (без явного from-to) генератор смотрит первое совпадение:
| English текст | KV-поле | l_flag |
|---|---|---|
| base health regen | StatusHealthRegen | False |
| base mana regen | StatusManaRegen | False |
| base health | StatusHealth | False |
| base mana | StatusMana | False |
| base armor | ArmorPhysical | False |
| base strength/agility/intelligence | Attribute Base * | False |
| strength/agility/intelligence gain | AttributeStrength/Agility/Intelligence Gain | False |
| base attack time | AttackRate | True |
| movement/move speed | MovementSpeed | False |
| attack range | AttackRange | False |
| base damage | AttackDamageMin (avg с Max) | False, is_dmg=True |

## Системные правила (не нарушать)

### Порядок строк внутри `<ul class="changes">` (per-ability)

Канонический порядок `<li>` строк внутри **каждого** `ul_open()`/`ul_close()` блока (= внутри одной способности / talents subgroup / hero-stat ul; сортировщик НЕ пересекает границы способностей):

1. **NEW** (rank 1) — `t("NEW")`
2. **REWORK** (rank 2) — `t("REWORK")` / raw `badge rework`
3. **BUFF** (rank 3) — `b()` / `bf()` / `bstat_h()` / `li_formula` с overall=buff, или `t("BUFF")`
4. **NERF** (rank 4) — numeric с overall=nerf, или `t("NERF")`
5. **DEL** (rank 5) — `t("DEL")`
6. **QoL** (rank 6) — `t("QoL")` (отдельный ранг ПЕРЕД MISC, чтобы QoL группировался, а не перемешивался с MISC)
7. **MISC** (rank 7) — `t("MISC")`
8. **Untagged** (rank 8) — структурные/описательные строки, остаются в хвосте

**Применяется автоматически** через `_sort_changes_li(html)` (в `save_html()` post-processing) → `_li_rank(li_html)`. Stable sort: внутри одного rank'а порядок исходника сохраняется (обычно Valve KV order). **Вручную переставлять `W(li(...))` не нужно** — пиши в удобном порядке, билд нормализует. Применяется ко всем патчам автоматически (7.08 → текущий).

Скипается для `<ul>` с `class="ability-row"` (Passive:/Active:/Toggle:/Aura: item-описания — там авторский визуальный порядок). `ability_change` panel получает `data-tag="new del rework"` отдельно (это `<div>`, не `<li>`).

### `ability_change(old, new)` — что внутри / что снаружи блока

**Внутри панелей (`old.desc`, `new.desc`)** — только официальное описание способности (как в игре / в KV патча). Без отсебятины типа «Self-buff values nerfed:», «Encouraged X», «Pre-7.41 …».

**Снаружи swap-card** (через `W(ul_open()) / W(li(...)) / W(ul_close())` после `W(ability_change(...))`) — числовые изменения характеристик способности, которые «пережили» реворк: `Bonus Attack Speed decreased from X to Y`, `Cooldown changed from X to Y` и т.п.

**Inline-note к новой механике** — встраивать через `inline_note("...")` прямо в `new.desc=[]` (не через `W(subnote(...))` после блока — это рендерится ВНЕ карточки). Рендерер `_side` детектит ведущий `<div` и вставляет его как есть.

### `ability_change(old, new)` — выбор layout-режима

Логика в `build_patch.py` `ability_change(...)` решает между тремя визуальными режимами по identity и количеству строк:

1. **`is-in-place`** — `old.name == new.name` И иконки совпадают (`slug`/`innate=True` оба). Правая шапка скрывается — показываем только одну (левую). Пример: Lion's To Hell and Back.
2. **`is-in-place is-new-taller`** — то же, но `len(new.desc) > len(old.desc)`. Правая панель `align-self: start`, без фейкового `padding-top` («много пустого пространства сверху» — баг, который мы зафиксили). Новый body начинается сразу с верха панели, параллельно старой шапке. Примеры: Primal Beast Colossal 7.41, Marci Special Delivery / Bodyguard 7.41.
3. **`compact-old` / `compact-new`** — разные identity И разница в строках ≥ 2. Меньшая панель центрируется.
4. **Plain symmetric** — всё остальное, обе шапки видны.

**Правило:** одинаковое имя+иконка → **ВСЕГДА** одна шапка (левая). Не показывать обе. Это явная просьба пользователя.

### `correction-note` фразировка (note_box со stats DB)

- Текст: `"Before this patch it was changed in <PATCH_LINK> (age)"`. Без двоеточия после `in` — это предлог, не лейбл.
- `<PATCH_LINK>` — клик ведёт на страницу патча (`{ver}.html`). Реализовано через хелпер `_patch_link(version)`. CSS-класс `.patch-link` (color inherit, dotted underline, hover синий).
- Возраст рендерится через `_format_age(days)`:
  - `< 365` дней → `"N days ago"`
  - `>= 365` дней → `"Y years M months ago"` (months скрыт если 0; singular/plural корректно)
- Лейбл `"Previously:"` — отдельный `<span class="correction-label">`.

### «No longer has a X penalty» — это BUFF, не DEL

Default-эвристика `no longer` → NERF/DEL **не работает** для строк, где удаляется **штраф** (penalty / downside / restriction / limitation). Удаление штрафа = бафф для героя.

Триггер-существительные: `penalty`, `downside`, `restriction`, `limitation`, `damage penalty`, `cost penalty`, `cooldown penalty`. Эвристика в `generate_patch_code.py::_detect_text_tag` уже это спецкейсит.

Контр-примеры (остаются NERF/DEL): «no longer applies slow», «no longer grants invisibility», «removed from the game».

### KV-строки с суффиксом `_info` — это `inline_note`, не отдельный li

В `data/patchnotes_english.txt` Valve явно помечает уточняющие строки суффиксом `_info` (например `_talent_2_info` поясняет содержимое `_talent_2`). Такие строки **никогда** не должны эмититься как отдельный `W(li(..., t("MISC")))` — только как `extra=inline_note(...)` к предыдущей строке.

Реализовано в `generate_patch_code.py` через `_attach_inline_note(out, desc)` для всех hero-веток (`hero_base`, `hero_ability`, `hero_talent`, `spirit_bear`, `spirit_bear_talent`, `general`, `item`). Если у предыдущей li уже есть `extra=inline_note(...)`, новый текст дописывается через `<br>`.

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

### Иконки-чипы → нужны hover-тултипы (если рядом нет пояснения)

Когда строка показывает список иконок-чипов (предметы, способности, сувениры и т.п.), каждый чип должен нести `data-tooltip="..."` с описанием эффекта, **если** рядом с чипом нет inline-текста, объясняющего что он делает.

- **Тултип нужен**: чип = иконка + имя (Ringmaster Dark Carnival souvenirs — игрок не знает, что делает «Funhouse Mirror»).
- **Тултип НЕ нужен**: рядом уже есть текст эффекта (раздел **Enchantment Changes** — у каждой чары перечислены бонусы рядом с чипом).

HTML-escape тултип через `_html.escape(text, quote=True)`. CSS `.enchant-chip[data-tooltip]::after` уже стилизует popup.

### Pool-style строки («X now consists of A, B, C») → показать kept + removed

Когда патч пишет «новый пул такой-то», текст скрывает что **удалили**. Перед написанием строки грепать прошлые патчи (facet-определения, прошлые пулы) и диффить — определить выпавшие элементы. Рендерить две группы chip'ов: в `inline_note` сначала «In pool:» с оставшимися, потом «Removed:» с выпавшими (с модификатором `.removed` — strike-through + красная рамка + grayscale иконки).

Helper: `souvenir_chip(name, slug, removed=False, tooltip=None)` → `<span class="enchant-chip souvenir-chip">` (pill с рамкой). `removed=True` → opacity 0.55 + grayscale **только на `> img` и `> span`** (НЕ на самом чипе, иначе tooltip popup `::after` тоже затемняется и становится плохо читаемым; явное правило `.removed::after { opacity: 0 }` + `.removed:hover::after { opacity: 1 }` сохраняет видимость подсказки). **Никакого strike-through.** Группы `.souvenir-group` — горизонтальный flex-ряд, разные группы на разных строках (каждая group block-level). Иконки — из `OneDrive/Desktop/panorama/images/spellicons/<slug>_png.png` → копировать в `Sloppy/icons/abilities/<slug>.png`. Пример: Ringmaster Dark Carnival Barker 7.41 (выбросили Crystal Ball + Weighted Pie).

**Фильтр:** если строка структурно REWORK, но содержит удаления (часть пула выпала), передавать `force_tag="rework del"` в `li(...)` — видимый бейдж остаётся REWORK, но строка попадает и в DEL фильтр для пользователей, отслеживающих удаления.

Главный текст строки описывает структурную суть («Souvenir pool unified across both Dark Carnival facets»), не перечисляет имена — это работа `inline_note`.

### Любой "per level" в строке → клик-формула обязательна

Если в строке упоминается per-level scaling (`X + Y per level`, `Xs − Ys per level` и т.п.) — рендерить через `li_formula(...)` (diff old vs new) или `scale_pill(...)` (новая способность без сравнения). Простой `t("MISC")` с текстовой формулой = баг.

```python
# Diff (старое → новое):
W(li_formula("Bonus Night Vision changed",
             "250 + 25 per level up", "225 + 25 per level",
             lambda L: 250 + 25*L, lambda L: 225 + 25*L,
             effective_unchanged=True))

# Новая способность (внутри ability_change new=dict(...)):
_pill, _table = scale_pill("45.75s − 0.75s per level",
                           lambda L: 45.75 - 0.75 * L,
                           levels=[1, 5, 10, 15, 20, 25, 30],
                           value_fmt="{:.2f}s")
# В desc: "Cooldown: " + _pill + ".",  tables=[_table]
```

**Сетка уровней (ПРАВИЛО):**
- **Полноширинные** таблицы (li_formula / scale_pill в обычной `li`-строке): НЕ передавать `levels=` — дефолт L1–L15, L20, L25, L30 (полная сетка) обязателен.
- Скейл каждые **X>1 уровней** («per 5 levels», «per 3 level ups»): сетка с шагом X до 30 (точки, где значение реально меняется, + L1). При смене шага old→new («per 7 → per 6 levels») — объединение точек перелома обеих формул.
- **Внутри панелей `ability_change`** (пол-ширины): компактная `levels=[1, 5, 10, 15, 20, 25, 30]` — полная сетка туда физически не влезает (`table-layout:fixed`, колонки сжимаются нечитаемо).

### li_formula с `effective_unchanged=True` → левый тег MISC

`li_formula` авто-вешает REWORK слева по умолчанию. Когда `effective_unchanged=True` — переключается на MISC (семантически нейтральная переформулировка, не структурная переработка). Глобальная строка `"Abilities that had 'per level up' scaling changed to be 'per level'"` тоже MISC, не REWORK.

### "per level up" ≠ "per level" (7.41 rename)

7.41 переименовал механику: `"Abilities that had 'per level up' scaling changed to be 'per level'"`. В `li_formula(...)` для 7.41 изменений вида `"changed from X per level up to Y per level"` — **СТАРАЯ** строка обязана содержать `"per level up"` буквально:

```python
W(li_formula("Agility Multiplier changed",
             "0.6 + 0.05 per level up",   # OLD — обязательно "up"
             "0.55 + 0.05 per level",     # NEW — без "up"
             lambda L: ..., lambda L: ...,
             effective_unchanged=True))
```

Удаление `up` из OLD-строки = семантическая ошибка (переименование механики не отражено). Обычно сочетается с `effective_unchanged=True` + `subnote("Effective values are not changed")`.

### "Effective values are not changed" → `effective_unchanged=True`

Когда патчноут говорит `"Effective values are not changed"` рядом с формульным изменением, передавать в `li_formula(...)` флаг `effective_unchanged=True`. Это подавит вводящий в заблуждение Δ% (формула может буквально различаться по числам, но Valve её перепараметризировала так, что итоговое значение в игре то же).

```python
W(li_formula("Damage changed",
             "25 + 2 per level", "23 + 2 per level",
             lambda L: 25.0 + 2.0 * L, lambda L: 23.0 + 2.0 * L,
             effective_unchanged=True))
W(ul_close())
W(subnote("Effective values are not changed"))
```

Если `old_fn(L) == new_fn(L)` буквально на всех уровнях (просто другая запись той же формулы), флаг не нужен — старый branch `values_unchanged` уже схлопывает в одну `value` строку автоматически.

### "No longer has a separate value for incoming heal reduction" → MISC

Когда патчноут говорит, что заклинание `no longer has a separate value for incoming heal reduction` — это **MISC**, не DEL. Эффект не удалён, просто переехал в общую Health Restoration систему. Канон (Cold Attack, Soul Release, Pudge Rot и т.д.):

```python
W(li("X no longer has a separate value for incoming heal reduction", t("MISC"),
     extra=inline_note("Still reduces incoming heals due to Health Restoration changes")))
```

Использовать `inline_note` (на той же `<li>`), не отдельный `subnote`.

### Innate ability reworked

Когда патчноут говорит `"Innate ability reworked"` — это **обязательно** `ability_change(...)`, не две плоские `t("MISC")` строки. Старое описание лифтится из патча, который ввёл текущий innate (грепать `hero_innate_<entity>_<ability>` в `patchnotes_english.txt`). Генератор `generate_patch_code.py` теперь пишет `# TODO[innate-rework]:` маркер — никогда не оставлять его в коммите.

## Предупреждения и подводные камни

- При добавлении нового героя: добавить в `HERO_SLUG` (build_patch.py) И в `load_hero_internal_to_display()` (generate_patch_code.py)
- При добавлении нового предмета: только в `ITEM_SLUG` (build_patch.py); generate_patch_code.py читает оттуда
- 7.41c в HANDCRAFTED раньше был сырой HTML — теперь конвертирован в W() вызовы; следующие патчи делать только через W()
- `_formula_id_counter` — глобальный счётчик для table-id, сбрасывается при каждом запуске
- `.gitignore` исключает `__pycache__/`, `_generated_p_*.py`, `_insert_patches.py`. Одноразовые скрипты `_*.py` после использования можно удалять
- 7.08 — патч слишком старый для stats DB (muk-as начался с 7.33), он остаётся с t() fallback
- **Иконки способностей: fallback пишется в `src` напрямую.** Если локального файла `icons/abilities/<slug>.png` нет (множество innate-способностей не имеют публичной CDN-иконки), `ability()` рендерит fallback СРАЗУ как `src` (innate → `innate_icon.png`, иначе → `missing.svg`), а не «битый путь, который меняется через onerror». Иначе поиск (читает `img.src` при загрузке, до срабатывания ленивого onerror) показывал не ту иконку. Набор существующих файлов — `_LOCAL_ABIL_ICONS` (строится при загрузке модуля). Пример-каноник: Timbersaw «Exposure Therapy» (+ ещё 27 innate)

## Прочие генерируемые страницы (не патчи)

`build_patch.py` также генерирует:
- **`index.html`** (`save_index_html`) — лендинг в виде игрового «инвентаря-книги»: орнаментальная панель `.inv-book` с квадратными слотами (`icons/ui/gothic/`, пак [Gothic Pixel UI](https://abyssowl.itch.io/gothic-pixel-ui)). Верхний ряд `.inv-filled` = ссылки на разделы, нижний `.inv-ph` = плейсхолдеры. Золото подогнано под бренд-слово `sikle` (`#e3c46a`). Подписи — временные плейсхолдеры (шрифт Jersey 10). Старая `.zuma-*` сетка удалена.
- **`calendar.html`** (`save_calendar_html`) — календарь патчей + кастомный год-пикер (`.cal-year-picker`, не нативный `<select>`) + полоса-инфографика «Patch cadence» внизу (`_spark_svg`: SVG-sparkline, «красивая» 5-ступенчатая ось Y, gridlines/оси, hover-значения). Переключатель Compact живёт в шапке блока года.
- **`terrain.html`** (`build_terrain.py`, 5-я вкладка Materials) — сравнение рельефа old→new через **шторку-слайдер** (две карты `icons/maps/map_<ver>.webp`, попиксельно совмещённые, клип через `clip-path` по `--pos`) + список Terrain Changes этого патча. Полный план и TODO — `docs/terrain.md`.
  - **Список изменений парсится из `build_patch.py`** (никакого дублирования): `_terrain_changes_by_patch()` читает каждую секцию `plain_header("Terrain Changes")` → `{ver: [(text, TAG)]}`. Сейчас это 7.41 и 7.40 (у 7.40 свой большой ремап-список — не путать). Тег `b(...)`-строк выводится по направлению с учётом `l=True` (дешевле mana cost = BUFF, меньше capture time = BUFF).
  - **Конвенции тегов для terrain-строк:** **«demoted to a 'medium'/'small' camp» → NERF** (понижение тира лагеря = ослабление); **«Removed … tree(s)» → MISC** (удаление деревьев нейтрально, НЕ DEL); удаление вотчеров/объектов («watchers … removed») остаётся DEL; время захвата объекта (capture time) меньше → BUFF с `b(old,new,l=True)` (даёт %-бейдж).
  - **Пикер патчей** (`_picker_html`, gold-скин календарного year-picker) живёт **в заголовке списка** как версия: `[7.41 ▾] Terrain Changes` (`.terrain-list-head`). Перечисляет все патчи с изменениями рельефа; переключение (scripts.js `initTerrainPicker`) показывает соответствующую `.terrain-map-pane` + `.terrain-list-pane` по `data-patch`. Тулбара над картой больше нет.
  - **Карта-пара есть только для патчей из `_MAP_PAIRS`** (dict `патч → (old_ver, new_ver)`; сейчас `7.41`→(7.40,7.41) и `7.40`→(7.39,7.40)). `_compare_html(old_ver, new_ver, markers_svg)` строит слайдер для любой пары. **Маркеры + полная панель слоёв (Trees/Camps/10 точечных) — ПЕР-ПАТЧЕВЫЕ**: каждый патч со своим `data/terrain_diff_<ver>.json` получает тумблеры; `save_terrain_html` строит `markers_by_patch`/`counts_by_patch` (по `_load_diff(ver)`). Если у пары нет диффа → `_controls_html(layers=False)` рисует только Zoom (без мёртвых тумблеров). Общий crop-meta (`terrain_map_meta.json`) проецирует маркеры ЛЮБОГО патча одинаково (карты обрезаны ОДНИМ общим crop-box: `build_terrain_maps.py 7.39 7.40 7.41`). **scripts.js `initTerrainCompare` инициализирует ВСЕ `.terrain-compare`** (`querySelectorAll().forEach(initOneTerrainCompare)`), иначе скрытая по умолчанию вторая панель не получит рабочий слайдер. Для патчей без карты-пары — `_fallback_html` (последняя карта в блюре + «Map comparison for X isn't available yet»).
  - **Как добавить новый патч с картой+слоями (чек-лист):** (1) `python scripts/build_terrain_maps.py <prev> <new> [и все прошлые]` — ВСЕГДА перечислять все версии, чтобы общий crop-box не сдвинулся; (2) скачать `mapdata_<prevcode>.json` в `.cache/leamare/` (если нет) + `python scripts/build_terrain_diff.py <prev>:<new>` → `data/terrain_diff_<new>.json` (генерик-ключи `treesOld/New`, `campsOld/New`, `entities`); (3) добавить запись в `_MAP_PAIRS`. `_terrain_changes_by_patch` подхватит список изменений из секции патча автоматически. Не забыть `git add icons/maps/map_<new>.webp` + `data/terrain_diff_<new>.json`.
  - **Слои-оверлеи** (тумблеры в баре `.tc-controls-bar` НАД картой, не поверх): Trees, Camps + **10 точечных сущностей** (`_ENTITY_LAYERS`: towers/lotus/twinGates/tormentors/bounty/power/wisdom/outposts/watchers/roshan). **Ключи leamare** (`layerDefinitions.js`): Outpost=`npc_dota_watch_tower` (2), **Watcher=`npc_dota_lantern` (10)** — это РАЗНЫЕ слои!; Roshan=`npc_dota_roshan_spawner` (2); Tormentor=`npc_dota_miniboss_spawner`; Shrine of Wisdom=`npc_dota_xp_fountain`. Каждый = old(740)+new(741) координаты из `terrain_diff.json["entities"]`, делится слайдером (классы `.tm-old`/`.tm-new`), тумблер = root-класс `.show-<key>`. JS-обработчик generic по `.tc-layer-btn[data-layer]`.
  - **Power-руна — анимация**: спот power-руны может выкинуть любую из 7 рун, поэтому слой Power особый — на КАРТЕ его иконки (`tc_rune_0..6.png`, скачаны с liquipedia в `icons/ref/runes/`, в НАТУРАЛЬНЫХ цветах) циклятся каждые 3с пока слой включён (scripts.js `togglePowerCycle`/`setRune`). Кнопка показывает СЛУЧАЙНУЮ руну при загрузке. `tc_power.png` (дефолт) = regeneration. Маркер всё равно в зелёном диске. Порядок: amplify/arcane/haste/illusion/invisibility/regeneration/shield.
  - **Значок** = пиксель-адаптация ИГРОВОЙ иконки из `icons/ref/` (`scripts/gen_terrain_layer_icons.py`, `REFS`; SVG растрит через ImageMagick `magick`), перекрашенная в цвет типа (`COLORS`) с 3-тоновым шейдингом по яркости + 1px тёмная обводка. Без рефа (wisdom, watchers) — рисованный `FALLBACK`-глиф. **Маркер на карте (`marker_g`) = тёмная подложка-круг (`#0d100b` @0.66, чтобы пёстрая карта не просвечивала «мутно») + слабый тинт цвета типа (@0.34) + золотое кольцо + значок сверху** (значок — ОСВЕТЛённый цвет типа, чтобы читался на своём диске). Цвета `_ENTITY_LAYERS` (build_terrain) ОБЯЗАНЫ совпадать с `COLORS` (генератор).
  - Маркеры/счётчики валидны только для `_DIFF_PATCH` (7.41 — под него заточен `terrain_diff.json`). Иконки кэмпов — `icons/camps/creepcamp_{small,mid,big,ancient}.png`.
  - **Карты обрезаны впритык** (`scripts/build_terrain_maps.py`, `_content_bbox` теперь отсекает плоский серый плейсхолдер по доле контента в строке/столбце ≥10%, а не «любой не-серый пиксель» — раньше оставались жирные серые поля). Поля ≈0. Проекция авто-подстраивается через `data/terrain_map_meta.json` (crop x/y/w/h в координатах сшитого холста; markers reproject автоматически).
  - **Кредит источников**: рендеры карт — `leamare/dota-interactive-map`, координаты сущностей — `leamare/dota-map-coordinates` (две разные репы, обе в `_source_html`).
  - **Кнопка «View on map» на патч-странице**: `plain_header("Terrain Changes", terrain_link="<base_ver>")` дорисовывает золотую пилюлю-ссылку (`.terrain-jump-btn`) в заголовок → `../terrain.html?patch=<base_ver>` (напр. `7.41`/`7.40`). Один общий `terrain.html` (НЕ отдельные `terrain_<ver>.html`): `initTerrainPicker` (scripts.js) читает `?patch=` и предвыбирает соответствующую панель через тот же пикер. ⚠ `_terrain_changes_by_patch()` теперь матчит `plain_header\("Terrain Changes"` БЕЗ закрывающей `\)` — иначе аргумент `terrain_link=` ломает парсер (0 изменений).
  - **Иконки index'а** (terrain/telegram/donation плитки) генерит `scripts/gen_index_icons.py` (PIL, 32×32, gothic-gold) → `icons/ui/gothic/icon_*.png`.

### Materials page vertical rhythm (правило отступов)

Все страницы Materials (Neutral Creeps / Unit Abilities / Mana Items / Terrain) держат **один и тот же** вертикальный ритм между текстом-описанием и основным блоком (таблица/карта). Источник правды — три значения паддингов внутри `.creeps-scroll`:
- блёрб `.mr-blurb.inbox-bar` → `padding: 22px 28px 0` (низ 0);
- тулбар `.cal-toggle-bar.inbox-bar` → `padding: 14px 28px 16px` (gap блёрб→тулбар = 14px);
- основной контент идёт сразу под тулбаром (его 16px снизу = gap тулбар→контент). На terrain `.terrain-wrap` стартует с `padding: 0 28px 30px` (тот же боковой инсет 28px, верх 0 — gap отдаёт тулбар).

Любая новая Materials-страница ОБЯЗАНА переиспользовать эти паддинги (блёрб → тулбар → контент), чтобы отступ «текст ↔ таблица/карта» был одинаковым везде. Не задавать произвольный верхний паддинг контенту — пусть gap владеет тулбар.

### Единая панель тулбара `.toolbar-panel` (СТАНДАРТ — обязателен для новых страниц)

Все кнопки/переключатели тулбара любой страницы оборачиваются в **ОДНУ обрамлённую панель** `.toolbar-panel` (не россыпь отдельных пилюль):

```html
<div class="cal-toggle-bar inbox-bar"><div class="toolbar-panel">… контролы …</div></div>
```

CSS (`styles.css`, секция «UNIFIED TOOLBAR PANEL») делает всё автоматически:
- панель = тёмная подложка `#11161d` + рамка + `border-radius:8px`, `width:100%` внутри тулбара (тулбар держит ритм 28px по бокам);
- переключатели (`.ua-upgrades-toggle`) и группы-лейблы (`.view-group`/`.hd-remove-group`/`.hd-class-group`) — **плоские** (прозрачные); инпуты/селекты (`.cal-mode-select`, `.mr-price-range`, search) сохраняют свою рамку поля; чипы тегов/классов — свой дизайн;
- **тонкий разделитель** перед каждым контролом, КРОМЕ между двумя подряд идущими `.ua-upgrades-toggle` (тумблеры группируются плотно). Реализовано через `> *:not(:first-child)::before` + отмена для `.ua-upgrades-toggle + .ua-upgrades-toggle`;
- `.toolbar-panel > .hd-search` растягивается (`flex:1 1 220px`).

Применяется на: heroes_dyn / items_dyn (`dyn_matrix_common`), neutral_creeps / neutral_abilities (`build_creeps`), mana_items (`build_mana_items`). **Новую страницу с тулбаром оформлять так же.**

### Regen columns in stats tables

For `HP/sec` and `MP/sec` columns in both `heroes_stats.html` and `neutral_stats.html`: do not show a leading `+`; render non-zero values with exactly two decimals (`1.60`, `0.50`; Neutral Stats may use its comma decimal style `1,60`); render exact zero as `0` and tint it with a muted version of that column color. Keep numeric `data-sort` values separate from display formatting.

### Patch-page filters and Hero Dynamics

- On patch pages, tag filters and category/group filters must recompute layout together. After either filter changes, collapse empty `ul.changes`, `ability-block`, `subgroup`, and `entity-block` containers again.
- For patch-page visibility, the entity header/name itself does **not** count as visible content. A card stays visible only if it still has visible change rows, `ability_change` blocks, or real auxiliary panels such as components/properties/provides boxes.
- `heroes_dyn.html` now supports the same Melee/Ranged toolbar filtering pattern used in Hero Stats. Feed `data-attack-type` per row from the latest hero raw data; Spirit Bear is always melee.
- Dyn-cell pills inside `td.hd-cell` should stay visually centered by forcing the cell to `line-height: 0`; otherwise the pill sits slightly high in the grid.

### Hero Stats: innate-derived computed values

- `heroes_stats.html` must treat innate-derived stat bonuses as part of the computed model, not as presentation-only exceptions. If an innate grants or converts stats into another displayed column (damage, armor, move speed, regen, range, etc.), that bonus belongs in `Starting` / `Expanded` when the `Innates` toggle is on, and stays out of `Base`.
- This applies even when the innate is conditional or unusual (example: Axe gaining Strength from armor while alone). If the site chooses to model that condition in Hero Stats, it must be expressed as an explicit toggle/assumption, not silently baked into raw values.
- Current project rule: for Axe in Hero Stats, ignore the nearby-allies condition and model One Man Army as always active when `Innates` is enabled. That Strength bonus must flow through displayed STR and every derived stat it affects (HP, HP regen, damage, etc.).
- For hero-level formulas phrased as `X + Y per level up`, the increment starts after level 1. In Hero Stats this means `(level - 1)`, not `level`. This matters for innate-derived computations too (example: Techies mana-pool regen).
- Distinguish `per level up` from `per level`. `per level` includes level 1 immediately; do not silently convert it to `(level - 1)`. Techies mana-pool regen is the canonical example.
- Derived stats in Hero Stats use whole attributes where the game truncates before applying conversions (example: Medusa mana at high levels). Do not use fractional attributes directly for HP / mana / primary-attribute damage when the in-game stat is based on floored attributes.
- If an innate changes in a later patch (numbers changed, formula changed, reworked, or removed), Hero Stats must respect the patch-gated version of that innate for the selected patch history / latest snapshot logic. Do not assume innate formulas are timeless.
- The main `Damage` column in Hero Stats shows average damage only. `Dmg min` / `Dmg max` belong to `Expanded` as separate columns.
- If a hero has a stat-affecting innate that is actually modeled in Hero Stats, show the mini innate icon next to the hero name. The icon must disappear when the `Innates` toggle is off, and stay on the same line as the hero name.

### Sticky divider overlays

- The vertical blue sticky-divider line must clamp to the real visible table bottom, not the full scroll-box bottom. This prevents the line from hanging below short filtered result sets.
- Divider visibility must depend on real horizontal overflow plus `scrollLeft > 0`, not just `scrollLeft > 0` in isolation.
- In `heroes_dyn.html`, turning `Hide old` on resets `scrollLeft` to `0` before re-anchoring the divider. Anchor the divider from the sticky `Hero` header cell, not from a body row.

### Источники данных по рельефу (terrain)
Главные источники координат карты (деревья/кэмпы/башни/тормент/гейты/лотосы по версиям):
- **Интерактивная карта**: https://tools.spectral.gg/interactive-map
- **GitHub с координатами**: `leamare/dota-interactive-map` — `assets/data/<ver>/mapdata.json` (per-version coords) + корневой `worlddata.json` (мировые границы для проекции). Дифф считает `scripts/build_terrain_diff.py` → `data/terrain_diff.json`. Проекция: мир ∈ [−10464, 10400] → 1280px (проверено наложением всех деревьев на рендер карты).

### Навигационные стрелки (ПРАВИЛО)
Все **навигационные / направленные стрелки** на сайте должны использовать единый дизайн: сплошной **пиксельный SVG-треугольник** (`shape-rendering=crispEdges`, золото `#e3c46a`) на золото-кожаном кружке (`linear-gradient(180deg,#3b2e1d,#2a2014)`, рамка `2px solid #e3c46a`). Эталон — `.back-to-top` / `.nav-back-arrow` / `.version-nav-arrow` (`is-prev`/`is-next`). Это касается и стрелок слайдера terrain (`.tc-chev-l/.tc-chev-r` переиспользуют те же data-URI пиксель-треугольники). НЕ использовать CSS-border-треугольники, юникод-стрелки (▲◄►) или эмодзи для навигации.

### Глобальные UI-элементы (во всех страницах через `site_common.py` / `scripts.js`)
- **Лого** — простой `<img class="nav-brand-logo" src="…/icons/logo_knight.png">` (пиксельный рыцарский шлем, прозрачный фон). Раньше был шлем `header-helmet.png` с canvas-эффектом EyeFire — удалён целиком (файлы + код).
- **Плавающие кнопки** `.nav-back-arrow` (назад в календарь/патч, низ-слева) и `.back-to-top` (низ-справа) — золото/кожа кружок (стиль index) + сплошной пиксельный SVG-треугольник (как `.version-nav-arrow`). Обе во НИЖНИХ углах (back-стрелка раньше была top-left и налезала на теги; JS больше НЕ выставляет ей inline `top`).
