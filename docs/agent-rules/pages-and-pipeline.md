# Структура, запуск и прочие страницы

## Структура проекта

```
build_site.py                ← ЕДИНЫЙ entrypoint. python build_site.py [steps] [--latest]
builders/
  build_patches.py           ← Авто-обнаруживает content/p*.py + calendar + index
  silent.py                  ← Дифф KV-файлов (heroes/ + items/npc_units/npc_abilities.txt) → dist/patches/silent/*.html
  terrain.py                 ← terrain_<code>.html (сравнение карт; terrain_stats.py ← terrain_stats.html)
  creeps.py (+ creeps_common / creeps_history / creeps_abilities.py), heroes_stats.py, hero_lab.py,
  mana_items.py, heroes_dyn.py, items_dyn.py
  dyn_matrix_common.py       ← Общий код для динамических матриц
content/
  p739d.py, p739e.py, ...    ← Один файл на патч. def build() → save_html()
patch/                       ← ЯДРО: не импортирует builders/ и tools/ (тест tests/test_layers.py)
  api.py                     ← from patch.api import * — публичный API для content/*.py
  elements.py                ← Все хелперы: W(), li(), hero_header(), ability(), ...
  cards_*.py                 ← Карточки, вынесены из elements.py (тест tests/test_elements_split.py):
                               cards_hero_stats (render_hs_card), cards_aghs (Aghanim's), cards_item_abilities
                               (item_abilities_change, render_iab_card), cards_item_stats (properties_change,
                               components_change, render_cost_card), cards_ability_change (ability_change, new_ability)
  images.py                  ← ITEM_SLUG, HERO_SLUG, item_img(), abil_img()
  meta.py                    ← PATCHES список, RELEASE_HISTORY
  index_page.py              ← index.html + What's New popup
  site_common.py             ← Общий HTML-обвёртка (head/nav/foot) всех страниц
  kv.py                      ← Единственный разбор KV Valve + hero_ability_blocks (раскладка 7.41f+)
  game_files.py              ← Чтение хранилища файлов игры (dota-patch-files, env DOTA_FILES_DIR): сборка каждого патча с 7.08
  loc_history.py / item_ability_text.py ← Подсказки игры любого патча; тексты способностей предметов
  map_versions.py / terrain_index.py    ← Шаги карты; какие патчи получают страницу Terrain и что сдвинулось
tools/generate_patch_code_v2.py    ← Datafeed → Python scaffold. Канонический генератор.
tools/                       ← Только команды: new_patch.py (новый патч одной командой, docs/workflow.md),
                               game_files.py materialize (раскладка сырых файлов из хранилища), …
data/
  normalized/patches/*.json  ← JSON-артефакты (генерятся параллельно со scaffold)
  stats/{version}/           ← KV-файлы героев/предметов (для silent changes)
  itemlist.json              ← Имена + engine slug всех предметов (Valve datafeed)
  abilities_by_id.json       ← ability_id → (dname, slug) для ability()
dist/                        ← Финальный сайт (весь в .gitignore; CI собирает его с нуля)
```

Полная успешная сборка (`python build_site.py` без ключей) удаляет из `dist/` HTML-страницы, которые она не записала
(`build_site._prune_stale_pages`; копии `src/` и `icons/` не трогает). До 2026-10-05 там копились 142 страницы
выкинутых патчей/предметов/юнитов: локально они давали ложные ошибки ссылок и HTML, на сайт не попадали (CI собирает с
нуля). Частичная сборка (`python build_site.py patch`) ничего не удаляет.

**Производительность (замеры 2026-10-05, 7.41 — самая тяжёлая страница: 1,2 МБ HTML / 125 КБ gzip, 24 тыс. узлов):**
- Шрифты и фон патч-страниц — свои (`src/fonts`, `icons/ui/bg/patch_bg.jpg`), шрифты latin предзагружаются
  (`site_common.head_common`).
- `content-visibility: auto` на `.entity-block` **не включать**: загрузка 7.41 быстрее (0,3–0,4 с против 0,5–1,1 с),
  но containment делает блок рамкой для `position: fixed` потомков и обрезает их по краю блока. Внутри блока живут
  всплывашка полосы истории `.dyn-tip` (fixed, у каждого блока), CSS-подсказки `::after` у `.enchant-chip` /
  `.ao-icon` и, на телефоне, они же в `position: fixed`. (Копии `.info-pop` в строках не мешают — они всегда
  скрыты, «?» показывает общий `.info-pop-body` на `body`; поправка 2026-10-06.) Включать только после переноса
  `.dyn-tip` и `::after`-подсказок в общий слой на `body`.
