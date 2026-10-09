# UI и стили

Правила вёрстки/стилей для всех страниц. `styles.css` и `scripts.js` — единственный источник правды (см. AGENTS.md «source of truth»).

> Подсистема таблиц (Neutral Creeps / Unit Abilities / Mana Items, sticky/overlay) — `docs/tables.md`.

## Patch-page visual layering

Патч-страницы должны использовать Valve-style continuous slab layout:
- `body.patch-page::before` держит общий `featured.jpg` фон.
- `.cat-panel` — один непрерывный content slab под заголовком категории: blue/black translucent gradient + broad black glow. Не возвращать старую модель большой скруглённой карточки с opaque фоном.
- `h2.section` — отдельная orange-to-transparent полоса с left orange border и glow; после неё нужен явный шов перед content slab.
- `.entity-block` внутри `.cat-panel` не должен быть отдельной карточкой/slab. Между героями/предметами/сущностями не должно быть “пропастей”; только тонкая full-width hairline, которая доходит до dyn-cells справа, чтобы было понятно, к какой сущности они относятся.
- Внутренние `item-cost-box`, `provides-box`, `properties-change`, `components-change`, `ability-block`, `patch-dynamics` должны оставаться одной ширины внутри entity-block. Если меняешь отступы, обязательно проверить Chasm Stone и соседние items в `patches/7.41.html`.

## Patch-page filters and Hero Dynamics

- On patch pages, tag filters and category/group filters must recompute layout together. After either filter changes, collapse empty `ul.changes`, `ability-block`, `subgroup`, and `entity-block` containers again.
- For patch-page visibility, the entity header/name itself does **not** count as visible content. A card stays visible only if it still has visible change rows, `ability_change` blocks, or real auxiliary panels such as components/properties/provides boxes.
- `heroes_dyn.html` now supports the same Melee/Ranged toolbar filtering pattern used in Hero Stats. Feed `data-attack-type` per row from the latest hero raw data; Spirit Bear is always melee.
- Dyn-cell pills inside `td.hd-cell` should stay visually centered by forcing the cell to `line-height: 0`; otherwise the pill sits slightly high in the grid.

## Materials page vertical rhythm (правило отступов)

Все страницы Materials (Neutral Creeps / Unit Abilities / Mana Items / Terrain) держат **один и тот же** вертикальный ритм между текстом-описанием и основным блоком (таблица/карта). Источник правды — три значения паддингов внутри `.creeps-scroll`:
- ~~блёрб `.mr-blurb.inbox-bar`~~ — **описаний-блёрбов на страницах больше нет** (убраны 2026-09-25 по просьбе пользователя; не добавлять снова). CSS класса оставлен на случай отката;
- тулбар `.cal-toggle-bar.inbox-bar` → `padding: 14px 28px 16px` (gap блёрб→тулбар = 14px);
- основной контент идёт сразу под тулбаром (его 16px снизу = gap тулбар→контент). На terrain `.terrain-wrap` стартует с `padding: 0 28px 30px` (тот же боковой инсет 28px, верх 0 — gap отдаёт тулбар).

Любая новая Materials-страница ОБЯЗАНА переиспользовать эти паддинги (блёрб → тулбар → контент), чтобы отступ «текст ↔ таблица/карта» был одинаковым везде. Не задавать произвольный верхний паддинг контенту — пусть gap владеет тулбар.

## Единая панель тулбара `.toolbar-panel` (СТАНДАРТ — обязателен для новых страниц)

Все кнопки/переключатели тулбара любой страницы оборачиваются в **ОДНУ обрамлённую панель** `.toolbar-panel` (не россыпь отдельных пилюль):

```html
<div class="cal-toggle-bar inbox-bar"><div class="toolbar-panel">… контролы …</div></div>
```

CSS (`styles.css`, секция «UNIFIED TOOLBAR PANEL») делает всё автоматически:
- панель = тёмная подложка `#11161d` + рамка + `border-radius:8px`, `width:100%` внутри тулбара (тулбар держит ритм 28px по бокам);
- переключатели (`.ua-upgrades-toggle`) и группы-лейблы (`.view-group`/`.hd-remove-group`/`.hd-class-group`) — **плоские** (прозрачные); инпуты/селекты (`.cal-mode-select`, `.mr-price-range`, search) сохраняют свою рамку поля; чипы тегов/классов — свой дизайн;
- **тонкий разделитель** перед каждым контролом, КРОМЕ между двумя подряд идущими `.ua-upgrades-toggle` (тумблеры группируются плотно). Реализовано через `> *:not(:first-child)::before` + отмена для `.ua-upgrades-toggle + .ua-upgrades-toggle`;
- `.toolbar-panel > .hd-search` растягивается (`flex:1 1 220px`).

