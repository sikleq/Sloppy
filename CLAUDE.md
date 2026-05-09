# Sloppy — Dota 2 patch notes site

## ВАЖНО: source of truth

`build_patch.py` — **главный файл патч-страниц**. CSS и JS для них встроены прямо в него.
- `scripts.js` и `styles.css` — отдельные файлы для `index.html` и `calendar.html`. Редактировать их можно, они не перезаписываются.
- Чтобы изменить стиль или поведение **патч-страниц** (`7.41c.html` и т.д.) — редактируй `CSS`/`SCRIPT` строки внутри `build_patch.py`, а не `styles.css`/`scripts.js`.
- Сгенерированные HTML (`7.41c.html` и т.д.) — результат запуска `build_patch.py`, не редактируй вручную.

## Структура проекта

```
build_patch.py          ← ГЛАВНЫЙ файл. Всё в одном: CSS, JS, HTML-хелперы, данные патча
generate_patch_code.py  ← Парсит Valve KV-формат → генерирует Python-код для build_patch.py
data/
  patchnotes_english.txt  ← Сырые патчноуты от Valve (KV формат)
  patchnotes_russian.txt  ← Русский перевод
  items.txt               ← Данные по предметам
docs/
  architecture.md         ← Как всё устроено
  data-format.md          ← API хелперов и формат данных
  workflow.md             ← Как добавить новый патч
```

## Как запустить

```bash
python build_patch.py > 7.41c.html     # собрать текущий патч
python generate_patch_code.py 7.42     # сгенерировать код из KV-файла
```

## Ключевые концепции

- **Бейджи** — цветные метки в % для числовых изменений: `b(old, new)` или `b(old, new, l=True)` (l=True = меньше лучше, для кулдаунов)
- **Текстовые теги** — `t("BUFF")`, `t("NERF")`, `t("REWORK")`, `t("MISC")`, `t("NEW")`, `t("QoL")`
- **Формульные бейджи** — `bf()` для scale-with-level изменений, создаёт раскрывающуюся таблицу
- **entity-block** — каждый герой/предмет оборачивается в блок через `hero_header()` / `item_header()`
- **ITEM_SLUG в build_patch.py** — также читается в `generate_patch_code.py` (line 81-87), добавлять новые предметы надо туда

## База статов (stats DB)

Файлы `data/stats/{version}/heroes.json` и `items.json` — распарсенные поля из npc_heroes.txt / items.txt за каждый патч. Скачиваются через `D:\Sloppy Patches\fetch_stats.py`.

### Хелперы для авто-бейджей из БД

```python
# Получить значение стата напрямую
old = stat_h("Doom", "ArmorPhysical", "7.41")        # → 4
old = stat_i("Blink Dagger", "ItemCooldown", "7.41") # → 14

# Авто-бейдж: delta = разница (new - old). patch_before = версия ДО патча
W(li("Base Armor decreased by 1", bstat_h("Doom", "ArmorPhysical", "7.41", -1)))
W(li("Cooldown decreased from 14 to 12", bstat_i("Blink Dagger", "ItemCooldown", "7.41b", -2, l=True)))
```

Ключи из npc_heroes.txt: `ArmorPhysical`, `AttackDamageMin/Max`, `AttackRate`, `MovementSpeed`,
`AttributeBaseStrength/Agility/Intelligence`, `AttributeStrengthGain/AgilityGain/IntelligenceGain`,
`StatusHealth`, `StatusMana`, `StatusHealthRegen`, `StatusManaRegen`.

Ключи из items.txt: `ItemCost`, `ItemCooldown`, `AbilityManaCost`, `AbilityCooldown`.

Если стат не найден (ещё нет файла за ту версию) — fallback на `t("BUFF")`/`t("NERF")`.

## Предупреждения

- При добавлении нового героя: добавить в `HERO_SLUG` (build_patch.py) И в `load_hero_internal_to_display()` (generate_patch_code.py)
- `l=True` — флаг «меньше = лучше»: cooldown, mana cost, cast point, gold cost и т.д.
- `_formula_id_counter` — глобальный счётчик для уникальных ID таблиц, сбрасывается при каждом запуске
