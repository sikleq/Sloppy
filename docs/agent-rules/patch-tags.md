# Patch-теги и строки изменений

Правила тегирования (`b()`/`t()`/`bf()`), порядка строк и канонических фраз для патч-страниц (`builders/patch.py`).

## Хелперы для строк изменений
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

## Порядок строк внутри `ul` (системное правило)

Все `W(li(...))` внутри одного `ul_open()` … `ul_close()` блока **сортируются по типу тега** в этом порядке (применимо к любой сущности — герои, предметы, чары, способности, нейтралы и т.д.):

1. **Числовые бейджи** — `b()`, `br()`, `bf()`, `bstat_h()`, `bstat_i()` (BUFF / NERF / %-дельты). Внутри группы порядок берётся из патчноута.
2. **`t("NEW")`** — добавление нового поведения/свойства/эффекта.
3. **`t("REWORK")`** — структурные изменения (смена тира, ограничение доступности, изменение механики).
4. **`t("DEL")`** — удаления.
5. **`t("QoL")`** — удобство/quality-of-life (сгруппировано перед MISC).
6. **`t("MISC")`** — всё прочее, в хвосте.

Применять даже если в исходном патчноуте Valve порядок другой — переставлять при наполнении блока. Примеры в коде: Crippling Crossbow, Jidi Pollen Bag, Crude.

### Авто-сортировка (per-ability, не нарушать)

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

## Канонические фразы и спецслучаи тегов

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

Когда патчноут говорит `"Innate ability reworked"` — это **обязательно** `ability_change(...)`, не две плоские `t("MISC")` строки. Старое описание лифтится из патча, который ввёл текущий innate (грепать `hero_innate_<entity>_<ability>` в `patchnotes_english.txt`). Генератор `generate_patch_code.py` теперь пишет `# TODO[innate-rework]:` маркер — никогда не оставлять его в коммите.

### Иконки-чипы → нужны hover-тултипы (если рядом нет пояснения)

Когда строка показывает список иконок-чипов (предметы, способности, сувениры и т.п.), каждый чип должен нести `data-tooltip="..."` с описанием эффекта, **если** рядом с чипом нет inline-текста, объясняющего что он делает.

- **Тултип нужен**: чип = иконка + имя (Ringmaster Dark Carnival souvenirs — игрок не знает, что делает «Funhouse Mirror»).
- **Тултип НЕ нужен**: рядом уже есть текст эффекта (раздел **Enchantment Changes** — у каждой чары перечислены бонусы рядом с чипом).

HTML-escape тултип через `_html.escape(text, quote=True)`. CSS `.enchant-chip[data-tooltip]::after` уже стилизует popup.