- Встроенные `onerror` у картинок — 60 КБ сырого HTML, но после gzip ~3 КБ: переделка на общий обработчик того не стоит.

## Добавление нового патча — полный workflow

С 2026-10-21 всю сторону данных делает одна команда — `tools/new_patch.py` (шаги и возобновление — в её docstring
и в `docs/workflow.md`; навык `sloppy-patch` ведёт по всему выпуску):

```bash
python tools/new_patch.py 7.42 21.10.2026 --dry-run   # план, ничего не меняет
python tools/new_patch.py 7.42 21.10.2026             # строка RELEASE_HISTORY, файлы игры, хранилище, черновик, сборка
# вычитать черновик _generated_p_7.42_v2.py в content/p742.py, затем:
python tools/new_patch.py 7.42 --from enchant
```

- Регистрировать патч руками не нужно: `new_patch.py` пишет строку в `RELEASE_HISTORY` (`patch/meta.py`), список
  `PATCHES` выводится из неё сам, `builders/build_patches.py` сам находит `content/p*.py`.
- Недостающие иконки способностей: `python scripts/fetch/fetch_icons.py`, затем `python tools/make_thumbs.py`
  (миниатюры; `new_patch.py` делает это шагом `thumbs`).
- Перед коммитом — полная сборка `python build_site.py`, `python -m pytest -q`, `python tools/ci_local.py`.

## Известные ловушки генератора (tools/generate_patch_code_v2.py)

### Enchantment items → enchant_header, не item_header
Генератор автоматически использует `enchant_header()` когда engine slug начинается с `enhancement_`.
Если в старом scaffold стоит `item_header("Brawny")` — заменить на `enchant_header("Brawny")`.
Иконка: `icons/items/enhancement_brawny.png` (не `brawny.png`).

### Предметы с несовпадающим display name и engine slug
`item_img("Parasma")` ищет `parasma.png`, но Valve хранит как `devastator.png`.
Генератор печатает `[WARN]` при таких случаях.
**Фикс:** добавить в `ITEM_SLUG` в `patch/images.py`: `"Parasma": "devastator"`.
Примеры уже в ITEM_SLUG: Khanda→angels_demise, Book of the Dead→demonicon, Parasma→devastator.

### Жизненный цикл Facets

**Введены в 7.36** (`"This update introduces two new mechanics for each hero: Innate abilities and Facets"`)
**Удалены в 7.41** (`"Facets removed from the game"`)

Значит `facet_header(...)` и facet-блоки применяются **только в патчах 7.36 – 7.40c** включительно.
В патчах до 7.36 и начиная с 7.41 — facet-секций нет.

### Facet slugs отсутствуют в FACETS → невидимый блок
`facet_header(slug)` возвращает HTML-комментарий если slug не найден в `FACETS` (`patch/badges.py`).
Блок facet рендерится невидимым без каких-либо ошибок сборки.

**Фикс при создании нового патча:** для каждого `facet:*` scope из JSON убедиться что slug есть в FACETS.
Если нет — добавить блок в `patch/badges.py`:
1. Имя: `grep -i "Tooltip_Facet_{slug}\"" data/abilities_english.txt` (строка без `_Description`)
2. Цвет: `data/facets_icons.json` → первый элемент массива для slug (например `"Gray3"`)
3. Добавить в соответствующий патч-блок: `"slug": ("Display Name", "Color")`