### Тёплый пиксельный скин (с 2026-09-25) — ОБЯЗАТЕЛЕН для любого контрола

Шапка «Угольки» задала стиль всего интерфейса: **никакого синего/серого «металла»** в меню, тулбарах и кнопках. Секция `WARM PIXEL SKIN` в конце `styles.css`:
- токены `--px-*` (поле `--px-field`, меню `--px-menu`, текст `--px-text`, «нажато» `--px-on`) + пиксельная рамка `--px-edge*` = `border-image` из SVG 6×6 (края 2px, пустые углы 2×2 → ступенчатый угол). `border-image`, а не `clip-path` — чтобы не обрезать выпадашки внутри панели;
- подписи контролов — шрифт `Jersey 10` (18px), лейблы групп (VIEW, LVL, PRICE) — 17px, приглушённое золото;
- кнопки-фильтры = «игровые»: тёмная нижняя кромка `inset 0 -3px 0`, нажатая/активная = золотая заливка `--px-on`;
- выбранный пункт меню «тлеет»: `--px-ember` + золотая полоска слева; подвкладка Materials — тёплый отсвет снизу;
- чипы GROUP / scope оставлены того же размера, что TAG-бейджи (1px рамка, обычный шрифт), только тёплые;
- иконки в кнопках — пиксельные из `icons/ui/gothic/` (меч/лук/таланты рисует `tools/pixel_icons/small.py`, отдаются ×2 с `image-rendering: pixelated`).
- **палитра всего сайта тёплая** (2026-09-25): холодные серо-голубые «металлические» цвета (панели, линии, приглушённый текст, `--line`, `--bg-*`, `--text-*`, `--blue-18…40`) заменены тёплыми той же яркости (L·1.03 / L / L·0.94 — после «слишком тёплый» 09-25; нейтрали скина −40% насыщенности). Хромовые синие (hover/focus/текущая версия/подчёркивание шапки таблиц/график календаря) → золото. **Синий остаётся только со смыслом**: QOL, магический урон, интеллект, Aghanim, мана, копия внутриигровой подсказки (`hlt-*`), цвета фасетов. Новый цвет интерфейса — только тёплый. Откат: git-теги `ui-before-warm-skin` / `ui-before-warm-palette`.
**Новый контрол → добавь его класс в списки селекторов скина**, не заводи свои цвета. Проверка: `px_probe`-подход — пройти страницы Playwright'ом и найти контролы с холодной рамкой/фоном (b ≥ r+5).

Применяется на: heroes_dyn / items_dyn (`dyn_matrix_common`), neutral_creeps / neutral_abilities (`build_creeps`), mana_items (`build_mana_items`). **Новую страницу с тулбаром оформлять так же.**

## Regen columns in stats tables

For `HP/sec` and `MP/sec` columns in both `heroes_stats.html` and `neutral_stats.html`: do not show a leading `+`; render non-zero values with exactly two decimals (`1.60`, `0.50`; Neutral Stats may use its comma decimal style `1,60`); render exact zero as `0` and tint it with a muted version of that column color. Keep numeric `data-sort` values separate from display formatting.

## Hero Stats: innate-derived computed values

- `heroes_stats.html` must treat innate-derived stat bonuses as part of the computed model, not as presentation-only exceptions. If an innate grants or converts stats into another displayed column (damage, armor, move speed, regen, range, etc.), that bonus belongs in `Starting` / `Expanded` when the `Innates` toggle is on, and stays out of `Base`.
- For new numeric inputs in Sloppy UI, hide native increment/decrement spinner controls by default unless the user explicitly asks for them.
- This applies even when the innate is conditional or unusual (example: Axe gaining Strength from armor while alone). If the site chooses to model that condition in Hero Stats, it must be expressed as an explicit toggle/assumption, not silently baked into raw values.
- Current project rule: for Axe in Hero Stats, ignore the nearby-allies condition and model One Man Army as always active when `Innates` is enabled. That Strength bonus must flow through displayed STR and every derived stat it affects (HP, HP regen, damage, etc.).
- For hero-level formulas phrased as `X + Y per level up`, the increment starts after level 1. In Hero Stats this means `(level - 1)`, not `level`. This matters for innate-derived computations too (example: Techies mana-pool regen).
- Distinguish `per level up` from `per level`. `per level` includes level 1 immediately; do not silently convert it to `(level - 1)`. Techies mana-pool regen is the canonical example.
- Derived stats in Hero Stats use whole attributes where the game truncates before applying conversions (example: Medusa mana at high levels). Do not use fractional attributes directly for HP / mana / primary-attribute damage when the in-game stat is based on floored attributes.
- If an innate changes in a later patch (numbers changed, formula changed, reworked, or removed), Hero Stats must respect the patch-gated version of that innate for the selected patch history / latest snapshot logic. Do not assume innate formulas are timeless.
- The main `Damage` column in Hero Stats shows average damage only. `Dmg min` / `Dmg max` belong to `Expanded` as separate columns.
- If a hero has a stat-affecting innate that is actually modeled in Hero Stats, show the mini innate icon next to the hero name. The icon must disappear when the `Innates` toggle is off, and stay on the same line as the hero name.

