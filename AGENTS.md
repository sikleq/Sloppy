# Sloppy — Dota 2 patch notes site

## Старт сессии — прочитай это

**Язык общения:** отвечай пользователю на русском (триггер `session_go` и работа над Sloppy в целом).

Сайт = две подсистемы: (1) аннотированные патчноуты и (2) сортируемые таблицы под разделом Materials. Общие `styles.css` / `src/js/*.js`.

Чтобы сразу быть в контексте, в начале сессии прочитай:
- `AGENTS.md` (этот файл) — source of truth + карта правил.
- `docs/architecture.md`, `docs/workflow.md`, `docs/data-format.md` — конвейер **патч-страниц** (`build_site.py` → `builders/build_patches.py` → `content/p*.py`).
- `docs/tables.md` — подсистема **таблиц** (Neutral Creeps + вложенная Neutral Abilities / Mana Items: `builders/creeps.py`, `builders/mana_items.py`, sticky/overlay-архитектура, история ячеек, грабли).

## ВАЖНО: source of truth

`build_site.py` — **единственный entrypoint сборки**. Он запускает все builders (patches, creeps, mana items, hero lab, terrain, silent, …). `builders/build_patches.py` сам авто-обнаруживает `content/p*.py` — ручной регистрации нового патча в builders/ не требуется (только `patch/meta.py`).
- `src/js/*.js` (40 частей, порядок склейки и файлы `dist/src/scripts-<вид страницы>.js` — `patch/js_bundle.py`: каждому виду страниц только его части, новую часть для немногих страниц вносить в `PART_MARKERS` и `JS_PAGES`, проверяет `tests/test_js_pages.py`) и `src/css/*.css` (склеиваются в `dist/styles.css`, `patch/css_bundle.py`) — единственный источник правды для стилей и поведения всех страниц (включая `index.html` и `calendar.html`). Редактируй напрямую — IDE/linter работают нормально. `build_site.py` минифицирует их в `dist/` при сборке.
- **Порядок частей `src/css` — это каскад, его не менять.** Правило добавлять в часть своего раздела. Чтобы изменить вид, править существующее объявление, а не дописывать новое ниже: `python tools/css_dead_rules.py` показывает объявления, которые уже ни на что не влияют. `colorblind.generated.css` пишет `scripts/gen/gen_colorblind_css.py`, руками не править.
- Сгенерированные HTML (`dist/patches/7.41d.html` и т.д.) — результат запуска `python build_site.py`, не редактируй вручную.
- Все патч-файлы лежат в `dist/patches/` (не в корне), поэтому их CSS/JS подключаются через `../styles.css`, `../src/scripts.js`.

## Карта правил агента (`docs/agent-rules/`)

Подробные правила вынесены в модули — читай нужный перед соответствующей задачей:

| Задача | Модуль |
|---|---|
| Теги/бейджи (`b()`/`t()`), порядок строк, канонические фразы (penalty→BUFF, Aghs reworked, pool-style, innate reworked, `_info`→inline_note, чипы-тултипы) | [docs/agent-rules/patch-tags.md](docs/agent-rules/patch-tags.md) |
| Формулы, per-level, `li_formula`/`scale_pill`, сетка уровней, `effective_unchanged`, «per level up» vs «per level» | [docs/agent-rules/formula-tables.md](docs/agent-rules/formula-tables.md) |
| Заголовки сущностей, структура changes-блока, `ability_change` (внутри/снаружи + layout), `cm_draft`, `correction-note` | [docs/agent-rules/entity-rendering.md](docs/agent-rules/entity-rendering.md) |
| Блок замены/реворка способности `ability_change(old, new)`: когда ставить, обе панели | [docs/agent-rules/ability-change.md](docs/agent-rules/ability-change.md) |
| Контент патч-страниц: DEL vs NERF, спецслучаи тегов, фразы, секции, нейтральные предметы, перечисления | [docs/agent-rules/content-rules.md](docs/agent-rules/content-rules.md) |
| База статов (`stats DB`) + маппинг описаний → поля БД (`_BSTAT_FIELD`, части генератора в `tools/patchgen`: см. `docs/architecture.md`) | [docs/agent-rules/stats-db.md](docs/agent-rules/stats-db.md) |
| Вёрстка/стили: patch-page layering, toolbar-panel, Materials rhythm, regen columns, фильтры, Hero Stats, sticky dividers, навигационные стрелки, глобальный UI | [docs/agent-rules/ui-style.md](docs/agent-rules/ui-style.md) |
| Структура проекта, как запустить, прочие страницы (index/calendar/terrain), грабли | [docs/agent-rules/pages-and-pipeline.md](docs/agent-rules/pages-and-pipeline.md) |

## Скиллы проекта (`.claude/skills/`)

- **`sloppy-patch`** — данные и содержание: новый патч целиком (файлы игры → тихие изменения → разметка
  `content/p<version>.py` → карта/Terrain/Oldgrowth → выпуск: доки, тесты, CI). Разметка — workflow с
  воротами (`references/annotate.md`), ядро — линтер канонических фраз:
  `python .claude/skills/sloppy-patch/lint_tags.py content/p<version>.py`.
- **`sloppy-visual`** — внешний вид: стиль сайта, иконки, визуальная проверка лёгким агентом.

Скиллы не дублируют правила, а ссылаются на `docs/agent-rules/*` и `docs/*.md`.

Узкоспециальные правила:
- `docs/captains-mode.md` — полное правило **Captains Mode** (`cm_draft`, кодировка `F/S/f/s`).
- `docs/formula-change.md` — блок `formula_change` для важных **игровых формул** (Assist Gold, Experience…).
- `docs/terrain.md` — полный план и TODO terrain-страницы.
- Вкладка календаря **Test servers** (сборки Experimental/Staging): `patch/branch_builds.py`, данные
  `data/branch_builds.json` от `scripts/fetch/fetch_branch_builds.py` (API Valve каждые 15 мин + журнал muk-as/DOTA2_WEB с 11.2023 + его канал t.me/DOTA_DM_SPAM с 10.2021,
  `.github/workflows/branch-builds.yml`); источник и его пределы — `docs/agent-rules/pages-and-pipeline.md`.
- `docs/todo.md` — отложенные задачи владельца (сравнение патчей, страница механик и проверка скрытых изменений).
  Только локально: в `.gitignore`, в публичный репозиторий не отправляется (владелец 2026-10-24).