### Иконки способностей не скачиваются автоматически
`fetch_icons.py` нужно запускать вручную после каждой новой сборки патча.
**Нет на CDN — ищем в файлах игры** (владелец 2026-10-26): `fetch_icons.py` сам пробует KV `AbilityTextureName`
(значок, который рисует игра: 7.41 Squee's Scope = Stasis Trap) на CDN и в VPK, затем
`panorama/images/spellicons/<slug>_png.vtex_c` в `pak01_dir.vpk`. В `KNOWN_INNATE_NO_CDN_ICON` — только то, чего нет и
там, с пометкой «not in the client VPK nor the CDN» и датой.
Иконки innate/facet без арта в игре — нормально: `ability()` отдаёт `innate_icon.png` сразу в `src`, без 404+onerror.
`_LOCAL_ABIL_ICONS` в `patch/images.py` строится при загрузке модуля — пересборка нужна после скачивания.

**Подтверждённые real-innate без CDN art** лежат в `patch/known_exceptions.py::KNOWN_INNATE_NO_CDN_ICON`.
Builders **не должны** молча подставлять `innate_icon.png` за любой отсутствующий slug — это спрячет случайно удалённую иконку от `check_icons.py`. Канон (см. `builders/aoe_increase.py`):
```
if local_png_exists:     use it
elif slug in allowlist:  emit innate_icon.png directly
else:                    raise RuntimeError
```

### Ability slug неправильный
Генератор берёт slug из `data/abilities_by_id.json`. Если способность переименована в новом патче,
нужно обновить `abilities_by_id.json`: `python -c "from tools.generate_patch_code_v2 import _refresh_abilities; _refresh_abilities()"`.

### Scaffold не включает write_head/write_footer/save_html
Генератор выдаёт только тело `build()`. Нужно вручную добавить:
```python
from patch.api import *

def build():
    write_head("7.42", "DD.MM.YYYY")
    # ... сгенерированный код ...
    write_footer()
    save_html('patches/7.42.html')
```

### terrain_link в plain_header("Terrain Changes")
Каждый патч с изменениями рельефа должен иметь `terrain_link=` в заголовке:
```python
W(plain_header("Terrain Changes", terrain_link="7.42"))
```
Иначе кнопка "View on Map" не появится на странице патча.

## Прочие команды

```bash
python build_site.py --latest      # только последний патч (patch step), ~3-4s
python build_site.py patch         # все патчи + calendar + index, ~6s
python build_site.py               # полная сборка всех страниц, ~60s
python scripts/fetch/fetch_itemlist.py  # обновить itemlist.json (с выходом патча)
python scripts/fetch/fetch_icons.py     # скачать недостающие иконки способностей
```

Локальный сервер (запустить один раз в отдельном окне или через Start-Process):
```powershell
Start-Process python -ArgumentList "-m http.server 8765 --directory dist"
```

## Предупреждения и подводные камни

- `_formula_id_counter` — глобальный счётчик для table-id, сбрасывается при каждом запуске
- `.gitignore` исключает `__pycache__/`, `_generated_p_*.py`. Одноразовые скрипты `_*.py` после использования можно удалять
- 7.08 — патч слишком старый для stats DB (muk-as начался с 7.33), он остаётся с t() fallback
- При добавлении нового героя: добавить в `HERO_SLUG` (`patch/images.py`)
- При добавлении предмета с нестандартным slug: добавить в `ITEM_SLUG` (`patch/images.py`)
- **Иконки способностей: fallback пишется в `src` напрямую.** Если локального файла `icons/abilities/<slug>.png` нет (множество innate-способностей не имеют публичной CDN-иконки), `ability()` рендерит fallback СРАЗУ как `src` (innate → `innate_icon.png`, иначе → `missing.svg`), а не «битый путь, который меняется через onerror». Набор существующих файлов — `_LOCAL_ABIL_ICONS` (строится при загрузке модуля). Пример-каноник: Timbersaw «Exposure Therapy» (+ ещё 27 innate)

## Прочие генерируемые страницы (не патчи)

`builders/build_patches.py` также генерирует:
- **`index.html`** (`save_index_html`) — лендинг в виде игрового «инвентаря-книги»: орнаментальная панель `.inv-book` с квадратными слотами (`icons/ui/gothic/`, пак [Gothic Pixel UI](https://abyssowl.itch.io/gothic-pixel-ui)). Верхний ряд `.inv-filled` = ссылки на разделы, нижний `.inv-ph` = плейсхолдеры. Золото подогнано под бренд-слово `sikle` (`#e3c46a`). Подписи — временные плейсхолдеры (шрифт Jersey 10). Старая `.zuma-*` сетка удалена.
- **`calendar.html`** (`save_calendar_html`) — календарь патчей + кастомный год-пикер (`.cal-year-picker`, не нативный `<select>`) + полоса-инфографика «Patch cadence» внизу (`_spark_svg`: SVG-sparkline, «красивая» 5-ступенчатая ось Y, gridlines/оси, hover-значения). Переключатель Compact живёт в шапке блока года.
  - **Вкладки Patches / Test servers (2026-11-10).** Над календарём две кнопки `.cal-view-tab` одной ширины (`VIEW_TABS` в `patch/calendar.py`; сетка с равными колонками, владелец: «симметрия»); `src/js/calendar-builds.js` меняет вид, `#test-servers` в адресе открывает второй. Страница грузит `scripts-calendar.js` (вид `calendar` в `JS_PAGES`). Вкладка Test servers (`patch/branch_builds.py`, `render_panel`) отвечает на вопрос владельца «через сколько после Staging вышел патч» и устроена как вид Patches, сверху вниз: календарь сборок — тот же блок, что на Patches (`builds_calendar`: `cal-year-block is-current`, свой выбор года `cal-year-picker` в шапке, пояснение цветов на месте Compact, одна сетка `cal-full-grid` на год, итог года в `cal-year-summary`; скрипт страницы в `calendar.py` обслуживает каждый выбор года и прячет только панели своего блока); у дня со сборками под числом точки: красно-оранжевая Experimental и золотая Staging, крупнее при 2 и 3+ сборках (`_dots`, `tb-d1..3`; владелец выбрал «Dots» из девяти макетов: половинки, столбики, квадратики, уголки, полосы, диагональ, числа в углах, полосы по краям, точки); у дня патча — фишка как на Patches с кольцом (золотым у целых) и точками под версией; подсказка дня — только таблица из двух строк в цветах серверов, без даты (`_count_table`); под календарём полоса-ответ в оформлении «Patch cadence» (`answer_strip`, `.cal-infographic`): медианы по целым патчам — через сколько после предпоследней и после последней сборки Staging выходит патч (обе золотом; владелец: последняя Staging часто приходит вместе с патчем, `staging_lag2`), за сколько до него вышла первая сборка Staging после предыдущего патча (`stg_first`; владелец 2026-11-10: «патч X вышел 10 ноября, все staging после его выхода и до выхода патча Y будут привязаны к патчу Y»; предыдущий патч — любой, и буквенный, `after_patch` в `group_by_patch`), за сколько начинается разгон Staging (только сборки после предыдущего патча) и Experimental; «Each patch» — таблица с линиями между ячейками и строками (`patch_card`: по умолчанию только целые патчи, кнопка All patches; фишка патча, крупно «после предпоследней Staging» (полоска до 7 дней, `LAG2_STAGING_CAP_H`) и «после последней Staging» (полоска до 48 ч, `LAG_STAGING_CAP_H`), «Первая Staging после предыдущего патча», «Staging начался за» и «Experimental начался за» на одной шкале дней, число сборок разгона цветными пилюлями); фильтр «From / To» стоит сразу под календарём, над полосой медиан, и действует на всё ниже: полосу (скрипт пересчитывает медианы по строкам целых патчей `data-lag2`…`data-lead`, как `medians()` и `fmt_short`; набор `WHOLE_ONLY` в скрипте держать в согласии с `medians()`), строки «Each patch» (`data-year`, пустой выбор — `.tb-plist-none`) и графики (владелец 2026-11-10; у календаря свой год); «Builds per week» (`weekly_svg`: вся история во всю ширину, Experimental вверх, Staging вниз, линия на патч, у целых подпись; числа на столбиках, когда неделя шире 14 px, `BAR_VALUE_MIN_COL`); часы и дни недели UTC. Подсказки недель и часов — заголовок и та же таблица из двух строк. Списка всех сборок и таблицы «By patch» больше нет (владелец: «много шума», «не читаемо»), как и ленты из рисок и строк разгона — к ним не возвращаться. Счёт — по номерам версий, не по обновлениям (владелец 2026-11-10: «считай номера версий»): обновление 3332 → 3338 даёт 6, откат на меньший номер или неизвестный номер — 1 (`versions`, поле `n` у сборки, сумма `nv`); так считают точки дня, подсказки, недели, часы, дни недели, итог года и столбец «Versions»; время «после последней Staging» и разгоны меряются по обновлениям (у пропущенных номеров времени нет). Гипотеза «Staging +1 = фикс текущего патча» не подтвердилась: прямо перед целыми патчами 7.38–7.41 последние сборки Staging почти все +1, правило фиксов прежнее. Числа — `fmt_short` («21 d» от 2 дней, иначе «26 h»); подсказки — 2–3 строки (`_row_tip`, неделя — счёт сборок). Правила: момент выхода патча = первая сборка основного клиента (570) в его день по UTC или до 12 ч следующего (`PATCH_DAY_SLACK_H`), иначе полдень; сборка относится к первому патчу, вышедшему после неё (у списка целых патчей — к следующему целому, `major_releases`); разгон сервера = его последние сборки перед патчем без паузы дольше 7 дней (`run_up`, `RUN_GAP_D`: Experimental идёт почти всегда, а у целого патча в группе ещё и Staging буквенных); «≥» — разгон упёрся в начало журнала. Кнопки Both / Experimental / Staging у графиков (`series_buttons`; у `<svg>` нет свойства `.hidden`, переключать атрибут `toggleAttribute`); подсказка у каждого столбца, дня и строки (`.tb-tip-target`, общий `tooltips.js`; у дней и недель в HTML только счёт `data-c="e,s"` и `data-title`, таблицу `calendar-builds.js` пишет при наведении, до `tooltips.js`: 13 лет недель и дней иначе тяжелы; числа на столбцах недель тоже рисует скрипт); наведение на патч подсвечивает недели его разгона (`data-patch`, у целых — `data-major`). Фильтр годов: страница собрана на весь журнал, скрипт перестраивает недельный график по `data-t`/`data-v` и часы и дни по счётам за годы `data-c-<сервер>`; шаги шкалы — `NICE_STEPS` в Python и `NICE` в скрипте, держать одинаковыми (больше 2500 на деление — округление вверх). Вкладка считается только с первой сборки Staging (01.03.2023, `since_staging`, `render_panel(…, from_staging=True)` в `calendar.py`): сборки и патчи раньше не показываются (владелец 2026-11-10 откатил импорт SteamDB 2013+ как «кашу»). Фиксы Staging (владелец 2026-11-10: Staging несёт и фиксы основной игры, это не разгон к патчу): сборка Staging — фикс, если следующая сборка основного клиента вышла не позже чем через 6 ч (`FIX_WINDOW_H`, `staging_fixes`) и не была выходом патча; таких 45 из 304. Вкладка собрана дважды (`.tb-view`, `data-fix="hide"` и `"all"`): без фиксов (показана, галочка «Hide Staging fixes» включена) и со всеми сборками; галочка стоит в шапке календаря сборок на месте Compact и меняет вид, сохраняя год календаря и годы графиков; моменты патчей в обоих видах по всем сборкам основного клиента. Без фиксов медианы на 10.11.2026: после предпоследней Staging 16 ч, после последней 7 ч, первая Staging после предыдущего патча 29 дней, разгон Staging 8 дней, Experimental 60 дней. Цвета вкладки: Experimental #d0603a (не оранжевый патчей), Staging #f0d58c.
  - **Источник Test servers.** Experimental и Staging — отдельные приложения Steam: 247040 (сервер 247060) и 2305270 (сервер 2305290), не ветки 570. Номер версии клиента без ключа даёт Web API Valve `api.steampowered.com/IGCVersion_<app>/GetClientVersion/v1` → `active_version` (7505, 3338, 6973 на 10.11.2026); новый номер = новая сборка (бывает и откат на номер ниже). PICS (api.steamcmd.net) для этих приложений бесполезен: без токена только номер изменения, без времени. Раньше 16.11.2023 — посты того же автора в канале t.me/DOTA_DM_SPAM (публичная веб-лента `t.me/s/…?before=<id>`, разовая загрузка `--telegram <id>`, страницы в `.cache/branch_builds/tg/`, пауза 1 с; `parse_telegram_page`: только строки `api_*version_active`; до 08.2022 без номера приложения: `api_server…` = 570, `api_test_server…` = 247040, номера идут подряд в его; Staging до 31.01.2023 не существовал, старый «Dota 2 Test» 205790 — свой метод версии Valve убрал, истории нет нигде), с 28.10.2021 (Experimental и основной клиент), Staging — с 01.03.2023; в 2023-03…11 строки вида «● 2305270 - Dota 2 Staging | a =&gt; b» (`_TG_BULLET`); точность: 516 из 538 сборок основного клиента 2021–2023 совпали с коммитами GameTracking в пределах 10 мин. Отдельного Staging до 2023 не было: в канале 2021–2022 только основной клиент и Experimental, в списке приложений автора Staging — только 2305270/2305290. История — журнал [muk-as/DOTA2_WEB](https://github.com/muk-as/DOTA2_WEB) `steam_api/_HISTORY_by_date.txt` (тот же API, с 16.11.2023, время UTC+3): 397 из 433 сборок основного клиента с 06.2025 совпали с коммитами GameTracking-Dota2 в пределах 10 минут. `scripts/fetch/fetch_branch_builds.py`: опрос API (`merge`, окно `after`..`time`), `--history` вливает журнал (`parse_history`, `merge_history`: одна смена `from → version` не считается дважды, побеждает более раннее время), `--offline` только проверяет файл; сырые ответы — `.cache/branch_builds/`; `data/branch_builds.json` — по сборке на строку. Расписание — `.github/workflows/branch-builds.yml`: каждые 15 мин API, раз в сутки ещё и журнал; последние проверки — в кэше Actions (`--state`); коммит только при новых сборках и не в main, а в свою ветку `data-branch-builds` (main защищён проверкой «build», токен задачи её не проходит: с 10.11 23:39 сборки не доходили до сайта; владелец 2026-11-11 «отдельная ветка данных»). Перед опросом задача вливает копию из этой ветки, `build.yml` перед сборкой сайта тоже (`--offline --merge-from`, функция `union`); копию в main подтягивают руками командой из шапки `fetch_branch_builds.py`. После новой сборки задача сама запускает сборку и выкладку сайта (`gh workflow run build.yml`, право `actions: write`; пуш от GITHUB_TOKEN другие задачи не запускает, владелец 2026-11-10). Сборка сайта сеть не трогает. Найдено при сверке: у 7.39 на сайте стояло 21.05.2025, а основной клиент обновился 22.05 в 22:12 UTC; дата исправлена на 22.05.2025 (владелец 2026-11-10). Тесты — `tests/test_branch_builds.py`.
- **`terrain_<code>.html`** (`builders/terrain.py`, 5-я вкладка Materials) — сравнение рельефа old→new через **шторку-слайдер** (две карты `icons/maps/map_<ver>.webp`, попиксельно совмещённые, клип через `clip-path` по `--pos`) + список Terrain Changes этого патча. Полный план и TODO — `docs/terrain.md`.
  - **Список изменений парсится из `content/p*.py`** (никакого дублирования): `_terrain_notes_by_patch()` читает контент как Python (ast); **заметки о карте = любой блок `plain_header(..., terrain_link="<патч>")`**, как бы он ни назывался (7.38c: «Dire Safe Lane Jungle» и др.; заголовок ≠ «Terrain Changes» становится подгруппой) → `{патч: [(text, TAG, subgroup, note)]}`; inline_note строки показывается значком (?). Новые заметки о карте — только в блоке с `terrain_link`, иначе страница Terrain их не увидит (так было с 7.38b/7.38c). Сверка заметок с файлом карты: `scripts/gen/terrain_audit.py`. Сейчас это 7.39, 7.39b, 7.39c, 7.39d, 7.40, 7.41 (у 7.40 свой большой ремап-список — не путать). Тег `b(...)`-строк выводится по направлению с учётом `l=True` (дешевле mana cost = BUFF, меньше capture time = BUFF).
  - **Конвенции тегов для terrain-строк:** **«demoted to a 'medium'/'small' camp» → NERF** (понижение тира лагеря = ослабление); **«Removed … tree(s)» → MISC** (удаление деревьев нейтрально, НЕ DEL); удаление вотчеров/объектов («watchers … removed») остаётся DEL; время захвата объекта (capture time) меньше → BUFF с `b(old,new,l=True)` (даёт %-бейдж).
  - **Пикер патчей** (`_picker_html`) — меню версий в шапке навигации (`.nav-context-terrain`): по ссылке на каждую страницу Terrain, новые сверху; стрелки `initSubpatchPicker` переходят на соседние ссылки.
  - **Одна страница на патч (2026-10-02, владелец: «разницу между буквенными картами тоже надо показывать»).** `patch/map_versions.py`: шаг = патч, чей файл карты отличается от файла патча перед ним (`data/map/patch_maps.json`), и у обоих файлов есть картинка (`data/map/renders.json`) → `terrain_<code>.html`. OLD-сторона подписана патчем перед ним, картинка — файла, который тот патч гонял. **«Тихие» патчи страниц не получают** (владелец: «если ничего не меняли — сравнивать нечего»): тот же файл (7.40b, 7.41b) или ни заметок, ни сдвинутых объектов (`_quiet`: 7.39e, 7.40c, 7.41c–f; картинки отличаются лишь шумом рендера — `scripts/gen/map_picture_diff.py`). Страница перед ними пишет «7.41b – 7.41f changed nothing on the map» (`_quiet_runs`). На 2026-10-04 — 14 страниц `terrain_*.html` (7.38 сравнивается с картой 7.37e; заметки 7.38 — под «Wandering Waters» и «Other Terrain Changes», парсер берёт и их). Картинки/mapdata называются по ПЕРВОМУ патчу с этим файлом (`mapdata_741` = релиз 7.41, `741f` = текущая). Список = заметки только этого патча; без заметок — «The patch notes list no terrain changes.»; под счётчиками «Moved in the map file» (`_moved_summary` из диффа). Дифф на каждый шаг: `python scripts/gen/build_terrain_diff.py` (без аргументов = все шаги). Ссылка «View on map» с патч-страницы → `terrain_<code>.html` этого патча. Пикер в шапке = список патчей; стрелки `initSubpatchPicker` ходят по соседним страницам. Если у пары нет диффа → `_controls_html(layers=False)` (только Zoom). Для патча с заметками без пары — `_fallback_html`.
  - **Резкий зум в fullscreen (2026-10-02):** кусочки 8192 (16×16 по 512 px, `scripts/gen/map_tiles.py`) лежат в Oldgrowth `tiles/<ver>/` и отдаются его GitHub Pages; `renders.json` "tiles" = у каких картинок они есть → `data-tiles-old/-new` на слайдере → `src/js/terrain.js` `updateTiles` кладёт видимые кусочки поверх картинки 4096, когда пиксель картинки крупнее пикселя экрана.
  - **Как добавить новый патч с картой:** отрендерить файл карты (docs/terrain.md, SFM), положить `icons/maps/map_<ver>.webp` + `data/map/mapdata_<code>.json`, обновить `data/map/patch_maps.json` и `renders.json`, `python scripts/gen/build_terrain_diff.py` — страница появится сама.
  - **Слои-оверлеи** (тумблеры в баре `.tc-controls-bar` НАД картой, не поверх): Trees, Camps + **10 точечных сущностей** (`_ENTITY_LAYERS`: towers/lotus/twinGates/tormentors/bounty/power/wisdom/outposts/watchers/roshan). **Классы сущностей:** Outpost=`npc_dota_watch_tower` (2), **Watcher=`npc_dota_lantern` (10)** — это РАЗНЫЕ слои!; Roshan=`npc_dota_roshan_spawner` (2); Tormentor=`npc_dota_miniboss_spawner`; Shrine of Wisdom=`npc_dota_xp_fountain`. Каждый = old(740)+new(741) координаты из `terrain_diff_<patch>.json["entities"]`, делится слайдером (классы `.tm-old`/`.tm-new`), тумблер = root-класс `.show-<key>`. JS-обработчик generic по `.tc-layer-btn[data-layer]`.
  - **Power-руна — анимация**: спот power-руны может выкинуть любую из 7 рун, поэтому слой Power особый — на КАРТЕ его иконки (`tc_rune_0..6.png`, скачаны с liquipedia в `icons/ref/runes/`, в НАТУРАЛЬНЫХ цветах) циклятся каждые 3с пока слой включён (`src/js/terrain.js` `togglePowerCycle`/`setRune`). Кнопка показывает `tc_power.png` — свой значок power-рун, связку из трёх рун (`scripts/gen/gen_power_rune_icon.py`, владелец 2026-10-28; раньше была случайная руна). Маркер всё равно в зелёном диске. Порядок: amplify/arcane/haste/illusion/invisibility/regeneration/shield.
  - **Значок** = пиксель-адаптация ИГРОВОЙ иконки из `icons/ref/` (`scripts/gen/gen_terrain_layer_icons.py`, `REFS`; SVG растрит через ImageMagick `magick`), перекрашенная в цвет типа (`COLORS`) с 3-тоновым шейдингом по яркости + 1px тёмная обводка. Без рефа (wisdom, watchers) — рисованный `FALLBACK`-глиф. **Маркер на карте (`marker_g`) = тёмная подложка-круг (`#0d100b` @0.66, чтобы пёстрая карта не просвечивала «мутно») + слабый тинт цвета типа (@0.34) + золотое кольцо + значок сверху** (значок — ОСВЕТЛённый цвет типа, чтобы читался на своём диске). Цвета `_ENTITY_LAYERS` (build_terrain) ОБЯЗАНЫ совпадать с `COLORS` (генератор).
  - Маркеры/счётчики валидны только для `_DIFF_PATCH` (7.41 — под него заточен `terrain_diff_<patch>.json`). Иконки кэмпов — `icons/camps/creepcamp_{small,mid,big,ancient}.png`.
  - **Карты обрезаны впритык** (`scripts/gen/build_terrain_maps.py`, `_content_bbox` теперь отсекает плоский серый плейсхолдер по доле контента в строке/столбце ≥10%, а не «любой не-серый пиксель» — раньше оставались жирные серые поля). Поля ≈0. Проекция авто-подстраивается через `data/terrain_map_meta.json` (crop x/y/w/h в координатах сшитого холста; markers reproject автоматически).
  - **Кредит источников**: строки под слайдером нет (владелец 2026-10-03) — все картинки и списки объектов наши, источник указан в README Oldgrowth.
  - **Кнопка «View on map» на патч-странице**: `plain_header("Terrain Changes", terrain_link="<base_ver>")` дорисовывает золотую пилюлю-ссылку (`.terrain-jump-btn`) в заголовок → `../terrain_<code>.html` — страница именно этого патча (у каждого патча с заметками рельефа она есть). ⚠ `_terrain_notes_by_patch()` матчит `plain_header\("Terrain Changes"` БЕЗ закрывающей `\)` — иначе аргумент `terrain_link=` ломает парсер (0 изменений).
  - **Иконки index'а** (terrain/telegram/donation плитки) генерит `scripts/gen/gen_index_icons.py` (PIL, 32×32, gothic-gold) → `icons/ui/gothic/icon_*.png`.

## Источники данных по рельефу (terrain)

Координаты карты (деревья/кэмпы/башни/тормент/гейты/лотосы по версиям) — только наши, из файлов игры: `scripts/gen/extract_map_entities.py` → `data/map/mapdata_<code>.json`. Дифф считает `scripts/gen/build_terrain_diff.py` → `data/terrain/terrain_diff_<patch>.json`. Проекция — `data/terrain_map_meta.json` (проверено наложением всех деревьев на рендер карты).

## Шапка
- Шапка: вкладка латест-патча называется **Patches**; в правом углу шапки версии патча нет, там только название таблицы на страницах Materials.

## Иконки плиток главной (`tools/pixel_icons/build.py`)
- Статичные плитки: Heroes, Stats, Hero Lab, AoE, Changes, Summons, Lane Creeps, Ko-Fi. Их иконки рисует скилл Pixel Art Studio из скрипта `tools/pixel_icons/build.py`, он и есть источник правды. Готовые PNG руками не правим, меняем скрипт и запускаем `python tools/pixel_icons/build.py --install` (PNG ляжет в `icons/ui/gothic/`).
- Стиль как у анимированных: 32×32, крупная масса на весь кадр, объём светлыми и тёмными плоскостями (свет сверху слева), контур `#311e12`, палитра `sloppy_gothic_gold` (карточка стиля в скилле: `references/learned/006-…`).
- Каждая иконка собрана из слоёв под будущую анимацию при наведении: у шлема качается плюмаж, в котле поднимаются пузыри, бусины счётов (Stats) сдвигаются, кольцо стрелок Changes вращается (внутри шлем у героев и самоцвет у предметов), кольца AoE расходятся, череп поднимается, мечи скрещиваются с бликом, из чашки поднимаются сердечки.
- Dynamics у героев и у предметов различаются значком в углу (шлем / самоцвет). Скрипт накладывает его на `icon_dynamics.png` и на каждый кадр `icon_dynamics.gif`, это исходники, их не удалять. Результат: `icon_dynamics_{heroes,items}.{png,gif}`.


## Новый патч → страницы Materials (проверено 2026-09-25)
- `heroes_raw.json` (скорость атаки, обзор, снаряд, поворот, хитбокс) для раскладки 7.41f+ собирается **из локальных `data/stats/<ver>/heroes/*.txt`** (`scripts/fetch/fetch_hero_history.py → build_from_local`), шаблон `npc_dota_hero_base` — из `data/stats/<ver>/npc_dota_hero_base.txt` (достать из VPK игры), иначе переносится с прошлого патча с предупреждением. Патч, уже лежащий в хранилище файлов игры (`patch/game_files.py`), читается оттуда (`build_from_store`). До 2026-10-24 источником был d2vpkr и давал 7.41f = копия 7.41e (Earth Spirit/KotL/Warlock BAS). Тест: `tests/test_latest_patch_data.py`.
- `RELEASE_HISTORY` сортируется по дате (новые сверху) при загрузке `patch/meta.py` — порядок в файле больше не важен.
- Mana Items: история предметов с интеллектом считается по константе ТОГО патча (`_int_const_at`: 11 маны/Int в 7.36–7.38).
- Остаток аудита (не сделано; пункт про отставание истории нейтралов/способностей на патч снят 2026-10-24: они читаются из хранилища файлов игры, по сборке самого патча): 4 разных «последних версии»; движковые константы продублированы (heroes_stats / entity_changes / `src/js/`); `_bucket` в terrain сравнивает только мажор.
