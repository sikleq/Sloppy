# Sloppy — Dota 2 patch notes site

## Старт сессии — прочитай это

**Язык общения:** отвечай пользователю на русском (триггер `session_go` и работа над Sloppy в целом).

Сайт = две подсистемы: (1) аннотированные патчноуты и (2) сортируемые таблицы под разделом Materials. Общие `styles.css` / `scripts.js`.

Чтобы сразу быть в контексте, в начале сессии прочитай:
- `AGENTS.md` (этот файл) — source of truth + карта правил.
- `docs/architecture.md`, `docs/workflow.md`, `docs/data-format.md` — конвейер **патч-страниц** (`builders/patch.py`).
- `docs/tables.md` — подсистема **таблиц** (Neutral Creeps + вложенная Neutral Abilities / Mana Items: `builders/creeps.py`, `builders/mana_items.py`, sticky/overlay-архитектура, история ячеек, грабли).

## ВАЖНО: source of truth

`builders/patch.py` — **главный файл патч-страниц**. CSS и JS читаются с диска при старте: `styles.css` и `scripts.js` — это **source files**, редактируются напрямую.
- `scripts.js` и `styles.css` — единственный источник правды для стилей и поведения всех страниц (включая `index.html` и `calendar.html`). Редактируй напрямую — IDE/linter работают нормально.
- Сгенерированные HTML (`patches/7.41c.html` и т.д.) — результат запуска `python builders/patch.py`, не редактируй вручную.
- Все патч-файлы лежат в `patches/` (не в корне), поэтому их CSS/JS подключаются через `../styles.css`, `../scripts.js`.

## Карта правил агента (`docs/agent-rules/`)

Подробные правила вынесены в модули — читай нужный перед соответствующей задачей:

| Задача | Модуль |
|---|---|
| Теги/бейджи (`b()`/`t()`), порядок строк, канонические фразы (penalty→BUFF, Aghs reworked, pool-style, innate reworked, `_info`→inline_note, чипы-тултипы) | [docs/agent-rules/patch-tags.md](docs/agent-rules/patch-tags.md) |
| Формулы, per-level, `li_formula`/`scale_pill`, сетка уровней, `effective_unchanged`, «per level up» vs «per level» | [docs/agent-rules/formula-tables.md](docs/agent-rules/formula-tables.md) |
| Заголовки сущностей, структура changes-блока, `ability_change` (внутри/снаружи + layout), `cm_draft`, `correction-note` | [docs/agent-rules/entity-rendering.md](docs/agent-rules/entity-rendering.md) |
| База статов (`stats DB`) + маппинг описаний → поля БД (`HERO_STAT_MAP`) | [docs/agent-rules/stats-db.md](docs/agent-rules/stats-db.md) |
| Вёрстка/стили: patch-page layering, toolbar-panel, Materials rhythm, regen columns, фильтры, Hero Stats, sticky dividers, навигационные стрелки, глобальный UI | [docs/agent-rules/ui-style.md](docs/agent-rules/ui-style.md) |
| Структура проекта, как запустить, прочие страницы (index/calendar/terrain), грабли | [docs/agent-rules/pages-and-pipeline.md](docs/agent-rules/pages-and-pipeline.md) |

Узкоспециальные правила:
- `docs/captains-mode.md` — полное правило **Captains Mode** (`cm_draft`, кодировка `F/S/f/s`).
- `docs/formula-change.md` — блок `formula_change` для важных **игровых формул** (Assist Gold, Experience…).
- `docs/terrain.md` — полный план и TODO terrain-страницы.
