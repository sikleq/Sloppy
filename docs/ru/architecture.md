# Архитектура Sloppy

## Схема данных

```
data/patchnotes_english.txt   (Valve KV)
        ↓
generate_patch_code.py        (парсер → Python-код)
        ↓
_generated_p_<version>.py     (промежуточный файл, ревьюится вручную)
        ↓
build_patch.py                (интегрируется вручную + CSS + JS + хелперы)
        ↓
7.41c.html                    (финальный сайт)
```

## build_patch.py — содержимое

Файл построен по секциям сверху вниз:

| Секция | Что делает |
|---|---|
| CDN-константы | URL для картинок героев/предметов/способностей |
| HERO_SLUG / ITEM_SLUG | Маппинг отображаемых имён → CDN-слаги |
| Градиент-хелперы | `gradient_class()`, `b()`, `br()`, `bf()`, `t()` |
| HTML-хелперы | `hero_header()`, `item_header()`, `section()`, `ability()`, `li()`, `subnote()` |
| Загрузка CSS/JS | `styles.css` и `JS_TEXT` **читаются с диска** из standalone-файлов `styles.css` / `scripts.js` при загрузке модуля — это **source-файлы**, редактируются вручную, НЕ генерируются |
| Scaffold | `W()` writer, HTML-обёртка, nav, фильтры |
| Контент патча | Секции General / Items / Heroes с вызовами хелперов |
| `save_index_html` | Лендинг — игровой «инвентарь-книга» (слоты gothic pixel UI → ссылки на разделы) |
| `save_calendar_html` | Календарь + кастомный год-пикер + полоса-инфографика «Patch cadence» (SVG-sparkline) |

## generate_patch_code.py — как работает

1. Читает `data/patchnotes_english.txt`
2. Ищет строки вида `"DOTA_Patch_7_41c_<ключ>" "<значение>"`
3. `parse_key()` — разбирает ключ на тип (герой/предмет/general/etc.) и entity
4. `parse_value_change()` — пытается извлечь "from X to Y", формулу, range, или угадывает тег
5. Выдаёт Python-строки типа `W(li("Mana cost reduced from 100 to 80", b(100, 80, l=True)))`
6. Пишет в `_generated_p_<version>.py`

## Как CSS и JS попадают в HTML

`styles.css` и `scripts.js` в корне репо — **редактируемые вручную source-файлы**, общие для всех страниц. Они **линкуются, а не встраиваются**: патч-страницы ссылаются на `../styles.css?v=…` / `../scripts.js?v=…`, корневые страницы (`index.html`, `calendar.html`, `neutral_stats.html`, …) — на `styles.css?v=…` / `scripts.js?v=…`. `build_patch.py` читает их с диска при загрузке (например в `JS_TEXT`) и проставляет cache-busting `?v=` — правка в одном месте, копия никуда не встраивается.

## Иконки способностей — fallback при отсутствии файла

`ABIL_CDN` указывает на локальное зеркало `../icons/abilities/`. Если локального PNG для слага нет (у большинства innate-способностей нет публичной CDN-иконки), `ability()` рендерит fallback **сразу как `<img src>`** (innate → `innate_icon.png`, иначе → `missing.svg`), а не «битый путь + onerror» — иначе поиск (читает `img.src`) показывал не ту иконку. Набор имеющихся файлов кэшируется в `_LOCAL_ABIL_ICONS` при загрузке модуля.

## Прочие генерируемые страницы

`build_patch.py` также пишет `index.html` (инвентарь-лендинг) и `calendar.html` (календарь + инфографика). Таблицы (`neutral_stats.html`, `neutral_abilities.html`, `mana_items.html`) собирают отдельно `build_creeps.py` / `build_mana_items.py` — запускать ПОСЛЕ `build_patch.py` (см. [tables.md](../tables.md)).
