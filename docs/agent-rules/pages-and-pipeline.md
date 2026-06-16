# Структура, запуск и прочие страницы

## Структура проекта

```
builders/patch.py            ← ГЛАВНЫЙ. CSS, JS, HTML-хелперы, данные всех патчей
generate_patch_code.py    ← KV → Python-код. Запускать перед добавлением нового патча
scripts/apply_stats.py    ← Постпроцессор: t("BUFF")→bstat_h() где есть БД
data/
  patchnotes_english.txt  ← Сырые патчноуты Valve (KV формат)
  patchnotes_russian.txt  ← Русский перевод
  stats/{version}/
    heroes.json           ← Стоты героев (npc_heroes.txt → нужные поля)
    items.json            ← Стоты предметов (items.txt → нужные поля)
patches/                  ← Финальные HTML, генерируются builders/patch.py
docs/
  architecture.md, data-format.md, workflow.md
```

Внешние скрипты (в `D:\Sloppy Patches`):
- `extract_patchnotes.py` — выкачивает свежие patchnotes_*.txt и npc_*.txt из локального VPK + заливает в репо
- `fetch_stats.py` — скачивает npc_heroes/items.txt из muk-as/DOTA2_CLIENT за каждый патч (с 7.33), парсит → JSON
- `upload_stats.py` — заливает JSON-файлы в репо

## Как запустить

```bash
python builders/patch.py        # пересобирает все patches/*.html и calendar.html
python builders/heroes_stats.py # heroes_stats.html — таблица статов героев (после build_patch)
python builders/hero_lab.py     # hero_lab.html — калькулятор сравнения героев с предметами
python generate_patch_code.py 7.42   # → _generated_p_7.42.py (вставлять в builders/patch.py)
python scripts/apply_stats.py          # упгрейдит t() → bstat_h() где можем
python scripts/fetch_itemlist.py       # обновляет data/itemlist.json из датафида Valve
                                        # (имена предметов + ТЕКУЩИЙ ПУЛ НЕЙТРАЛОВ для items_dyn).
                                        # Запускать с выходом нового патча, затем builders/patch.py —
                                        # добавленные/выведенные нейтралы подхватятся автоматически.
python scripts/extract_shops.py        # извлекает scripts/shops.txt из VPK → data/shops.txt
                                        # (КАТЕГОРИИ магазина для фильтра items_dyn: Consumables/
                                        # Attributes/Weapons…). Локально (нужен `pip install vpk`).
                                        # Запускать с выходом патча (Valve тасует категории), затем
                                        # builders/patch.py — перемещения категорий подхватятся сами.
```

## Предупреждения и подводные камни

- При добавлении нового героя: добавить в `HERO_SLUG` (builders/patch.py) И в `load_hero_internal_to_display()` (generate_patch_code.py)
- При добавлении нового предмета: только в `ITEM_SLUG` (builders/patch.py); generate_patch_code.py читает оттуда
- 7.41c в HANDCRAFTED раньше был сырой HTML — теперь конвертирован в W() вызовы; следующие патчи делать только через W()
- `_formula_id_counter` — глобальный счётчик для table-id, сбрасывается при каждом запуске
- `.gitignore` исключает `__pycache__/`, `_generated_p_*.py`, `_insert_patches.py`. Одноразовые скрипты `_*.py` после использования можно удалять
- 7.08 — патч слишком старый для stats DB (muk-as начался с 7.33), он остаётся с t() fallback
- **Иконки способностей: fallback пишется в `src` напрямую.** Если локального файла `icons/abilities/<slug>.png` нет (множество innate-способностей не имеют публичной CDN-иконки), `ability()` рендерит fallback СРАЗУ как `src` (innate → `innate_icon.png`, иначе → `missing.svg`), а не «битый путь, который меняется через onerror». Иначе поиск (читает `img.src` при загрузке, до срабатывания ленивого onerror) показывал не ту иконку. Набор существующих файлов — `_LOCAL_ABIL_ICONS` (строится при загрузке модуля). Пример-каноник: Timbersaw «Exposure Therapy» (+ ещё 27 innate)

## Прочие генерируемые страницы (не патчи)

