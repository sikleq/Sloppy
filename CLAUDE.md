# Sloppy — Dota 2 patch notes site

## ВАЖНО: source of truth

`build_patch.py` — **главный файл патч-страниц**. CSS и JS для них встроены прямо в него.
- `scripts.js` и `styles.css` — отдельные файлы для `index.html` и `calendar.html`. Редактировать их можно, они не перезаписываются.
- Чтобы изменить стиль или поведение **патч-страниц** — редактируй `CSS`/`SCRIPT` строки внутри `build_patch.py`, а не `styles.css`/`scripts.js`.
- Сгенерированные HTML (`patches/7.41c.html` и т.д.) — результат запуска `python build_patch.py`, не редактируй вручную.
- Все патч-файлы лежат в `patches/` (не в корне), поэтому их CSS/JS подключаются через `../styles.css`, `../scripts.js`.

## Структура проекта

```
build_patch.py            ← ГЛАВНЫЙ. CSS, JS, HTML-хелперы, данные всех патчей
generate_patch_code.py    ← KV → Python-код. Запускать перед добавлением нового патча
apply_stats_to_build.py   ← Постпроцессор: t("BUFF")→bstat_h() где есть БД
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
python apply_stats_to_build.py        # упгрейдит t() → bstat_h() где можем
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

## Предупреждения и подводные камни

- При добавлении нового героя: добавить в `HERO_SLUG` (build_patch.py) И в `load_hero_internal_to_display()` (generate_patch_code.py)
- При добавлении нового предмета: только в `ITEM_SLUG` (build_patch.py); generate_patch_code.py читает оттуда
- 7.41c в HANDCRAFTED раньше был сырой HTML — теперь конвертирован в W() вызовы; следующие патчи делать только через W()
- `_formula_id_counter` — глобальный счётчик для table-id, сбрасывается при каждом запуске
- `.gitignore` исключает `__pycache__/`, `_generated_p_*.py`, `_insert_patches.py`. Одноразовые скрипты `_*.py` после использования можно удалять
- 7.08 — патч слишком старый для stats DB (muk-as начался с 7.33), он остаётся с t() fallback
