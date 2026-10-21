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
- **Врождённые способности** — `data/rules/hero_stat_innates.json` через `builders/innate_rules.load()` (не читать JSON напрямую). Эффект с картой `"kv"` (`поле: [ключ AbilityValues, value|hero_levelup, множитель]`) для каждого патча новее `_checked_version` берёт число из `data/stats/<v>/heroes/` и сам заводит запись истории. Старые патчи — только ручная история: до 2026-10-21 часть слепков была снята до своего патча (см. ниже), сейчас все — сборки патчей. `tests/test_innate_rules_kv.py` (`innate_rules.review`) падает, если новый патч переделал врождённую без `kv`, дал герою новую или добавил героя: проверить, поправить правило, поднять `_checked_version`.
- **Какая способность врождённая в каком патче** — `data/rules/innate_history.json` (`tools/build_innate_history.py`, шаг `innate_history` в `tools/new_patch.py`): с 7.34e — флаг `"Innate" "1"` в файлах героев, раньше — патчноуты (Treant 7.23c, Alchemist и Ogre 7.33). Правило героя начинается с его `since`: эффект без своей даты наследует её (`innate_rules._inherit_hero_since`; до 2026-10-21 Lunar Blessing Luna, врождённая с 7.37, считалась во всех патчах с 7.08). Многие врождённые до 7.41 были аспектами или обычными способностями (Axe, Sven, Dragon Knight, Lifestealer — с 7.41, Dark Seer — с 7.38): `tests/test_innate_history.py` падает, если `since` правила раньше, чем способность стала врождённой.
- **Слепок = сборка САМОГО патча** — первая сборка не раньше даты, в патчноутах которой уже есть ключи `DOTA_Patch_<v>_` (`tools/fetch_stats.find_patch_build`). Старое правило «первая сборка в день выхода» дало сборку ДО патча у 14 патчей (7.33b, 7.33e, 7.34c, 7.34d, 7.35b, 7.36b, 7.36c, 7.37c, 7.37d, 7.37e, 7.39b, 7.39c, 7.41 = 6726 вместо 6728, 7.41b): 2026-10-21 их `heroes/`, `abilities.json`, `ability_ids.json` перезалиты из архива клиента (`items.json` / `units.json` / `heroes.json` и так брались по истории файлов — из конца жизни патча). 7.33c не тронут: в архиве дыра 13–24.05.2023. Правила врождённых, выверенные по старым слепкам, сдвинуты на патч, который называют заметки (Elder Titan, KotL, Rubick, Techies — с 7.41; Medusa 7.37e). `tests/test_innate_history.py`: `KNOWN_LAGGED` пуст — новый слепок до патча роняет CI; числа правил сверяются со ВСЕМИ слепками (исключения `ON_PURPOSE`: Ursa — макс. ранг, Luna 7.37e–7.40c — другая запись того же числа).
- **Списки сущностей**, которых нет в файлах (лагеря крипов, ярусы чар, фантомные предметы, призывные юниты, время ярусов нейтралок, ручные ячейки Neutral Abilities с `ABIL_MANUAL_CHECKED`) — `tests/test_roster_guards.py`: новый крип / чара / способность в файлах игры без строки в списке = падение с подсказкой, куда дописать. Ауры крипов (`AURA_SELF`) и предметы AoE Increase (`AOE_BONUS_KEYS`) уже читаются из файлов.
