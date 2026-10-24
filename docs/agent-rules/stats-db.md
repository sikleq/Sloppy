# База статов (stats DB) и маппинг полей

## База статов

Файлы `data/stats/{version}/heroes.json` и `items.json` — поля из npc_heroes.txt / items.txt. Покрытие: с 7.33 (источник muk-as/DOTA2_CLIENT). Для патчей старше 7.33 БД нет, fallback на t().

Ключи из npc_heroes.txt: `ArmorPhysical`, `AttackDamageMin/Max`, `AttackRate`, `MovementSpeed`, `AttackRange`, `AttributeBaseStrength/Agility/Intelligence`, `AttributeStrengthGain/AgilityGain/IntelligenceGain`, `StatusHealth`, `StatusMana`, `StatusHealthRegen`, `StatusManaRegen`.
Ключи из items.txt: `ItemCost`, `ItemCooldown`, `AbilityManaCost`.

**Ловушка: слепки-копии прошлого патча (2026-09-27).** Скачиватель (`tools/fetch_stats.py`,
`find_commit_for_patch`) берёт первый коммит d2vpkr, датированный днём патча. Он бывает сделан ДО выхода патча,
и тогда слепок равен прошлому патчу: `items.json` 7.41 был побайтно 7.40c (вся переработка предметов 7.41 лежала в
7.41a), в 7.37e у Khanda остался рецепт 7.37d (600, а не 500). Эталон — история items.txt по патчам
(`outputs/valve-revealed-weights-20260915/items_history`, по ней же считаются веса). `tools/resync_snapshots.py`
пересобирает `items.json`, `heroes.json` и `units.json` (история npc_heroes.txt — `heroes_history`; npc_units.txt — `units_history`, скачана 2026-09-27 из dotabuff/d2vpkr по коммитам плана истории предметов) — у героев это чинит подсказки «Now it's …» / «Before this patch it was changed in …» (Night Stalker 7.36a писал «−1.25, now 1.5» вместо 0.25); тест `tests/test_snapshots_match_history.py` (пропускается без истории).
Обходы «взять цены из следующего патча» (auto_components_change, `_postprocess_unstated_total_cost`) убраны: они
приписывали бы патчу чужое изменение.

**С 2026-10-24 эталон — сборка самого патча** из архивов файлов игры (`tools/item_history.py`: GameTracking 7.08 …
7.32d, DOTA2_CLIENT 7.32e …; сборка = первая с патчноутами патча и без патчноутов следующего + исправления той же ночи
≤12 ч). История d2vpkr («последний коммит ≤ выход + 4 дня») держала соседний патч: 52 слепка героев, предметов и юнитов
(7.13 — броня и скорость из 7.13b, 7.33d/7.33e/7.34d — герои до патча, …) перезаписаны, каждое расхождение сверено с
заметками Valve. `tools/resync_snapshots.py` берёт архив по умолчанию (`--d2vpkr` — старый источник); тест
`tests/test_snapshots_match_history.py` пропускается без клонов архивов. Hero Stats (`_history_for`) переносит изменение
на заметку прошлого подпатча, только если у патча сборки своей заметки об этом поле нет.

## Маппинг описаний → поля БД (`_BSTAT_FIELD` в generate_patch_code_v2.py)

При паттерне `"увеличено/уменьшено на N"` (без явного from-to) генератор смотрит первое совпадение:

| English текст | KV-поле | l_flag |
|---|---|---|
| base health regen | StatusHealthRegen | False |
| base mana regen | StatusManaRegen | False |
| base health | StatusHealth | False |
| base mana | StatusMana | False |
| base armor | ArmorPhysical | False |
| base strength/agility/intelligence | Attribute Base * | False |
| strength/agility/intelligence gain | AttributeStrength/Agility/Intelligence Gain | False |
| base attack time | AttackRate | True |
| movement/move speed | MovementSpeed | False |
| attack range | AttackRange | False |
| base damage | AttackDamageMin (avg с Max) | False, is_dmg=True |

