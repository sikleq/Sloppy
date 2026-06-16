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
- блёрб `.mr-blurb.inbox-bar` → `padding: 22px 28px 0` (низ 0);
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
- **Плавающие кнопки** `.nav-back-arrow` (назад в календарь/патч, низ-слева) и `.back-to-top` (низ-справа) — золото/кожа кружок (стиль index) + сплошной пиксельный SVG-треугольник (как `.version-nav-arrow`). Обе во НИЖНИХ углах (back-стрелка раньше была top-left и налезала на теги; JS больше НЕ выставляет ей inline `top`).
