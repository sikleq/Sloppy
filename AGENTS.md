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
python generate_patch_code.py 7.42   # → _generated_p_7.42.py (вставлять в build_patch.py)
python scripts/apply_stats.py          # упгрейдит t() → bstat_h() где можем
```

## Ключевые концепции

### Хелперы для строк изменений
- `b(old, new, l=False)` — числовой бейдж в %. `l=True`: меньше = лучше (cooldown, mana cost, BAT, gold cost, penalty, channel time, recharge, cast point)
  - **Исключение**: «X Cooldown Reduction», «X Mana Cost Reduction», «Cooldown Advance» — это **значения талантов**, НЕ применять l=True
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
5. **`t("MISC")` / `t("QoL")`** — всё прочее, обычно в хвосте.

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
6. **MISC / QoL** (rank 6) — `t("MISC")`, `t("QoL")`
7. **Untagged** (rank 7) — структурные/описательные строки, остаются в хвосте

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

### Глобальные UI-элементы (во всех страницах через `site_common.py` / `scripts.js`)
- **Лого** — простой `<img class="nav-brand-logo" src="…/icons/logo_knight.png">` (пиксельный рыцарский шлем, прозрачный фон). Раньше был шлем `header-helmet.png` с canvas-эффектом EyeFire — удалён целиком (файлы + код).
- **Плавающие кнопки** `.nav-back-arrow` (назад в календарь/патч, низ-слева) и `.back-to-top` (низ-справа) — золото/кожа кружок (стиль index) + сплошной пиксельный SVG-треугольник (как `.version-nav-arrow`). Обе во НИЖНИХ углах (back-стрелка раньше была top-left и налезала на теги; JS больше НЕ выставляет ей inline `top`).