`builders/patch.py` также генерирует:
- **`index.html`** (`save_index_html`) — лендинг в виде игрового «инвентаря-книги»: орнаментальная панель `.inv-book` с квадратными слотами (`icons/ui/gothic/`, пак [Gothic Pixel UI](https://abyssowl.itch.io/gothic-pixel-ui)). Верхний ряд `.inv-filled` = ссылки на разделы, нижний `.inv-ph` = плейсхолдеры. Золото подогнано под бренд-слово `sikle` (`#e3c46a`). Подписи — временные плейсхолдеры (шрифт Jersey 10). Старая `.zuma-*` сетка удалена.
- **`calendar.html`** (`save_calendar_html`) — календарь патчей + кастомный год-пикер (`.cal-year-picker`, не нативный `<select>`) + полоса-инфографика «Patch cadence» внизу (`_spark_svg`: SVG-sparkline, «красивая» 5-ступенчатая ось Y, gridlines/оси, hover-значения). Переключатель Compact живёт в шапке блока года.
- **`terrain.html`** (`builders/terrain.py`, 5-я вкладка Materials) — сравнение рельефа old→new через **шторку-слайдер** (две карты `icons/maps/map_<ver>.webp`, попиксельно совмещённые, клип через `clip-path` по `--pos`) + список Terrain Changes этого патча. Полный план и TODO — `docs/terrain.md`.
  - **Список изменений парсится из `builders/patch.py`** (никакого дублирования): `_terrain_changes_by_patch()` читает каждую секцию `plain_header("Terrain Changes")` → `{ver: [(text, TAG)]}`. Сейчас это 7.41 и 7.40 (у 7.40 свой большой ремап-список — не путать). Тег `b(...)`-строк выводится по направлению с учётом `l=True` (дешевле mana cost = BUFF, меньше capture time = BUFF).
  - **Конвенции тегов для terrain-строк:** **«demoted to a 'medium'/'small' camp» → NERF** (понижение тира лагеря = ослабление); **«Removed … tree(s)» → MISC** (удаление деревьев нейтрально, НЕ DEL); удаление вотчеров/объектов («watchers … removed») остаётся DEL; время захвата объекта (capture time) меньше → BUFF с `b(old,new,l=True)` (даёт %-бейдж).
  - **Пикер патчей** (`_picker_html`, gold-скин календарного year-picker) живёт **в заголовке списка** как версия: `[7.41 ▾] Terrain Changes` (`.terrain-list-head`). Перечисляет все патчи с изменениями рельефа; переключение (scripts.js `initTerrainPicker`) показывает соответствующую `.terrain-map-pane` + `.terrain-list-pane` по `data-patch`. Тулбара над картой больше нет.
  - **Карта-пара есть только для патчей из `_MAP_PAIRS`** (dict `патч → (old_ver, new_ver)`; сейчас `7.41`→(7.40,7.41) и `7.40`→(7.39,7.40)). `_compare_html(old_ver, new_ver, markers_svg)` строит слайдер для любой пары. **Маркеры + полная панель слоёв (Trees/Camps/10 точечных) — ПЕР-ПАТЧЕВЫЕ**: каждый патч со своим `data/terrain_diff_<ver>.json` получает тумблеры; `save_terrain_html` строит `markers_by_patch`/`counts_by_patch` (по `_load_diff(ver)`). Если у пары нет диффа → `_controls_html(layers=False)` рисует только Zoom (без мёртвых тумблеров). Общий crop-meta (`terrain_map_meta.json`) проецирует маркеры ЛЮБОГО патча одинаково (карты обрезаны ОДНИМ общим crop-box: `build_terrain_maps.py 7.39 7.40 7.41`). **scripts.js `initTerrainCompare` инициализирует ВСЕ `.terrain-compare`** (`querySelectorAll().forEach(initOneTerrainCompare)`), иначе скрытая по умолчанию вторая панель не получит рабочий слайдер. Для патчей без карты-пары — `_fallback_html` (последняя карта в блюре + «Map comparison for X isn't available yet»).
  - **Как добавить новый патч с картой+слоями (чек-лист):** (1) `python scripts/build_terrain_maps.py <prev> <new> [и все прошлые]` — ВСЕГДА перечислять все версии, чтобы общий crop-box не сдвинулся; (2) скачать `mapdata_<prevcode>.json` в `.cache/leamare/` (если нет) + `python scripts/build_terrain_diff.py <prev>:<new>` → `data/terrain_diff_<new>.json` (генерик-ключи `treesOld/New`, `campsOld/New`, `entities`); (3) добавить запись в `_MAP_PAIRS`. `_terrain_changes_by_patch` подхватит список изменений из секции патча автоматически. Не забыть `git add icons/maps/map_<new>.webp` + `data/terrain_diff_<new>.json`.
  - **Слои-оверлеи** (тумблеры в баре `.tc-controls-bar` НАД картой, не поверх): Trees, Camps + **10 точечных сущностей** (`_ENTITY_LAYERS`: towers/lotus/twinGates/tormentors/bounty/power/wisdom/outposts/watchers/roshan). **Ключи leamare** (`layerDefinitions.js`): Outpost=`npc_dota_watch_tower` (2), **Watcher=`npc_dota_lantern` (10)** — это РАЗНЫЕ слои!; Roshan=`npc_dota_roshan_spawner` (2); Tormentor=`npc_dota_miniboss_spawner`; Shrine of Wisdom=`npc_dota_xp_fountain`. Каждый = old(740)+new(741) координаты из `terrain_diff.json["entities"]`, делится слайдером (классы `.tm-old`/`.tm-new`), тумблер = root-класс `.show-<key>`. JS-обработчик generic по `.tc-layer-btn[data-layer]`.
  - **Power-руна — анимация**: спот power-руны может выкинуть любую из 7 рун, поэтому слой Power особый — на КАРТЕ его иконки (`tc_rune_0..6.png`, скачаны с liquipedia в `icons/ref/runes/`, в НАТУРАЛЬНЫХ цветах) циклятся каждые 3с пока слой включён (scripts.js `togglePowerCycle`/`setRune`). Кнопка показывает СЛУЧАЙНУЮ руну при загрузке. `tc_power.png` (дефолт) = regeneration. Маркер всё равно в зелёном диске. Порядок: amplify/arcane/haste/illusion/invisibility/regeneration/shield.
  - **Значок** = пиксель-адаптация ИГРОВОЙ иконки из `icons/ref/` (`scripts/gen_terrain_layer_icons.py`, `REFS`; SVG растрит через ImageMagick `magick`), перекрашенная в цвет типа (`COLORS`) с 3-тоновым шейдингом по яркости + 1px тёмная обводка. Без рефа (wisdom, watchers) — рисованный `FALLBACK`-глиф. **Маркер на карте (`marker_g`) = тёмная подложка-круг (`#0d100b` @0.66, чтобы пёстрая карта не просвечивала «мутно») + слабый тинт цвета типа (@0.34) + золотое кольцо + значок сверху** (значок — ОСВЕТЛённый цвет типа, чтобы читался на своём диске). Цвета `_ENTITY_LAYERS` (build_terrain) ОБЯЗАНЫ совпадать с `COLORS` (генератор).
  - Маркеры/счётчики валидны только для `_DIFF_PATCH` (7.41 — под него заточен `terrain_diff.json`). Иконки кэмпов — `icons/camps/creepcamp_{small,mid,big,ancient}.png`.
  - **Карты обрезаны впритык** (`scripts/build_terrain_maps.py`, `_content_bbox` теперь отсекает плоский серый плейсхолдер по доле контента в строке/столбце ≥10%, а не «любой не-серый пиксель» — раньше оставались жирные серые поля). Поля ≈0. Проекция авто-подстраивается через `data/terrain_map_meta.json` (crop x/y/w/h в координатах сшитого холста; markers reproject автоматически).
  - **Кредит источников**: рендеры карт — `leamare/dota-interactive-map`, координаты сущностей — `leamare/dota-map-coordinates` (две разные репы, обе в `_source_html`).
  - **Кнопка «View on map» на патч-странице**: `plain_header("Terrain Changes", terrain_link="<base_ver>")` дорисовывает золотую пилюлю-ссылку (`.terrain-jump-btn`) в заголовок → `../terrain.html?patch=<base_ver>` (напр. `7.41`/`7.40`). Один общий `terrain.html` (НЕ отдельные `terrain_<ver>.html`): `initTerrainPicker` (scripts.js) читает `?patch=` и предвыбирает соответствующую панель через тот же пикер. ⚠ `_terrain_changes_by_patch()` теперь матчит `plain_header\("Terrain Changes"` БЕЗ закрывающей `\)` — иначе аргумент `terrain_link=` ломает парсер (0 изменений).
  - **Иконки index'а** (terrain/telegram/donation плитки) генерит `scripts/gen_index_icons.py` (PIL, 32×32, gothic-gold) → `icons/ui/gothic/icon_*.png`.

## Источники данных по рельефу (terrain)

Главные источники координат карты (деревья/кэмпы/башни/тормент/гейты/лотосы по версиям):
- **Интерактивная карта**: https://tools.spectral.gg/interactive-map
- **GitHub с координатами**: `leamare/dota-interactive-map` — `assets/data/<ver>/mapdata.json` (per-version coords) + корневой `worlddata.json` (мировые границы для проекции). Дифф считает `scripts/build_terrain_diff.py` → `data/terrain_diff.json`. Проекция: мир ∈ [−10464, 10400] → 1280px (проверено наложением всех деревьев на рендер карты).
