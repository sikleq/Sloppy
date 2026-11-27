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
- `src/js/*.js` (42 части, порядок склейки и файлы `dist/src/scripts-<вид страницы>.js` — `patch/js_bundle.py`: каждому виду страниц только его части, новую часть для немногих страниц вносить в `PART_MARKERS` и `JS_PAGES`, проверяет `tests/test_js_pages.py`) и `src/css/*.css` (склеиваются в `dist/styles.css`, `patch/css_bundle.py`) — единственный источник правды для стилей и поведения всех страниц (включая `index.html` и `calendar.html`). Редактируй напрямую — IDE/linter работают нормально. `build_site.py` минифицирует их в `dist/` при сборке.
- **Порядок частей `src/css` — это каскад, его не менять.** Правило добавлять в часть своего раздела. Чтобы изменить вид, править существующее объявление, а не дописывать новое ниже: `python tools/css_dead_rules.py` показывает объявления, которые уже ни на что не влияют. `colorblind.generated.css` пишет `scripts/gen/gen_colorblind_css.py`, руками не править.
- Сгенерированные HTML (`dist/patches/7.41d.html` и т.д.) — результат запуска `python build_site.py`, не редактируй вручную.
- Все патч-файлы лежат в `dist/patches/` (не в корне), поэтому их CSS/JS подключаются через `../styles.css`, `../src/scripts-<kind>.js` (kind: base, home, changes, entity, lab, table; `patch/js_bundle.py`).

## Таблицы — одинаково на всех страницах (владелец 2026-11-22)

Любая таблица сайта (Materials и таблицы механик на патчах). Подробно — `docs/agent-rules/ui-style.md`, раздел
«Таблицы — единые правила». **Эталон — `units_stats.html`** (владелец 2026-11-22: «делай везде так, оттуда
правила»): при сомнении смотреть, как сделано там, и делать так же. Тестов на это нет и не нужно: перед отчётом пройти страницы одним скриптом в браузере.
- Таблица сразу под своим тулбаром; блок над ней (карточки) компактный, без пустых зазоров, и на телефоне тоже.
- Липкая шапка — вплотную под шапкой сайта, без щели (sticky на всей `thead`).
- Названия заголовков всегда по центру; ячейки по центру, столбец имени — слева (исключение: значки AoE Increase).
- Поле для числа (Upgrade в Unit Stats): без стрелок вверх-вниз (`type="text" inputmode="numeric"`), значение строго
  по центру поля (`padding:0`, `text-align:center`); игровое время шага — подсказкой при наведении на поле, не отдельно рядом (владелец 2026-11-26).
- Hero / Item Dynamics в режиме весов: строка — одна гладкая волна без разрывов; горб вверх = бафф, яма вниз = нерф,
  высота = сила правки; цвет — по правке ЭТОГО патча (не по стороне оси), патчи без правок — тусклая серая линия
  (владелец 2026-11-24, `src/js/patch-dynamics.js` `dynDrawRowLines`).
- Страница героя / предмета: в шапке под именем — накопительный график силы (сумма весов правок по патчам, гладкий,
  точка зелёная/красная по правке патча, клик — к патчу); меньше 3 патчей с правками — графика нет; на телефоне
  подписан каждый 2–3-й патч (владелец 2026-11-24, `src/js/entity-curve.js`, `entity_changes._curve_box`).
- Страница героя / предмета: фильтры — карточка справа, как на патчах (`entity_changes._rail`): теги и разделы в один
  столбец шрифтом как на патчах, разделы квадратными галочками (Shard / Scepter без слова Aghanim), способности — сетка значков по 5, удалённые
  под «Removed»; кнопки в углу — общий `corner-dock` с поиском (одна строка на имя). Выбранная иконка способности — золотое кольцо 2px со свечением;
  выбранные предметы прячет кнопка «Items» среди разделов, не удаляя их; способность, которую игра выдаёт из кода (Martyrdom у Зелота Chen), — не
  removed: `data/rules/abilities_granted_in_code.json` (владелец 2026-11-24).
- Шапка в два этажа как Hero Stats: `tr.cat-row` + `th.cat-head`, столбец без группы — `th.th-tall rowspan=2`.
- Столбец имени сортируется, со значком; светится при наведении только сортируемый заголовок.
- Линии 1px только цветами `var(--tbl-col-line)` / `var(--tbl-row-line)` (`tokens.css`); 2px только у смысловой границы.
- Сортируются все столбцы с одним видом значений; ячейка с числом и подписью — с `data-sort`. Сортировщик один
  (`mana-items.js`, `.mr-table` и `.ts-table`), свой не писать. Текстовый столбец (имя) первым кликом — A→Z, не Z→A
  (владелец 2026-11-27; `creeps-table.js` тоже).
- Unit Stats: на 1600 px таблица Standard влезает без прокрутки (поля ячеек 6px, заголовков 4px); на телефоне тулбар в
  4 строки, Melee / Ranged — одни значки (владелец 2026-11-27).
- Перед новой таблицей прочитать «Грабли» в разделе таблиц `ui-style.md`: там всё, что уже ломалось.
- **Владелец уточнил оформление или поймал ошибку вида — в том же коммите дописать правило** сюда (коротко) и в
  `docs/agent-rules/ui-style.md` (подробно, в «Грабли», с датой и словами владельца). Противоречащее старое правило
  исправить, а не оставить рядом. Любая сессия, не только основная.
- Ячейка имени: `td.mr-name.hs-name` + `img.mr-ico` (растёт при наведении); значок способности — подсказка сайта.
- Имя в любой таблице — ссылка на страницу героя / предмета / юнита (`mr_table.hero_href` / `item_href`, только
  если страница есть); способность ведёт на страницу своего героя.
- Кнопка «Removed» — общая `hs-attack-filter`; карточки и кнопки рядом — рамка из `src/css/pixel-skin.css`.
- Телефон: таблица листается внутри своего блока, лишний столбец сжимать до нуля, не `display:none`.
- Выделенная по клику строка — сплошная золотая рамка вокруг всей группы строк одного имени, без разрывов у ячеек с rowspan.
- Новые стили не писать с нуля: брать классы Hero Stats / `.mr-table`. Шапку и ячейку имени новой таблицы строить
  общей деталью `builders/mr_table.py` (`th`, `group_th`, `thead`, `name_cell`, `icon`) — на ней Hero Stats, Mana Items (`grid=True`), Item Potency,
  Dormant Curio, AoE Increase.

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
  `python tools/lint_tags.py content/p<version>.py`.
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