## Sticky divider overlays

- The vertical blue sticky-divider line must clamp to the real visible table bottom, not the full scroll-box bottom. This prevents the line from hanging below short filtered result sets.
- Divider visibility must depend on real horizontal overflow plus `scrollLeft > 0`, not just `scrollLeft > 0` in isolation.
- In `heroes_dyn.html`, turning `Hide old` on resets `scrollLeft` to `0` before re-anchoring the divider. Anchor the divider from the sticky `Hero` header cell, not from a body row.

## Навигационные стрелки (ПРАВИЛО)

Все **навигационные / направленные стрелки** на сайте должны использовать единый дизайн: сплошной **пиксельный SVG-треугольник** (`shape-rendering=crispEdges`, золото `#e3c46a`) на золото-кожаном кружке (`linear-gradient(180deg,#3b2e1d,#2a2014)`, рамка `2px solid #e3c46a`). Эталон — `.back-to-top` / `.nav-back-arrow` / `.version-nav-arrow` (`is-prev`/`is-next`). Это касается и стрелок слайдера terrain (`.tc-chev-l/.tc-chev-r` переиспользуют те же data-URI пиксель-треугольники). НЕ использовать CSS-border-треугольники, юникод-стрелки (▲◄►) или эмодзи для навигации.

## Глобальные UI-элементы (во всех страницах через `site_common.py` / `scripts.js`)
- **Лого** — простой `<img class="nav-brand-logo" src="…/icons/logo_knight.png">` (пиксельный рыцарский шлем, прозрачный фон). Раньше был шлем `header-helmet.png` с canvas-эффектом EyeFire — удалён целиком (файлы + код).
- **Режим для дальтоников** (2026-10-09): значок-глаз `button.cb-toggle` в правом конце шапки (`.nav-end`, в рамке
  как `.version`, той же высоты 38px; иконки `icon_cb_off/on.png` из `scripts/gen/gen_cb_icon.py`). Выключен —
  серый тусклый глаз; включён — цветной глаз над золотой полоской с искрами, как у активной вкладки шапки
  (`.nav-ember`; владелец: «непонятно, когда иконка нажата»). Ставит
  `html.cb-mode`, помнится в localStorage `cbMode`; ранний `<script>` в начале `<nav>` ставит класс до отрисовки
  бейджей. Меняются ТОЛЬКО теги (бейджи, % у строк, счёт патча `.ec-score`, цифры в подсказках предметов, ячейки
  динамики): у каждого тега свой цвет из `CB_TAGS` (по палитре Okabe–Ito: BUFF голубой, NERF оранжевый, NEW жёлтый,
  REWORK розово-лиловый, SWAP сине-зелёный, QoL тёмно-синий, DEL вишнёвый, MISC светло-серый). Тест симулирует
  зрение дейтеранопа/протанопа: любая пара тегов ≥ `MIN_DE` (14; на обычном сайте SWAP/MISC = 6). Текст тега
  сохраняет яркость (читается), фон и рамка — цвет тега, плотнее обычного. CSS — генерируемый блок перед блоком
  телефонов (`scripts/gen/gen_colorblind_css.py`, `TAG_SELECTORS`; `--check` и `tests/test_colorblind.py` ловят
  забытую перегенерацию), ячейки динамики — `DYN_TAG_RGB_CB` в scripts.js (тест держит равным `CB_TAGS`). Новое
  правило с цветом тега → перезапустить генератор. Карта, таблицы, атрибуты — не трогаем (владелец: «только для
  тегов/cells»).
- **Плавающие кнопки** `.nav-back-arrow` (назад в календарь/патч, низ-слева) и `.back-to-top` (низ-справа) — золото/кожа кружок (стиль index) + сплошной пиксельный SVG-треугольник (как `.version-nav-arrow`). Обе во НИЖНИХ углах (back-стрелка раньше была top-left и налезала на теги; JS больше НЕ выставляет ей inline `top`).


## Поиск на страницах патчей (2026-09-26)

