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

## Предупреждения

- При добавлении нового героя: добавить в `HERO_SLUG` (build_patch.py) И в `load_hero_internal_to_display()` (generate_patch_code.py)
- `l=True` — флаг «меньше = лучше»: cooldown, mana cost, cast point, gold cost и т.д.
- `_formula_id_counter` — глобальный счётчик для уникальных ID таблиц, сбрасывается при каждом запуске
