# Архитектура Sloppy

## Схема данных

```
data/<version>_datafeed.json   (датафид Valve, кэш)
        ↓
generate_patch_code_v2.py      (парсер → вызовы хелперов patch/)
        ↓
_generated_p_<version>_v2.py   (промежуточный файл, ревьюится вручную)
        ↓
content/p<version>.py          (ревьюнутый def build(); регистрируется в builders/patch.py)
        ↓
builders/patch.py + patch/     (оркестратор запускает каждый content.build())
        ↓
patches/<version>.html         (финальный сайт)
```

## Пакет `patch/`

Старый монолит `build_patch.py` распилен на пакет; контент патчей переехал в
`content/` (по файлу на версию). Хелперы импортируются через `from patch.api import *`.

| Модуль | Что делает |
|---|---|
| `patch/images.py` | CDN-константы, `HERO_SLUG` / `ITEM_SLUG` (имя → слаг) |
| `patch/badges.py` | `gradient_class()`, `b()`, `br()`, `bf()`, `t()`, `scale_pill()` |
| `patch/elements.py` | HTML-хелперы: `hero_header()`, `item_header()`, `section()`, `ability()`, `li()`, `subnote()`, … |
| `patch/output.py` / `patch/state.py` | `W()`-аккумулятор + синглтон состояния `_State` |
| `patch/page.py` | `write_head()` / `write_footer()` / `save_html()`; читает `styles.css` + `src/scripts.js` с диска, проставляет cache-busting `?v=` |
| `patch/meta.py` | `PATCHES`, `RELEASE_HISTORY`, nav / даты |
| `patch/rosters.py` | ростеры героев/предметов, пишет `_dynamics.json` |
| `patch/index_page.py` / `patch/calendar.py` | лендинг «инвентарь-книга» + календарь/инфографика |
| `content/p<version>.py` | контент патча — `def build()` |
| `builders/patch.py` | оркестратор: импортит все `content`-модули и зовёт `build()` от старых к новым |

## generate_patch_code_v2.py — как работает

1. Грузит датафид JSON (`data/<version>_datafeed.json`) + `itemlist.json` / `herolist.json`
2. Обходит секции (General → Items → Neutral Creeps → Neutral Items → Heroes) и дерево заметок каждой сущности, сохраняя иерархию `indent_level`, фасет-подсекции, aghanims-маркеры, info-уточнения
3. Применяет эвристику тегов (BUFF/NERF/REWORK/MISC/QoL/NEW/DEL) + `l=True` для cost/BAT/cooldown/manacost/cast-point
4. Выдаёт строки типа `W(li("Mana cost reduced from 100 to 80", b(100, 80, l=True)))` и пишет `_generated_p_<version>_v2.py`

## Как CSS и JS попадают в HTML

`styles.css` (корень) и `src/scripts.js` — **редактируемые вручную source-файлы**, общие для всех страниц. Они **линкуются, а не встраиваются**: патч-страницы ссылаются на `../styles.css?v=…` / `../src/scripts.js?v=…`, корневые — относительно корня. `patch/page.py` читает их с диска и проставляет cache-busting `?v=` — правка в одном месте, копия никуда не встраивается.

## Иконки способностей — fallback при отсутствии файла

`ABIL_CDN` указывает на локальное зеркало `../icons/abilities/`. Если локального PNG для слага нет (у большинства innate-способностей нет публичной CDN-иконки), `ability()` рендерит fallback **сразу как `<img src>`** (innate → `innate_icon.png`, иначе → `missing.svg`), а не «битый путь + onerror» — иначе поиск (читает `img.src`) показывал не ту иконку. Набор имеющихся файлов кэшируется в `_LOCAL_ABIL_ICONS` при загрузке модуля.

## Прочие генерируемые страницы

`builders/patch.py` также пишет `index.html` (инвентарь-лендинг) и `calendar.html` (календарь + инфографика). Таблицы (`neutral_stats.html`, `neutral_abilities.html`, `mana_items.html`) собирают отдельно `builders/creeps.py` / `builders/mana_items.py` — запускать ПОСЛЕ `builders/patch.py` (см. [tables.md](../tables.md)).
