# База статов (stats DB) и маппинг полей

## База статов

Файлы `data/stats/{version}/heroes.json` и `items.json` — поля из npc_heroes.txt / items.txt. Покрытие: с 7.33 (источник muk-as/DOTA2_CLIENT). Для патчей старше 7.33 БД нет, fallback на t().

Ключи из npc_heroes.txt: `ArmorPhysical`, `AttackDamageMin/Max`, `AttackRate`, `MovementSpeed`, `AttackRange`, `AttributeBaseStrength/Agility/Intelligence`, `AttributeStrengthGain/AgilityGain/IntelligenceGain`, `StatusHealth`, `StatusMana`, `StatusHealthRegen`, `StatusManaRegen`.
Ключи из items.txt: `ItemCost`, `ItemCooldown`, `AbilityManaCost`.

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
