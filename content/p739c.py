from patch.api import *

_NC_CDN = "../icons/units/npc_dota_neutral_"

def build():
    write_head("7.39c", "24.06.2025")

    # ===== GENERAL UPDATES =====
    W(section("General Updates"))

    W(plain_header("Map Objectives"))
    W(ul_open())
    W(li("Roshan: Melee attacks against couriers are now treated as melee hero attacks", t("REWORK")))
    W(li("Tormentor: Reflect no longer considers creep-heroes for the damage reflected", t("REWORK"), extra=inline_note("Lone Druid's Spirit Bear is an exception for this")))
    W(ul_close())

    W(plain_header("Terrain Changes", terrain_link="7.39c"))
    W(ul_open())
    W(li("Watchers by the respective Wisdom shrines have been slightly moved away from the nearby ramps", t("MISC")))
    W(li("Watcher activation range decreased from 300 to 200", b(300, 200)))
    W(ul_close())

    # ===== NEUTRAL CREEP UPDATES =====
    W(section("Neutral Creep Updates"))

    # Boglet
    W(unit_header("Boglet", _NC_CDN + "froglet.png"))
    W(ability("Arm of the Deep", icon_url="../icons/abilities/frogmen_arm_of_the_deep.png"))
    W(ul_open())
    W(li("Arm of the Deep: Cast point increased from 0.2s to 0.3s", b(0.2, 0.3, l=True)))
    W(ul_close())

    # Croaker
    W(unit_header("Croaker", _NC_CDN + "grown_frog.png"))
    W(ability("Tendrils of the Deep", icon_url="../icons/abilities/frogmen_tendrils_of_the_deep.png"))
    W(ul_open())
    W(li("Tendrils of the Deep: Cast point increased from 0.2s to 0.3s", b(0.2, 0.3, l=True)))
    W(ul_close())

    # Ancient Croaker
    W(unit_header("Ancient Croaker", _NC_CDN + "ancient_frog.png"))
    W(ability("Congregation of the Deep", icon_url="../icons/abilities/frogmen_congregation_of_the_deep.png"))
    W(ul_open())
    W(li("Cast point increased from 0.2s to 0.3s", b(0.2, 0.3, l=True)))
    W(ul_close())

    # Ancient Prowler Shaman
    W(unit_header("Ancient Prowler Shaman", _NC_CDN + "prowler_shaman.png"))
    W(ability("Petrify", icon_url="../icons/abilities/spawnlord_master_freeze.png"))
    W(ul_open())
    W(li("No longer has a health threshold restriction when the Shaman is controlled by a player", t("MISC")))
    W(ul_close())

    # ===== ITEM UPDATES =====
    W(section("Item Updates"))
    W(item_header("Orb of Venom"))
    W(ul_open())
    W(li("Poison Attack no longer has True Strike on the attack", t("DEL")))
    W(ul_close())
    W(item_header("Blade Mail"))
    W(ul_open())
    W(li("Armor bonus decreased from +7 to +6", b(7, 6)))
    W(ul_close())
    W(item_header("Hurricane Pike"))
    W(ul_open())
    W(li("Hurricane Thrust buff provided to the wearer when targeting an enemy is now dispellable", t("NEW")))
    W(ul_close())
    W(item_header("Harpoon"))
    W(ul_open())
    W(li("Draw Forth initial projectile is now disjointable", t("NEW")))
    W(ul_close())
    W(item_header("Phylactery"))
    W(ul_open())
    W(li("Recipe cost decreased from 400 to 300. Total cost decreased from 2600 to 2500", b(400, 300, l=True)))
    W(ul_close())
    W(item_header("Khanda"))
    W(ul_open())
    W(li("Total cost decreased from 5700 to 5600 (due to Phylactery Recipe cost reduction)", b(5700, 5600, l=True)))
    W(li("Empower Spell Break debuff no longer dispellable", t("NEW"), extra=inline_note("Slow debuff applied by Empower Spell is still dispellable")))
    W(ul_close())

    # ===== NEUTRAL ITEM UPDATES =====
    W(section("Neutral Item Updates"))

    W(plain_header("Artifact changes", dynamics=False, sublabel=True))
    W(item_header("Ripper's Lash"))
    W(ul_open())
    W(li("Flay cast range increased from 700 to 850", b(700, 850)))
    W(ul_close())
    W(item_header("Mana Draught"))
    W(ul_open())
    W(li_formula(
        "Bottoms Up mana restore rescaled",
        "60 + 4% max mana", "70 + 3% max mana",
        old_fn=lambda m: 60 + 0.04 * m,
        new_fn=lambda m: 70 + 0.03 * m,
        levels=[300, 500, 750, 1000, 1500, 2000],
        label="Max Mana",
        headline_level=750,
        force_rework=True,
        inline_note_text="Dormant Curio Max Mana Restoration decreased from 5.2% to 3.9% — " + b(5.2, 3.9),
    ))
    W(ul_close())
    W(item_header("Searing Signet"))
    W(ul_open())
    W(li("Burn Through no longer applies if the wearer is more than 2000 range away from the target", t("DEL")))
    W(ul_close())
    W(item_header("Serrated Shiv"))
    W(ul_open())
    W(li("Gut 'Em no longer grants Illusions the chance to True Strike", t("DEL")))
    W(ul_close())
    W(item_header("Giant's Maul"))
    W(ul_open())
    W(li("Crushing Blow can no longer be applied by illusions", t("DEL")))
    W(ul_close())

    W(plain_header("Enchantment changes", dynamics=False, sublabel=True))
    W(enchant_header("Vampiric"))
    W(ul_open())
    W(li("Spell Lifesteal bonus decreased from 8/10/12% to 6/8/10%", b([8, 10, 12], [6, 8, 10])))
    W(ul_close())

    # ===== HERO UPDATES =====
    W(section("Hero Updates"))

    # Axe
    W(hero_header("Axe"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Movement Speed per active Battle Hunger decreased from +10% to +8%", b(10, 8)))
    W(li("Level 25 Talent Berserker's Call AoE decreased from +100 to +85", b(100, 85)))
    W(ul_close())

    # Batrider
    W(hero_header("Batrider"))
    W(ul_open())
    W(li("Base Health Regen decreased from 1.75 to 1.25", b(1.75, 1.25)))
    W(ul_close())
    W(ability("Sticky Napalm", slug="batrider_sticky_napalm"))
    W(ul_open())
    W(li("Aghanim's Shard Building Damage decreased from 35% to 25%", b(35, 25)))
    W(ul_close())

    # Beastmaster
    W(hero_header("Beastmaster"))
    W(ability("Primal Roar", slug="beastmaster_primal_roar"))
    W(ul_open())
    W(li("Movement speed bonus duration decreased from 3/3.5/4s to 2s", b([3, 3.5, 4], 2)))
    W(ul_close())

    # Bristleback
    W(hero_header("Bristleback"))
    W(facet_header("bristleback_snot_rocket"))
    W(ul_open())
    W(li("Viscous Nasal Goo: Armor Loss per stack decreased from 2.5/3/3.5/4 to 2/2.5/3/3.5", b([2.5, 3, 3.5, 4], [2, 2.5, 3, 3.5])))
    W(ul_close())
    W(ul_open())
    W(li("Viscous Nasal Goo: Duration decreased from 6s to 5s", b(6, 5)))
    W(ul_close())

    # Chaos Knight
    W(hero_header("Chaos Knight"))
    W(ability("Chaos Bolt", slug="chaos_knight_chaos_bolt"))
    W(ul_open())
    W(li("Aghanim's Shard Illusion damage reduction decreased from 30% to 15%", b(30, 15)))
    W(ul_close())

    # Clinkz
    W(hero_header("Clinkz"))
    W(ability("Bone and Arrow", slug="clinkz_bone_and_arrow"))
    W(ul_open())
    W(li("Tower hits on archers now count as hero hits", t("REWORK")))
    W(ul_close())

    # Crystal Maiden
    W(hero_header("Crystal Maiden"))
    W(ability("Freezing Field", slug="crystal_maiden_freezing_field"))
    W(ul_open())
    W(li("Aghanim's Scepter time for Frostbite application decreased from 2.5s to 2s", b(2.5, 2)))
    W(ul_close())

    # Dark Seer
    W(hero_header("Dark Seer"))
    W(ability("Surge", slug="dark_seer_surge"))
    W(ul_open())
    W(li("Aghanim's Shard movement speed slow decreased from 50% to 35%", b(50, 35)))
    W(ul_close())
    W(ability("Wall of Replica", slug="dark_seer_wall_of_replica"))
    W(ul_open())
    W(li("Movement Slow decreased from 50/60/70% to 40%", b([50, 60, 70], 40)))
    W(ul_close())

    # Dark Willow
    W(hero_header("Dark Willow"))
    W(ability("Shadow Realm", slug="dark_willow_shadow_realm"))
    W(ul_open())
    W(li("Mana Cost increased from 70/80/90/100 to 80/90/100/110", b([70, 80, 90, 100], [80, 90, 100, 110], l=True)))
    W(ul_close())

    # Death Prophet
    W(hero_header("Death Prophet"))
    W(ul_open())
    W(li("Base Armor decreased by 1", bstat_h("Death Prophet", "ArmorPhysical", "7.39b", -1), extra=note_box(hero="Death Prophet", field="ArmorPhysical", before_patch="7.39b")))
    W(ul_close())
    W(ability("Exorcism", slug="death_prophet_exorcism"))
    W(ul_open())
    W(li("Aghanim's Scepter ghosts no longer slow enemies", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Attack Speed decreased from +40 to +30", b(40, 30)))
    W(ul_close())

    # Disruptor
    W(hero_header("Disruptor"))
    W(ability("Electromagnetic Repulsion", slug="disruptor_electromagnetic_repulsion"))
    W(ul_open())
    W(li("Cooldown increased from 4s to 5s", b(4, 5, l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Kinetic Field Duration decreased from +1.5s to +1s", b(1.5, 1)))
    W(ul_close())

    # Doom
    W(hero_header("Doom"))
    W(ul_open())
    W(li("Strength gain decreased from 3.8 to 3.5", b(3.8, 3.5)))
    W(ul_close())

    # Earth Spirit
    W(hero_header("Earth Spirit"))
    W(facet_header("earth_spirit_ready_to_roll"))
    W(ul_open())
    W(li("Rolling Boulder: Allied heroes that are affected by Enchant Remnant ability are now considered a hero instead of a Stone Remnant", t("MISC")))
    W(ul_close())
    W(ul_open())
    W(li("Rolling Boulder: Distance increased from 750 to 800", b(750, 800)))
    W(ul_close())

    # Enchantress
    W(hero_header("Enchantress"))
    W(ability("Untouchable", slug="enchantress_untouchable"))
    W(ul_open())
    W(li("Attack Slow increased from 100/150/200 to 110/160/210", b([100, 150, 200], [110, 160, 210])))
    W(ul_close())

    # Gyrocopter
    W(hero_header("Gyrocopter"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Health decreased from +175 to +150", b(175, 150)))
    W(li("Level 25 Talent Flak Cannon Cooldown Reduction decreased from 5s to 4s", b(5, 4)))
    W(ul_close())

    # Hoodwink
    W(hero_header("Hoodwink"))
    W(ul_open())
    W(li("Base Movement Speed increased from 310 to 315", b(310, 315)))
    W(ul_close())
    W(ability("Bushwhack", slug="hoodwink_bushwhack"))
    W(ul_open())
    W(li("Stun Duration increased from 1.4/1.6/1.8/2s to 1.5/1.7/1.9/2.1s", b([1.4, 1.6, 1.8, 2], [1.5, 1.7, 1.9, 2.1])))
    W(ul_close())

    # Kez
    W(hero_header("Kez"))
    W(ability("Echo Slash", slug="kez_echo_slash"))
    W(ul_open())
    W(li("Mana Cost decreased from 85/100/115/130 to 75/90/105/120", b([85, 100, 115, 130], [75, 90, 105, 120], l=True)))
    W(ul_close())
    W(ability("Kazurai Katana", slug="kez_kazurai_katana"))
    W(ul_open())
    W(li("Impale Duration decreased from 0.6s to 0.5s", b(0.6, 0.5)))
    W(li("Mana Cost decreased from 50 to 40", b(50, 40, l=True)))
    W(ul_close())

    # Kunkka
    W(hero_header("Kunkka"))
    W(ability("Tidal Wave", slug="kunkka_tidal_wave"))
    W(ul_open())
    W(li("Wave Distance decreased from 2300 to 1800", b(2300, 1800)))
    W(li("Cast Range decreased from 1400 to 1050", b(1400, 1050), extra=inline_note("As a result, wave's spawn distance behind Kunkka decreased from 900 to 750 — " + b(900, 750))))
    W(ul_close())

    # Lich
    W(hero_header("Lich"))
    W(facet_header("lich_cryophobia"))
    W(ul_open())
    W(li("Sinister Gaze: Bonus Damage increased from 10/15/20/25 to 15/20/25/30", b([10, 15, 20, 25], [15, 20, 25, 30])))
    W(ul_close())

    # Lone Druid
    W(hero_header("Lone Druid"))
    W(ability("Summon Spirit Bear", slug="lone_druid_spirit_bear"))
    W(ul_open())
    W(li("Spirit Bear health per Lone Druid's level increased from 90 to 100", b(90, 100)))
    W(ul_close())

    # Monkey King
    W(hero_header("Monkey King"))
    W(ability("Mischief", slug="monkey_king_mischief"))
    W(ul_open())
    W(li("Bonus Move Speed rescaled from 6/9/12/15% to 8%", b([6, 9, 12, 15], 8)))
    W(ul_close())

    # Muerta
    W(hero_header("Muerta"))
    W(ul_open())
    W(li("Base Agility increased from 20 to 21", b(20, 21)))
    W(ul_close())

    # Naga Siren
    W(hero_header("Naga Siren"))
    W(ul_open())
    W(li("Base Intelligence decreased from 21 to 20", b(21, 20)))
    W(ul_close())

    # Nature's Prophet
    W(hero_header("Nature's Prophet"))
    W(facet_header("furion_soothing_saplings"))
    W(ul_open())
    W(li("Level 15 Talent Sprout Heal Per Second decreased from +30% to +20%", b(30, 20)))
    W(ul_close())
    W(ul_open())
    W(li("Curse of the Oldgrowth: DPS per Tree decreased from 20 to 15", b(20, 15)))
    W(ul_close())

    # Nyx Assassin
    W(hero_header("Nyx Assassin"))
    W(ability("Spiked Carapace", slug="nyx_assassin_spiked_carapace"))
    W(ul_open())
    W(li("Damage Reflected increased from 125% to 140%", b(125, 140)))
    W(ul_close())

    # Pangolier
    W(hero_header("Pangolier"))
    W(ul_open())
    W(li("Base Damage decreased by 2", bstat_h("Pangolier", "AttackDamageMin", "7.39b", -2), extra=note_box(hero="Pangolier", field="AttackDamageMin", before_patch="7.39b")))
    W(li("Damage at level 1 decreased from 51-57 to 49-55", br(51, 57, 49, 55)))
    W(ul_close())

    # Phantom Assassin
    W(hero_header("Phantom Assassin"))
    W(ability("Blur", slug="phantom_assassin_blur"))
    W(ul_open())
    W(li("Cooldown rescaled from 60/55/50/45s to 50s", b([60, 55, 50, 45], 50, l=True)))
    W(ul_close())
    W(ability("Fan of Knives", slug="phantom_assassin_fan_of_knives"))
    W(ul_open())
    W(li("Break debuff is no longer dispellable", t("NEW")))
    W(ul_close())

    # Phantom Lancer
    W(hero_header("Phantom Lancer"))
    W(ability("Phantom Rush", slug="phantom_lancer_phantom_edge"))
    W(ul_open())
    W(li("Aghanim's Scepter now additionally every 600 units rushed creates a Juxtapose illusion that rushes to the target alongside Phantom Lancer", t("NEW")))
    W(li("Aghanim's Scepter collision radius for Phantom Lancer increased from 75 to 125", b(75, 125)))
    W(ul_close())

    # Primal Beast
    W(hero_header("Primal Beast"))
    W(facet_header("primal_beast_provoke_the_beast"))
    W(ul_open())
    W(li("Uproar: Now also provides stacks upon being leashed", t("NEW")))
    W(ul_close())
    W(ul_open())
    W(li("Rock Throw: Cooldown decreased from 25s to 20s", b(25, 20, l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Damage increased from +20 to +30", b(20, 30)))
    W(ul_close())

    # Puck
    W(hero_header("Puck"))
    W(ability("Waning Rift", slug="puck_waning_rift"))
    W(ul_open())
    W(li("Max Distance decreased from 400 to 350", b(400, 350)))
    W(ul_close())
    W(ability("Phase Shift", slug="puck_phase_shift"))
    W(ul_open())
    W(li("Aghanim's Shard Bonus Damage decreased from 35 to 20", b(35, 20)))
    W(ul_close())

    # Pugna
    W(hero_header("Pugna"))
    W(ability("Nether Ward", slug="pugna_nether_ward"))
    W(ul_open())
    W(li("Ward Duration increased from 18/22/26/30s to 21/24/27/30s", b([18, 22, 26, 30], [21, 24, 27, 30])))
    W(ul_close())

    # Sand King
    W(hero_header("Sand King"))
    W(ability("Burrowstrike", slug="sandking_burrowstrike"))
    W(ul_open())
    W(li("Damage increased from 80/140/200/260 to 80/150/220/290", b([80, 140, 200, 260], [80, 150, 220, 290])))
    W(ul_close())
    W(ability("Epicenter", slug="sandking_epicenter"))
    W(ul_open())
    W(li("Aghanim's Shard pulse interval decreased from 3.5s to 3s", b(3.5, 3)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Sand Storm Slow increased from 45% to 50%", b(45, 50)))
    W(ul_close())

    # Shadow Shaman
    W(hero_header("Shadow Shaman"))
    W(ul_open())
    W(li("Base Armor decreased by 1", bstat_h("Shadow Shaman", "ArmorPhysical", "7.39b", -1), extra=note_box(hero="Shadow Shaman", field="ArmorPhysical", before_patch="7.39b")))
    W(li("Base Intelligence decreased from 25 to 23", b(25, 23)))
    W(ul_close())

    # Snapfire
    W(hero_header("Snapfire"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Mortimer Kisses Burn DPS increased from +25 to +35", b(25, 35)))
    W(ul_close())

    # Spectre
    W(hero_header("Spectre"))
    W(ability("Reality", slug="spectre_reality"))
    W(ul_open())
    W(li("Mana Cost increased from 0 to 40", b(0, 40, l=True)))
    W(ul_close())

    # Sven
    W(hero_header("Sven"))
    W(ability("God's Strength", slug="sven_gods_strength"))
    W(ul_open())
    W(li("Duration decreased from 35s to 30s", b(35, 30)))
    W(ul_close())

    # Techies
    W(hero_header("Techies"))
    W(ability("Reactive Tazer", slug="techies_reactive_tazer"))
    W(ul_open())
    W(li("Explosion Radius increased from 400 to 450", b(400, 450)))
    W(ul_close())

    # Templar Assassin
    W(hero_header("Templar Assassin"))
    W(ul_open())
    W(li("Base Strength decreased from 23 to 21", b(23, 21)))
    W(ul_close())
    W(ability("Psionic Trap", slug="templar_assassin_psionic_trap"))
    W(ul_open())
    W(li("Trap vision radius decreased from 400 to 250", b(400, 250), extra=inline_note("Effect radius unchanged and still 400")))
    W(ul_close())

    # Terrorblade
    W(hero_header("Terrorblade"))
    W(ul_open())
    W(li("Base Damage decreased by 2", bstat_h("Terrorblade", "AttackDamageMin", "7.39b", -2), extra=note_box(hero="Terrorblade", field="AttackDamageMin", before_patch="7.39b")))
    W(li("Damage at level 1 decreased from 50-56 to 48-54", br(50, 56, 48, 54)))
    W(ul_close())

    # Tiny
    W(hero_header("Tiny"))
    W(ability("Toss", slug="tiny_toss"))
    W(ul_open())
    W(li("Flight duration decreased from 1.4s to 1.25s", b(1.4, 1.25)))
    W(ul_close())

    # Tusk
    W(hero_header("Tusk"))
    W(ul_open())
    W(li("Agility gain decreased from 2.1 to 1.9", b(2.1, 1.9)))
    W(ul_close())

    # Underlord
    W(hero_header("Underlord"))
    W(ability("Invading Force", slug="abyssal_underlord_raid_boss"))
    W(ul_open())
    W(li("Movement speed bonus increased from 5/10/15/20% to 11/14/17/20%", b([5, 10, 15, 20], [11, 14, 17, 20])))
    W(ul_close())

    # Undying
    W(hero_header("Undying"))
    W(ability("Flesh Golem", slug="undying_flesh_golem"))
    W(ul_open())
    W(li("Bonus Movespeed decreased from 20/30/40 to 20", b([20, 30, 40], 20)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Tombstone on Death replaced with +4 Tombstone Attacks to Destroy", t("REWORK")))
    W(li("Level 25 Talent +6 Tombstone Attacks to Destroy replaced with Tombstone on Death", t("REWORK")))
    W(ul_close())

    # Vengeful Spirit
    W(hero_header("Vengeful Spirit"))
    W(ul_open())
    W(li("Base Attack Speed decreased from 110 to 100", b(110, 100)))
    W(ul_close())
    W(ability("Vengeance Aura", slug="vengefulspirit_command_aura"))
    W(ul_open())
    W(li("Aghanim's Scepter illusion damage taken increased from 100% to 115%", b(100, 115, l=True)))
    W(ul_close())

    # Visage
    W(hero_header("Visage"))
    W(ability("Summon Familiars", slug="visage_summon_familiars"))
    W(ul_open())
    W(li("Familiar Armor increased from 0/2/4 to 2/3/4", b([0, 2, 4], [2, 3, 4])))
    W(ul_close())

    # Windranger
    W(hero_header("Windranger"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +25 Easy Breezy Min/Max Movespeed replaced with +4 All Attributes", t("REWORK")))
    W(ul_close())

    # Winter Wyvern
    W(hero_header("Winter Wyvern"))
    W(ul_open())
    W(li("Base Damage increased by 1", bstat_h("Winter Wyvern", "AttackDamageMin", "7.39b", 1), extra=note_box(hero="Winter Wyvern", field="AttackDamageMin", before_patch="7.39b")))
    W(li("Damage at level 1 increased from 40-47 to 41-48", br(40, 47, 41, 48)))
    W(ul_close())

    # Wraith King
    W(hero_header("Wraith King"))
    W(facet_header("skeleton_king_facet_bone_guard"))
    W(ul_open())
    W(li("Skeleton Armor decreased from 3 to 2", b(3, 2)))
    W(ul_close())
    W(ul_open())
    W(li("Reincarnation: Slow Radius decreased from 900 to 600", b(900, 600), extra=inline_note("Also affects Wraithfire Blast cast range from level 25 talent")))
    W(ul_close())

    # Zeus
    W(hero_header("Zeus"))
    W(ul_open())
    W(li("Base intelligence increased from 22 to 23", b(22, 23)))
    W(ul_close())

    write_footer()
    save_html('patches/7.39c.html')
