# Структура, запуск и прочие страницы

## Структура проекта

```
build_site.py                ← ЕДИНЫЙ entrypoint. python build_site.py [steps] [--latest]
builders/
  patch.py                   ← Запускает все content/p*.py + calendar + index
  silent.py                  ← Дифф KV-файлов → patches/silent/*.html (скрытые изменения)
  terrain.py                 ← terrain.html (сравнение карт)
  creeps.py, heroes_stats.py, hero_lab.py, mana_items.py, heroes_dyn.py, items_dyn.py
  site_common.py             ← Общий HTML-обвёртка (head/nav/foot)
  dyn_matrix_common.py       ← Общий код для динамических матриц
content/
  p739d.py, p739e.py, ...    ← Один файл на патч. def build() → save_html()
patch/
  api.py                     ← from patch.api import * — публичный API для content/*.py
  elements.py                ← Все хелперы: W(), li(), hero_header(), ability(), ...
  images.py                  ← ITEM_SLUG, HERO_SLUG, item_img(), abil_img()
  meta.py                    ← PATCHES список, RELEASE_HISTORY
  index_page.py              ← index.html + What's New popup
generate_patch_code_v2.py    ← Datafeed → Python scaffold. Канонический генератор.
data/
  normalized/patches/*.json  ← JSON-артефакты (генерятся параллельно со scaffold)
  stats/{version}/           ← KV-файлы героев/предметов (для silent changes)
  itemlist.json              ← Имена + engine slug всех предметов (Valve datafeed)
  abilities_by_id.json       ← ability_id → (dname, slug) для ability()
dist/                        ← Финальный сайт (в .gitignore, кроме dist/patches/)
```

## Добавление нового патча — полный workflow

```bash
# 1. Обновить itemlist (engine slugs предметов, нейтрал-пул)
python scripts/fetch/fetch_itemlist.py

# 2. Сгенерировать scaffold
python generate_patch_code_v2.py 7.42
# → _generated_p_7.42_v2.py + data/normalized/patches/7.42.json

# 3. Сохранить scaffold как content/p742.py:
#    - добавить в начало: from patch.api import *
#    - обернуть в: def build():
#    - добавить в конец: write_footer(); save_html('patches/7.42.html')
#    ⚠ генератор НЕ добавляет эти три обёртки — нужно вручную

# 4. Зарегистрировать патч
#    - builders/patch.py: import content.p742 + content.p742.build() в нужном месте
#    - patch/meta.py: добавить в PATCHES (для nav dropdown)
#    - patch/index_page.py: добавить в _PATCH_SITE_DATES (для What's New popup)

# 5. Собрать + проверить иконки
python build_site.py --latest      # только новый патч, ~3-4s
python scripts/fetch/fetch_icons.py  # скачать недостающие иконки способностей
python build_site.py --latest      # пересобрать чтобы пересчитать _LOCAL_ABIL_ICONS

# 6. Полная сборка перед коммитом
python build_site.py
git add content/p742.py icons/abilities/*.png ...
git commit -m "feat: add 7.42 patch page"
```

## Известные ловушки генератора (generate_patch_code_v2.py)

### Enchantment items → enchant_header, не item_header
Генератор автоматически использует `enchant_header()` когда engine slug начинается с `enhancement_`.
Если в старом scaffold стоит `item_header("Brawny")` — заменить на `enchant_header("Brawny")`.
Иконка: `icons/items/enhancement_brawny.png` (не `brawny.png`).

### Предметы с несовпадающим display name и engine slug
`item_img("Parasma")` ищет `parasma.png`, но Valve хранит как `devastator.png`.
Генератор печатает `[WARN]` при таких случаях.
**Фикс:** добавить в `ITEM_SLUG` в `patch/images.py`: `"Parasma": "devastator"`.
Примеры уже в ITEM_SLUG: Khanda→angels_demise, Book of the Dead→demonicon, Parasma→devastator.

### Иконки способностей не скачиваются автоматически
`fetch_icons.py` нужно запускать вручную после каждой новой сборки патча.
Иконки innate/facet (404 на CDN) — нормально, браузер использует fallback `innate_icon.png`.
`_LOCAL_ABIL_ICONS` в `patch/images.py` строится при загрузке модуля — пересборка нужна после скачивания.

### Ability slug неправильный
Генератор берёт slug из `data/abilities_by_id.json`. Если способность переименована в новом патче,
нужно обновить `abilities_by_id.json`: `python -c "from generate_patch_code_v2 import _refresh_abilities; _refresh_abilities()"`.

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

