# Рендеринг сущностей

Заголовки, структура changes-блока, `ability_change`, `cm_draft` и `correction-note` для патч-страниц.

## Заголовки сущностей
- `hero_header(name)` — `/heroes/{slug}.png`. Slug из `HERO_SLUG` или fallback titlecase
- `item_header(name)` — `/items/{slug}.png`. Slug из `ITEM_SLUG`
- `enchant_header(name, slug)` — для нейтральных enchantments. URL = `/items/enhancement_{slug}.png`. Использовать вместо `plain_header` для Crude/Greedy/Tough и т.д.
- `unit_header(name, icon_url)` — отдельный юнит (Spirit Bear) с кастомным URL
- `plain_header(name)` — без иконки (Mechanics, Tormentor, Roshan, Map Objectives и т.п.)
- `ability(name)` — `<h4>` название способности. **БЕЗ префикса героя** в имени! «Penitence», не «Chen Penitence». Generate_patch_code.py делает это автоматически — fallback titlecase берёт только bare ability name (после `entity_` префикса)
- `subgroup(name)` — `<h4>` подгруппа («Talents», «Abilities», «Spirit Bear»)
- **Категория «Other»** — первый `ul_open()` сразу после `hero_header` авто-оборачивается в подгруппу «Other» (базовые/прочие статы героя, как Base Intelligence у Jakiro). Если в блоке ровно одна строка, общая иконка меняется на иконку под стат (`STAT_ICONS`/`STAT_DETECT_RULES`). **Изменения обзора героя (day/night vision) → иконка `icons/vision.png`** (детект по «night vision»/«day vision»/«vision»). Не делать vision/прочие статы отдельной `ability(...)` — это категория Other.

## Структура changes-блока
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

## `ability_change(old, new)` — что внутри / что снаружи блока

**Внутри панелей (`old.desc`, `new.desc`)** — только официальное описание способности (как в игре / в KV патча). Без отсебятины типа «Self-buff values nerfed:», «Encouraged X», «Pre-7.41 …».

**Снаружи swap-card** (через `W(ul_open()) / W(li(...)) / W(ul_close())` после `W(ability_change(...))`) — числовые изменения характеристик способности, которые «пережили» реворк: `Bonus Attack Speed decreased from X to Y`, `Cooldown changed from X to Y` и т.п.

**Inline-note к новой механике** — встраивать через `inline_note("...")` прямо в `new.desc=[]` (не через `W(subnote(...))` после блока — это рендерится ВНЕ карточки). Рендерер `_side` детектит ведущий `<div` и вставляет его как есть.

## `ability_change(old, new)` — выбор layout-режима

Логика в `builders/patch.py` `ability_change(...)` решает между тремя визуальными режимами по identity и количеству строк:

1. **`is-in-place`** — `old.name == new.name` И иконки совпадают (`slug`/`innate=True` оба). Правая шапка скрывается — показываем только одну (левую). Пример: Lion's To Hell and Back.
2. **`is-in-place is-new-taller`** — то же, но `len(new.desc) > len(old.desc)`. Правая панель `align-self: start`, без фейкового `padding-top` («много пустого пространства сверху» — баг, который мы зафиксили). Новый body начинается сразу с верха панели, параллельно старой шапке. Примеры: Primal Beast Colossal 7.41, Marci Special Delivery / Bodyguard 7.41.
3. **`compact-old` / `compact-new`** — разные identity И разница в строках ≥ 2. Меньшая панель центрируется.
4. **Plain symmetric** — всё остальное, обе шапки видны.

**Правило:** одинаковое имя+иконка → **ВСЕГДА** одна шапка (левая). Не показывать обе. Это явная просьба пользователя.

## Captains Mode (порядок драфта) → `cm_draft`

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

## `correction-note` фразировка (note_box со stats DB)

- Текст: `"Before this patch it was changed in <PATCH_LINK> (age)"`. Без двоеточия после `in` — это предлог, не лейбл.
- `<PATCH_LINK>` — клик ведёт на страницу патча (`{ver}.html`). Реализовано через хелпер `_patch_link(version)`. CSS-класс `.patch-link` (color inherit, dotted underline, hover синий).
- Возраст рендерится через `_format_age(days)`:
  - `< 365` дней → `"N days ago"`
  - `>= 365` дней → `"Y years M months ago"` (months скрыт если 0; singular/plural корректно)
- Лейбл `"Previously:"` — отдельный `<span class="correction-label">`.
