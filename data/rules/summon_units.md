# summon_units.json: откуда взяты числа (патч 7.42a)

Файл `summon_units.json`: 76 записей, по одной на уровень, который различает игра. Поле `source` у каждой записи показывает, какие поля взяты не из KV юнита: `ability:<способность>.<ключ>`, `code` (считает код игры) или `none`. Поле `unsure_fields` перечисляет догадки внутри записи. `sure: false` значит, что главные числа не доказаны.

Источники: `data/stats/7.42a/npc_units.txt` (KV юнитов, с учётом `include_keys_from` и базового юнита), `data/stats/7.42a/heroes/npc_dota_hero_*.txt` (способности героев лежат там внутри файла героя, а не в `abilities.json`), `items.txt` (Book of the Dead).

| Юнит (ключи) | Записей | Что перекрывает способность | Что не уверено |
|---|---|---|---|
| Warlock Golem, `warlock_golem_1..3` | 3 | `warlock_rain_of_chaos`: HP, реген, броня (KV 0, в игре 8/12/14), скорость, урон, золото | разброс урона ±10 взят из KV |
| Golem от Aghanim, `warlock_golem_scepter_1..3` | 3 | урон 80/120/160, HP и золото `*_scepter` | реген, броня, скорость взяты как у обычного (догадка) |
| Lycan Wolf, `lycan_wolf_1..4` | 4 | `lycan_summon_wolves`: урон 22/32/42/52 (KV устарел: 22/28/34/40); HP и BAT совпали с KV | разброс ±1 взят из KV волка 1; волки 5-6 не включены |
| Treant, `furion_treant_1..4` | 4 | `furion_force_of_nature`: HP 425-500, урон 15/25/35/45, броня 1-4, скорость, золото 18-24, опыт 30 | разброс урона +3 (догадка, что значение способности это минимум); талант x3 не применён; `npc_dota_furion_treant_large` в способности не используется (мёртвый KV), отдельной записи нет |
| Spiderling, `broodmother_spiderling_1..3` | 3 | `broodmother_spawn_spiderlings`: прибавка урона 0/6/12 (подсказка 18.5/24.5/30.5 сходится с KV) | не проверено, что прибавка действует на пауков из других источников |
| Spiderite, `broodmother_spiderite` | 1 | ничего | `sure: false`: бонус урона паукам может действовать и на него |
| Visage Familiar, `visage_familiar_1..3` | 3 | `visage_summon_familiars`: HP 450/600/750 (KV 500/600/700), скорость 430 (KV 420) | фасет Faithful Followers меняет дальность, скорость, награду (не применён) |
| Enigma Eidolon, `enigma_eidolon_1..5` | 5 | `enigma_demonic_conversion`: HP, сопротивление магии, скорость, дальность, урон (в KV 0), награда | `sure: false`: соответствие уровня способности ступени KV (lesser/eidolon/greater/dire) и рост каждые 6 атак проверить кодом нельзя; `dire` тут ступень роста, а не команда Dire; деления «только Radiant» в KV не найдено; запись 5 (`dire_eidolon2`) только по KV |
| Forged Spirit, `invoker_forged_spirit_1..9` | 9 | `invoker_forge_spirit`: HP и дальность по Quas, урон, мана, броня по Exort (KV это заглушки: HP 5, дальность 0) | уровень в записи = Quas = Exort; урон принят как min=max |
| Razorback (boar), `beastmaster_boar_1..4` | 4 | `beastmaster_summon_razorback`: HP, урон, скорость, опыт | дальность 550 и дальний бой взяты прямо из KV и выглядят странно для кабана, не проверены |
| Raptor (hawk), `beastmaster_raptor_1..4` | 4 | `beastmaster_summon_raptor`: HP, сопротивление магии, золото, опыт | `sure: false`: обычной атаки нет (пикирование 70/110/150/190 магического урона); скорость 455 это только минимум (максимум 1100) |
| Ancient Thunderhide, `beastmaster_thunderhide` | 1 | `beastmaster_summon_thunderhide`: HP 2100, урон 90, скорость 355 (KV устарел) | урон 90 принят как min=max |
| Undying Zombie и torso | 2 | `undying_tombstone.zombie_health` = 1 пип = 4 HP (Pip Health 7.42, server.dll 6983; KV говорит 2) | урон: подсказка 34 против KV 33-36, оставлен KV; torso идентичен зомби |
| Brewling Earth / Storm / Fire, `brewmaster_*_1..4` | 12 | ничего: подсказки Primal Split совпадают с KV | уровень 4 только с Aghanim |
| Brewling Void, `brewmaster_void_1..3` | 3 | ничего | `sure: false`: в Primal Split Void нет, как и когда он призывается в 7.42a, не найдено |
| Chen Zealot | 1 | зависит от уровня героя (`hero_levelup`): HP 400+50/ур., урон 5+2/ур., скорость 5+2/ур. | `sure: false`: как это складывается с KV (HP 550), решает код; показан KV |
| Clinkz Skeleton Archer (Skeleton Walk) | 1 | `clinkz_wind_walk`: HP 2 пипа = 8, BAT 1.6; урон = 20% урона Клинкза (числа нет, `null`) | `sure: false` по урону |
| Clinkz Skeleton Archer (Burning Army) | 1 | в способности только дальность, число, интервал; HP, урон считает код (`null`) | `sure: false`: вероятно те же 2 пипа и 20% урона (догадка) |
| Warlock Imp minor | 1 | `warlock_eldritch_summoning`: HP и скорость зависят от уровня героя, смещение неизвестно, поэтому `null` | `sure: false` |
| Warlock Imp major | 1 | ничего (таблицы бонусов из 5 значений без привязки) | `sure: false`: что задаёт уровень и откуда призывается, не найдено |
| Wraith King Skeleton, `wraith_king_skeleton_1..4` | 4 | `skeleton_king_bone_guard`: подсказка урона 34/39/43/49 (KV 29-34), золото 5, опыт 5 | как подсказка раскладывается на min/max: догадка (max = подсказка, min = −5) |
| Book of the Dead, `book_of_the_dead_{warrior,archer}_1..3` | 6 | ничего: у предмета `item_demonicon` нет статов юнитов, только длительность 65 | `sure: false`: какой уровень юнита призывает предмет, в коде; показан KV `npc_dota_necronomicon_*`; старый Necronomicon устарел (IsObsolete), его подсказки (800/1200/1600 HP) с KV не совпадают |