`builders/patch.py` также генерирует:
- **`index.html`** (`save_index_html`) — лендинг в виде игрового «инвентаря-книги»: орнаментальная панель `.inv-book` с квадратными слотами (`icons/ui/gothic/`, пак [Gothic Pixel UI](https://abyssowl.itch.io/gothic-pixel-ui)). Верхний ряд `.inv-filled` = ссылки на разделы, нижний `.inv-ph` = плейсхолдеры. Золото подогнано под бренд-слово `sikle` (`#e3c46a`). Подписи — временные плейсхолдеры (шрифт Jersey 10). Старая `.zuma-*` сетка удалена.
- **`calendar.html`** (`save_calendar_html`) — календарь патчей + кастомный год-пикер (`.cal-year-picker`, не нативный `<select>`) + полоса-инфографика «Patch cadence» внизу (`_spark_svg`: SVG-sparkline, «красивая» 5-ступенчатая ось Y, gridlines/оси, hover-значения). Переключатель Compact живёт в шапке блока года.
- **`terrain.html`** (`builders/terrain.py`, 5-я вкладка Materials) — сравнение рельефа old→new через **шторку-слайдер** (две карты `icons/maps/map_<ver>.webp`, попиксельно совмещённые, клип через `clip-path` по `--pos`) + список Terrain Changes этого патча. Полный план и TODO — `docs/terrain.md`.
  - **Список изменений парсится из `builders/patch.py`** (никакого дублирования): `_terrain_changes_by_patch()` читает каждую секцию `plain_header("Terrain Changes")` → `{ver: [(text, TAG)]}`. Сейчас это 7.41 и 7.40 (у 7.40 свой большой ремап-список — не путать). Тег `b(...)`-строк выводится по направлению с учётом `l=True` (дешевле mana cost = BUFF, меньше capture time = BUFF).
  - **Конвенции тегов для terrain-строк:** **«demoted to a 'medium'/'small' camp» → NERF** (понижение тира лагеря = ослабление); **«Removed … tree(s)» → MISC** (удаление деревьев нейтрально, НЕ DEL); удаление вотчеров/объектов («watchers … removed») остаётся DEL; время захвата объекта (capture time) меньше → BUFF с `b(old,new,l=True)` (даёт %-бейдж).
  - **Пикер патчей** (`_picker_html`, gold-скин календарного year-picker) живёт **в заголовке списка** как версия: `[7.41 ▾] Terrain Changes` (`.terrain-list-head`). Перечисляет все патчи с изменениями рельефа; переключение (scripts.js `initTerrainPicker`) показывает соответствующую `.terrain-map-pane` + `.terrain-list-pane` по `data-patch`. Тулбара над картой больше нет.
  - **Карта-пара есть только для патчей из `_MAP_PAIRS`** (dict `патч → (old_ver, new_ver)`; сейчас `7.41`→(7.40,7.41) и `7.40`→(7.39,7.40)). `_compare_html(old_ver, new_ver, markers_svg)` строит слайдер для любой пары. **Маркеры + полная панель слоёв (Trees/Camps/10 точечных) — ПЕР-ПАТЧЕВЫЕ**: каждый патч со своим `data/terrain_diff_<ver>.json` получает тумблеры; `save_terrain_html` строит `markers_by_patch`/`counts_by_patch` (по `_load_diff(ver)`). Если у пары нет диффа → `_controls_html(layers=False)` рисует только Zoom (без мёртвых тумблеров). Общий crop-meta (`terrain_map_meta.json`) проецирует маркеры ЛЮБОГО патча одинаково (карты обрезаны ОДНИМ общим crop-box: `build_terrain_maps.py 7.39 7.40 7.41`). **scripts.js `initTerrainCompare` инициализирует ВСЕ `.terrain-compare`** (`querySelectorAll().forEach(initOneTerrainCompare)`), иначе скрытая по умолчанию вторая панель не получит рабочий слайдер. Для патчей без карты-пары — `_fallback_html` (последняя карта в блюре + «Map comparison for X isn't available yet»).
  - **Как добавить новый патч с картой+слоями (чек-лист):** (1) `python scripts/gen/build_terrain_maps.py <prev> <new> [и все прошлые]` — ВСЕГДА перечислять все версии, чтобы общий crop-box не сдвинулся; (2) скачать `mapdata_<prevcode>.json` в `.cache/leamare/` (если нет) + `python scripts/gen/build_terrain_diff.py <prev>:<new>` → `data/terrain_diff_<new>.json` (генерик-ключи `treesOld/New`, `campsOld/New`, `entities`); (3) добавить запись в `_MAP_PAIRS`. `_terrain_changes_by_patch` подхватит список изменений из секции патча автоматически. Не забыть `git add icons/maps/map_<new>.webp` + `data/terrain_diff_<new>.json`.
  - **Слои-оверлеи** (тумблеры в баре `.tc-controls-bar` НАД картой, не поверх): Trees, Camps + **10 точечных сущностей** (`_ENTITY_LAYERS`: towers/lotus/twinGates/tormentors/bounty/power/wisdom/outposts/watchers/roshan). **Ключи leamare** (`layerDefinitions.js`): Outpost=`npc_dota_watch_tower` (2), **Watcher=`npc_dota_lantern` (10)** — это РАЗНЫЕ слои!; Roshan=`npc_dota_roshan_spawner` (2); Tormentor=`npc_dota_miniboss_spawner`; Shrine of Wisdom=`npc_dota_xp_fountain`. Каждый = old(740)+new(741) координаты из `terrain_diff.json["entities"]`, делится слайдером (классы `.tm-old`/`.tm-new`), тумблер = root-класс `.show-<key>`. JS-обработчик generic по `.tc-layer-btn[data-layer]`.
  - **Power-руна — анимация**: спот power-руны может выкинуть любую из 7 рун, поэтому слой Power особый — на КАРТЕ его иконки (`tc_rune_0..6.png`, скачаны с liquipedia в `icons/ref/runes/`, в НАТУРАЛЬНЫХ цветах) циклятся каждые 3с пока слой включён (scripts.js `togglePowerCycle`/`setRune`). Кнопка показывает СЛУЧАЙНУЮ руну при загрузке. `tc_power.png` (дефолт) = regeneration. Маркер всё равно в зелёном диске. Порядок: amplify/arcane/haste/illusion/invisibility/regeneration/shield.
  - **Значок** = пиксель-адаптация ИГРОВОЙ иконки из `icons/ref/` (`scripts/gen/gen_terrain_layer_icons.py`, `REFS`; SVG растрит через ImageMagick `magick`), перекрашенная в цвет типа (`COLORS`) с 3-тоновым шейдингом по яркости + 1px тёмная обводка. Без рефа (wisdom, watchers) — рисованный `FALLBACK`-глиф. **Маркер на карте (`marker_g`) = тёмная подложка-круг (`#0d100b` @0.66, чтобы пёстрая карта не просвечивала «мутно») + слабый тинт цвета типа (@0.34) + золотое кольцо + значок сверху** (значок — ОСВЕТЛённый цвет типа, чтобы читался на своём диске). Цвета `_ENTITY_LAYERS` (build_terrain) ОБЯЗАНЫ совпадать с `COLORS` (генератор).
  - Маркеры/счётчики валидны только для `_DIFF_PATCH` (7.41 — под него заточен `terrain_diff.json`). Иконки кэмпов — `icons/camps/creepcamp_{small,mid,big,ancient}.png`.
  - **Карты обрезаны впритык** (`scripts/gen/build_terrain_maps.py`, `_content_bbox` теперь отсекает плоский серый плейсхолдер по доле контента в строке/столбце ≥10%, а не «любой не-серый пиксель» — раньше оставались жирные серые поля). Поля ≈0. Проекция авто-подстраивается через `data/terrain_map_meta.json` (crop x/y/w/h в координатах сшитого холста; markers reproject автоматически).
  - **Кредит источников**: рендеры карт — `leamare/dota-interactive-map`, координаты сущностей — `leamare/dota-map-coordinates` (две разные репы, обе в `_source_html`).
  - **Кнопка «View on map» на патч-странице**: `plain_header("Terrain Changes", terrain_link="<base_ver>")` дорисовывает золотую пилюлю-ссылку (`.terrain-jump-btn`) в заголовок → `../terrain.html?patch=<base_ver>` (напр. `7.41`/`7.40`). Один общий `terrain.html` (НЕ отдельные `terrain_<ver>.html`): `initTerrainPicker` (scripts.js) читает `?patch=` и предвыбирает соответствующую панель через тот же пикер. ⚠ `_terrain_changes_by_patch()` теперь матчит `plain_header\("Terrain Changes"` БЕЗ закрывающей `\)` — иначе аргумент `terrain_link=` ломает парсер (0 изменений).
  - **Иконки index'а** (terrain/telegram/donation плитки) генерит `scripts/gen/gen_index_icons.py` (PIL, 32×32, gothic-gold) → `icons/ui/gothic/icon_*.png`.

## Источники данных по рельефу (terrain)

Главные источники координат карты (деревья/кэмпы/башни/тормент/гейты/лотосы по версиям):
- **Интерактивная карта**: https://tools.spectral.gg/interactive-map
- **GitHub с координатами**: `leamare/dota-interactive-map` — `assets/data/<ver>/mapdata.json` (per-version coords) + корневой `worlddata.json` (мировые границы для проекции). Дифф считает `scripts/gen/build_terrain_diff.py` → `data/terrain_diff.json`. Проекция: мир ∈ [−10464, 10400] → 1280px (проверено наложением всех деревьев на рендер карты).