## Формат файлов героев с 7.41f (ловушка)
- `data/stats/<ver>/npc_heroes.txt` с 7.41f — только список `#base "heroes/npc_dota_hero_<slug>.txt"`. Героев читать вместе с включениями: `tools/slim_from_kv.load_kv`, `builders/aoe_increase._heroes_root`.
- `heroes/npc_dota_hero_<slug>.txt` до 7.41e: `"DOTAAbilities" { <ability> {…} }`. С 7.41f: `"DOTAHeroes" { npc_dota_hero_<slug> { …, "AbilityDefinitions" { <ability> {…} } } }`. Способности брать **только** через `builders.site_common.hero_ability_blocks(kv)`, он понимает оба варианта. Иначе страница молча теряет все способности: так было с AoE Increase, Silent changes 7.41f и врождёнными способностями в Hero Lab. Тест: `tests/test_hero_kv_layout.py`.
- С 7.41f в slim `heroes.json` нет блока `npc_dota_hero_base` (120 HP, 75 маны, 25% магрезиста…). Hero Stats / Hero Lab берут его из `heroes_raw.json` (`heroes_stats._inject_hero_base`), а не из `_FIELD_DEFAULTS`. Тест: `tests/test_hero_base_block.py`.

## Новый патч — числа без правки кода (2026-10-21)
Цель владельца: вышел патч (новый `data/stats/<v>/` + строка в `RELEASE_HISTORY`) — все страницы подхватывают новые значения сами. Правило: число, которое есть в файлах игры, **читать**; число, которого там нет, держать в одном месте и закрыть **тестом-сторожем**, который падает с понятным текстом в день, когда игра с ним разошлась.
- **Константы атрибутов** (22 HP за силу, 1/6 брони за ловкость, 12 маны за интеллект, 0.45 у универсалов…) живут в движке, в KV их нет. Одна копия — `patch/game_constants.py` (Python всех страниц; в `scripts.js` они приходят встроенным JSON: `hs-game-constants` / `data.constants` Hero Lab). `tests/test_game_constants.py` сверяет их с подсказками самой игры в `dota_english.txt` (`DOTA_HeroStats_*_Desc`, `DOTA_Loadout_PrimaryAttribute_Universal_Tooltip`). Изменилось — добавить строку истории.
  История HP в Hero Stats использует `hp_per_strength(version, primary=...)`: `STR_HP_HIST` (20 → 18 в 7.13 → 20 в 7.21 → 22 в 7.33) и `PRIMARY_ATTRIBUTE_BONUS_HIST` (+25% для силы у силовых героев с 7.13 до 7.21). Бонус применяется только к HP от силы, не к базовому HP. Физическое и магическое EHP наследуют этот расчёт. Изменения правил не сдвигаются на предыдущий патч эвристикой запоздалых KV-слепков. Регрессии: `tests/test_hero_hp_history.py`.
  **Все вторичные бонусы — по своему патчу** (2026-10-22): `per_point(история, патч, primary=)` — броня за ловкость `AGI_ARMOR_HIST` (0.17 → 0.16 в 7.13 → 1/6 в 7.27), сопротивление магии `INT_MR_HIST` (0.15% до 7.13, 0.1% с 7.33) и `STR_MR_HIST` (0.08% в 7.13–7.25), реген `STR_HPREG_HIST` / `INT_REGEN_HIST` (фикс. 0.1 / 0.05 с 7.20; «0.09» в подсказках 7.20–7.40c — ошибка текста) и `*_AMP_HIST` (% усиления до 7.20), скорость `AGI_MS_HIST` (% до 7.26), +25% основного атрибута 7.13–7.20 ко всем его бонусам (и скорость атаки). Источники: таблица Valve в 7.13, заметки 7.20 (блог) / 7.26 / 7.27 / 7.33, подсказки `DOTA_HeroStats_*_Desc` по патчам (`tools/loc_history`) и server.dll 11 сборок 2018–2026 (поля конструктора игрового режима, проверено агентом dota2-ida-researcher 2026-10-22). Мана за интеллект 12 во всех патчах (строки 14 и 11 в старой таблице игра никогда не имела). Столбец → его истории: `RULES_OF_COLUMN` (правка правил — правка своего патча). Средние по категориям (`entity_changes`) и JS считают только текущий патч — им сегодняшние значения. Формула брони — `ARMOR_FORMULA_HIST` / `armor_reduction(броня, патч)`: до 7.20 — 0.05·A / (1 + 0.05·A), в 7.20–7.26 — 0.052·A / (0.9 + 0.048·A) (заметки 7.20 — блог Valve, в файле патчноутов их нет), с 7.27 — 0.06·A / (1 + 0.06·A) (все три — по server.dll); Hero Stats и история крипов (`creeps_common.armor_factor(a, version)`) берут формулу патча клетки. Тесты: `tests/test_hero_attr_history.py`, `test_secondary_bonus_history`. Шапки STR / AGI / INT / Attr в Hero Stats при наведении показывают эту историю (`ATTRIBUTE_RULES` → `attribute_history()` / `attribute_today()`, подсказка stat-hist-tip с `th[data-hist]`): новая строка истории в `game_constants` попадает туда сама.