Лупа в правом нижнем стеке. Горячая клавиша — `\`, по физической клавише (`e.code === "Backslash"`), поэтому
работает в любой раскладке; повторное нажатие (в том числе из поля поиска) закрывает поиск, сам символ в поле
не попадает. Поле принимает только английский: русская буква заменяется английской с той же клавиши
(«щсефкшту» → «octarine»), остальное не-ASCII отбрасывается. Код — `src/scripts.js`, блок «Patch pages: the
search sits behind the round loupe button».


## Полоса истории (квадратики патчей) открывается на своём патче (2026-10-06)

`scripts.js dynDefaultOffset`: на странице патча текущий патч стоит посередине полосы (слева старее, справа новее) и
подсвечен (`.dyn-cell-wrap.current`); у краёв списка — первым или последним. Раньше полоса всегда показывала
последние 12 патчей: на 7.38 самого 7.38 в ней не было, на 7.08 полоса Blink Dagger была пустой. Страницы героев,
предметов и юнитов (без версии в выборе патча) — как раньше, последние патчи. Стрелки листают от этого места.

## Talent tree icon, Dynamics hover lens, Changelog columns (2026-09-26)

- **Talent tree** (`patch/talent_tree.py`, post-pass in `patch/page.py save_html`): the Talents block icon lights
  the changed twigs in gold, as the game lights a taken talent. Side = the hero's talent slots of THAT patch
  (`data/rules/talent_slots.json`, built by `tools/build_talent_slots.py` from the d2vpkr npc_heroes.txt
  history): the first 8 `special_bonus_*` slots in order, first of each pair = RIGHT. Source: the game's own
  talent picker `panorama/layout/hud/dota_hud_stat_branch.vxml_c` (pak01): buttons Upgrade1/3/5/7 are
  `BranchChoice RightBranch`, Upgrade2/4/6/8 `LeftBranch` (Upgrade N = the N-th talent slot). Liquipedia agrees
  (14 heroes, 56 levels, 0 mirrored); no need to re-check per patch. A row is placed by words vs. today's tooltip + the ability/value the talent changed
  in its own patch; a row that fits neither side lights nothing. Gold copy of the icon: `icons/misc/talents_gold.svg`.
  Each placed row gets `data-tt="20r 25r"`, each twig its own gold `<image data-b>`; scripts.js "TALENT TREE"
  lights only the twigs of rows a filter leaves visible (a hidden NERF row's twig must not glow). Unlit twigs dim to 42%.
  Any changed talent lights its twig, not only a SWAP. If a hero's twig stays dark, check talent_slots.json first:
  from 7.39 some KV hero heads sit at column 0 (Earth Spirit, Slark) and the builder used to merge them into the
  hero above (fixed 2026-10-09, `test_a_single_changed_talent_lights_its_twig_for_unindented_heroes`).
- **Dynamics matrices**: cells never pop; one `.dyn-lens` (scripts.js) with a copy of the hovered pill grows
  over it and glides between cells (transform/opacity only). A per-cell transition repaints every passing cell.
- **Changelog**: chip | beetle | text columns (`--clog-cat-w`), titles, bullets and small changes start on one x;
  small changes are separated by faint lines. Keep titles short (about 90 characters).

## Телефоны (2026-10-05)

С коммита 356e152c у каждой страницы есть `<meta name="viewport" content="width=device-width">`
(`builders/site_common.head_common`). До этого телефон рисовал страницу шириной 980 px и ужимал её до 40 %: текст
строк выходил примерно 6 px, а правила для узкого экрана не срабатывали вовсе.
- Все правила под телефон — в **последнем** блоке `styles.css` «PHONES», внутри `@media (max-width: 760px)`. ПК они не
  трогают: полностраничные снимки на 1440 px до и после совпадают пиксель в пиксель.
- **Страница не шире экрана** (`scrollWidth <= innerWidth`): широкое (вкладки, фильтры, таблицы уровней, календарь,
  таблица лагерей, таблицы Silent Changes) прокручивается внутри своего контейнера (`overflow-x: auto`), а не всей
  страницей. Невидимые копии подсказок (`.info-pop` в строке, `::after` у чипов) раньше растягивали страницу до 1069 px:
  на телефоне они скрыты. «?» показывает общий `.info-pop-body` из scripts.js, `::after`-подсказки по нажатию
  открываются полосой над угловыми кнопками.
- Текст строк не меньше 14 px (сейчас 15). Кнопки фильтров и вкладок не ниже 32 px.
- Угловые круглые кнопки — 38 px, одним рядом внизу справа.
- Длинная группа бейджей (3 и больше: «-8%, -8%, -9%», «0% start +21% L20 -21% end») уходит под текст, по-прежнему
  справа.
- Карточки «было → стало» (свойства, способности, компоненты, игровые формулы) ставятся друг под другом, стрелка
  поворачивается вниз.
- Полоса истории (квадратики патчей) — отдельной строкой под иконкой и именем.
- Замеры 2026-10-06 (375 и 390 px, 12 страниц): ширина страницы была 443–1069 px, стала ровно ширина экрана; мелких
  кнопок было 5–13 на странице патча, стало 0.