## Проверка по server.dll 6997 (dota2-ida-researcher, 2026-11-27)

Таблица выше записана до проверки. Что изменила проверка:

| Юнит | Итог | В файле |
|---|---|---|
| Golem от Aghanim | урон `golem_dmg_scepter` ±5 (75–85 / 115–125 / 155–165), броня, реген, скорость — ключи обычного голема | `sure: true`, показан |
| Book of the Dead | предмет всегда призывает юнитов 3-го уровня, 2 воина и 2 лучника, бафф +100% HP и +75% базового урона (числа в коде): воин 1600 HP, урон 122.5–148.75; лучник 1300 HP, 122.5–140 | `_3` — `sure: true`, показаны; `_1`, `_2` — юниты Underlord, не показаны |
| Raptor | обычной атаки нет; скорость 455 у Бистмастера, до 1100 с расстоянием до своей точки | `sure: true`, показан |
| Enigma Eidolon 1–4 | уровень способности 1–4 = lesser / eidolon / greater / dire; HP = база + 3% текущего HP Энигмы; деление на 7-й атаке | `sure: false`: HP зависит от Энигмы, ждёт решения владельца, как показать |
| Chen Zealot | HP = max(550 + 12·n, 400 + 50·L), скорость 330 + 2·L, урон зависит от L | `sure: false`: зависит от уровня Чена |
| Warlock Imp minor | HP 5 + 15·L, скорость 297 + 3·L | `sure: false`: зависит от уровня Варлока |
| Clinkz скелеты | оба вида одинаковые: 2 пипа, BAT 1.6, 20% урона Клинкза | `sure: false`: урон от Клинкза |
| `enigma_eidolon_5`, Major imp, Void Brewling | в игре 7.42a не появляются | `not_in_game: true` |
| Spiderite | Spawn Spiderite создаёт обычного паучка (`npc_dota_broodmother_spiderling`) с бонусами Spawn Spiderlings; юнит `npc_dota_broodmother_spiderite` код только сравнивает по имени, не создаёт | `not_in_game: true`, его роль — строки Spiderling |

Полный разбор с адресами: заметка сессии `summons_confirm_742a.md` (папка заметок сессий, не в репозитории).

## Что сделано кодом, а не данными

- Pip Health 7.42: у зомби и скелетов Клинкза HP задан пипами (1 пип = 4 HP), по заметке `dota_mech_pip_health.md` (проверено по server.dll 6983). Остальные призванные юниты на пипы не переведены.
- Урон скелетов Клинкза считается как процент от урона героя: числа нет.
- Рост эйдолонов Enigma, уровень героя у Chen и Warlock, призыв Book of the Dead: только код.

## Талантами и фасетами не применено

Все значения даны без талантов, фасетов и Aghanim/Shard-прибавок, кроме отдельных записей Golem от Aghanim и Brewling уровня 4. Прибавки перечислены в `note` каждой записи.