- **Врождённые способности** — `data/rules/hero_stat_innates.json` через `builders/innate_rules.load()` (не читать JSON напрямую). Эффект с картой `"kv"` (`поле: [ключ AbilityValues, value|hero_levelup, множитель]`) для каждого патча новее `_checked_version` берёт число из `data/stats/<v>/heroes/` и сам заводит запись истории. Старые патчи — только ручная история: до 2026-10-21 часть слепков была снята до своего патча (см. ниже), сейчас все — сборки патчей. `tests/test_innate_rules_kv.py` (`innate_rules.review`) падает, если новый патч переделал врождённую без `kv`, дал герою новую или добавил героя: проверить, поправить правило, поднять `_checked_version`.
- **Какая способность врождённая в каком патче** — `data/rules/innate_history.json` (`tools/build_innate_history.py`, шаг `innate_history` в `tools/new_patch.py`): с 7.34e — флаг `"Innate" "1"` в файлах героев, раньше — патчноуты (Treant 7.23c, Alchemist и Ogre 7.33). Правило героя начинается с его `since`: эффект без своей даты наследует её (`innate_rules._inherit_hero_since`; до 2026-10-21 Lunar Blessing Luna, врождённая с 7.37, считалась во всех патчах с 7.08). Многие врождённые до 7.41 были аспектами или обычными способностями (Axe, Sven, Dragon Knight, Lifestealer — с 7.41, Dark Seer — с 7.38): `tests/test_innate_history.py` падает, если `since` правила раньше, чем способность стала врождённой.
- **Слепок = сборка САМОГО патча** — первая сборка не раньше даты, в патчноутах которой уже есть ключи `DOTA_Patch_<v>_` (`tools/fetch_stats.find_patch_build`). Старое правило «первая сборка в день выхода» дало сборку ДО патча у 14 патчей (7.33b, 7.33e, 7.34c, 7.34d, 7.35b, 7.36b, 7.36c, 7.37c, 7.37d, 7.37e, 7.39b, 7.39c, 7.41 = 6726 вместо 6728, 7.41b): 2026-10-21 их `heroes/`, `abilities.json`, `ability_ids.json` перезалиты из архива клиента (`items.json` / `units.json` / `heroes.json` и так брались по истории файлов — из конца жизни патча). 7.33c уже был сборкой патча (5713: сборки 5712 не было, вышла 14.05 по GameTracking; локальный архив записал её 24.05 — даты коммитов там — даты записи, поэтому отставание считается в сборках, `MAX_NOTES_LAG_BUILDS`). Правила врождённых, выверенные по старым слепкам, сдвинуты на патч, который называют заметки (Elder Titan, KotL, Rubick, Techies — с 7.41; Medusa 7.37e). `tests/test_innate_history.py`: `KNOWN_LAGGED` пуст — новый слепок до патча роняет CI; числа правил сверяются со ВСЕМИ слепками (исключения `ON_PURPOSE`: Ursa — макс. ранг, Luna 7.37e–7.40c — другая запись того же числа).
- **Списки сущностей**, которых нет в файлах (лагеря крипов, ярусы чар, фантомные предметы, призывные юниты, время ярусов нейтралок, ручные ячейки Neutral Abilities с `ABIL_MANUAL_CHECKED`) — `tests/test_roster_guards.py`: новый крип / чара / способность в файлах игры без строки в списке = падение с подсказкой, куда дописать. Ауры крипов (`AURA_SELF`) и предметы AoE Increase (`AOE_BONUS_KEYS`) уже читаются из файлов.
