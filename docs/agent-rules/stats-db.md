# База статов (stats DB) и маппинг полей

## База статов

Файлы `data/stats/{version}/heroes.json` и `items.json` — поля из npc_heroes.txt / items.txt. Покрытие: с 7.33 (источник muk-as/DOTA2_CLIENT). Для патчей старше 7.33 БД нет, fallback на t().

Ключи из npc_heroes.txt: `ArmorPhysical`, `AttackDamageMin/Max`, `AttackRate`, `MovementSpeed`, `AttackRange`, `AttributeBaseStrength/Agility/Intelligence`, `AttributeStrengthGain/AgilityGain/IntelligenceGain`, `StatusHealth`, `StatusMana`, `StatusHealthRegen`, `StatusManaRegen`.
Ключи из items.txt: `ItemCost`, `ItemCooldown`, `AbilityManaCost`.

**Ловушка: слепки-копии прошлого патча (2026-09-27).** Скачиватель (`D:\Sloppy Patches\fetch_stats.py`,
`find_commit_for_patch`) берёт первый коммит d2vpkr, датированный днём патча. Он бывает сделан ДО выхода патча,
и тогда слепок равен прошлому патчу: `items.json` 7.41 был побайтно 7.40c (вся переработка предметов 7.41 лежала в
7.41a), в 7.37e у Khanda остался рецепт 7.37d (600, а не 500). Эталон — история items.txt по патчам
(`~/outputs/valve-revealed-weights-20260915/items_history`, по ней же считаются веса). `tools/resync_item_snapshots.py`
пересобирает `items.json` из неё; тест `tests/test_item_snapshots_match_history.py` (пропускается без истории).
Обходы «взять цены из следующего патча» (auto_components_change, `_postprocess_unstated_total_cost`) убраны: они
приписывали бы патчу чужое изменение.

## Маппинг описаний → поля БД (HERO_STAT_MAP в generate_patch_code.py)

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
