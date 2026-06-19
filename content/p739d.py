from patch.api import *

def build():
    write_head("7.39d", "05.08.2025")

    # ===== GENERAL UPDATES =====
    W(section("General Updates"))

    W(plain_header("Terrain Changes", terrain_link="7.39d"))
    W(ul_open())
    W(li("Increased spawnboxes of Triangle Ancient camps", t("BUFF")))
    W(li("Fixed a ward spot in Radiant safe lane hard camp", t("MISC")))
    W(li("Removed several trees from the inside corner of the Dire Safelane small camp", t("DEL")))
    W(ul_close())

    # ===== ITEM UPDATES =====
    W(section("Item Updates"))

    W(item_header("Blade Mail"))
    W(ul_open())
    W(li("Damage bonus decreased from +18 to +15", b(18, 15)))
    W(li_formula(
        "Damage Return passive attack damage returned decreased",
        "20 + 20% attack damage", "10 + 15% attack damage",
        old_fn=lambda d: 20 + 0.20 * d,
        new_fn=lambda d: 10 + 0.15 * d,
        levels=[50, 100, 150, 200, 300, 400],
        label="Attack Damage",
        headline_level=200,
    ))
    W(ul_close())

    W(item_header("Dragon Lance"))
    W(ul_open())
    W(li("Attack Range bonus decreased from +150 to +140", b(150, 140)))
    W(ul_close())

    W(item_header("Hurricane Pike"))
    W(ul_open())
    W(li("Attack Range bonus decreased from +150 to +140", b(150, 140)))
    W(ul_close())

    W(item_header("Glimmer Cape"))
    W(ul_open())
    W(li("Glimmer cooldown increased from 14s to 15s", b(14, 15, l=True)))
    W(ul_close())

    W(item_header("Heaven's Halberd"))
    W(ul_open())
    W(li("Disarm duration increased from 3s to 3.5s on melee targets and from 4s to 4.5s on ranged targets", b(3, 3.5)))
    W(ul_close())

    W(item_header("Maelstrom"))
    W(ul_open())
    W(li("Chain Lightning no longer deals bonus damage to illusions", t("DEL")))
    W(ul_close())

    W(item_header("Mjollnir"))
    W(ul_open())
    W(li("Fixed item description stating that Chain Lightning deals bonus damage to illusions", t("QoL")))
    W(ul_close())

    W(item_header("Mask of Madness"))
    W(ul_open())
    W(li("Berserk bonus attack speed decreased from 110 to 100", b(110, 100)))
    W(ul_close())

    W(item_header("Octarine Core"))
    W(ul_open())
    W(li("Health bonus decreased from +500 to +450", b(500, 450)))
    W(li("Mana bonus decreased from +500 to +450", b(500, 450)))
    W(ul_close())

    W(item_header("Pavise"))
    W(ul_open())
    W(li("Protect mana cost decreased from 100 to 60", b(100, 60, l=True)))
    W(ul_close())

    W(item_header("Phylactery"))
    W(ul_open())
    W(li("Empower Spell cooldown decreased from 10s to 9s", b(10, 9, l=True)))
    W(ul_close())

    W(item_header("Khanda"))
    W(ul_open())
    W(li("Empower Spell cooldown decreased from 10s to 9s", b(10, 9, l=True)))
    W(ul_close())

    W(item_header("Witch Blade"))
    W(ul_open())
    W(li("Armor bonus decreased from +6 to +5", b(6, 5)))
    W(ul_close())

    W(item_header("Parasma"))
    W(ul_open())
    W(li("Armor bonus decreased from +8 to +7", b(8, 7)))
    W(ul_close())

    # ===== NEUTRAL ITEM UPDATES =====
    W(section("Neutral Item Updates"))

    W(plain_header("Artifact changes", dynamics=False, sublabel=True))

    W(item_header("Sister's Shroud"))
    W(ul_open())
    W(li("Veiled starting evasion decreased from 200% to 150%", b(200, 150)))
    W(li("Veiled duration decreased from 8s to 5s", b(8, 5)))
    W(ul_close())

    W(item_header("Gale Guard"))
    W(ul_open())
    W(li("Cyclonic Shield barrier amount decreased from 250 to 225", b(250, 225)))
    W(ul_close())

    W(item_header("Helm of the Undying"))
    W(ul_open())
    W(li("Death Delay base duration increased from 5s to 6s", b(5, 6)))
    W(li("Units can no longer attack buildings while under the effect of Death Delay", t("DEL")))
    W(ul_close())

    W(item_header("Psychic Headband"))
    W(ul_open())
    W(li("Psychic Push cooldown decreased from 20s to 15s", b(20, 15, l=True)))
    W(ul_close())

    W(item_header("Magnifying Monocle"))
    W(ul_open())
    W(li("Keen Eye disable duration on taking damage increased from 3s to 6s", b(3, 6)))
    W(ul_close())

    W(item_header("Outworld Staff"))
    W(ul_open())
    W(li("Self-Exile mana cost increased from 40 to 65", b(40, 65, l=True)))
    W(ul_close())

    W(plain_header("Enchantment Changes", dynamics=False, sublabel=True))

    W(enchant_header("Brawny"))
    W(ul_open())
    W(li("Health Regen bonus decreased from +0/4/8/12 to +0/3/6/9", b([0, 4, 8, 12], [0, 3, 6, 9])))
    W(ul_close())

    W(enchant_header("Mystical"))
    W(ul_open())
    W(li("Mana Regen bonus decreased from +1/1.75/2.5/3.25 to +0.8/1.6/2.4/3.2", b([1, 1.75, 2.5, 3.25], [0.8, 1.6, 2.4, 3.2])))
    W(ul_close())

    # ===== HERO UPDATES =====
    W(section("Hero Updates"))

    # Abaddon
    W(hero_header("Abaddon"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Aphotic Shield provides HP Regen decreased from +12 to +10", b(12, 10)))
    W(ul_close())

    # Axe
    W(hero_header("Axe"))
    W(ability("Berserker's Call", slug="axe_berserkers_call"))
    W(ul_open())
    W(li("Mana Cost increased from 80/90/100/110 to 90/100/110/120", b([80, 90, 100, 110], [90, 100, 110, 120], l=True)))
    W(ul_close())
    W(ability("Culling Blade", slug="axe_culling_blade"))
    W(ul_open())
    W(li("Kill Armor Bonus decreased from 20/25/30 to 10/15/20", b([20, 25, 30], [10, 15, 20])))
    W(ul_close())

    # Batrider
    W(hero_header("Batrider"))
    W(ul_open())
    W(li("Base Agility decreased from 15 to 13", bstat_h("Batrider", "AttributeBaseAgility", "7.39c", -2)))
    W(li("Damage at level 1 decreased from 39–43 to 38–42", br(39, 43, 38, 42)))
    W(ul_close())
    W(ability("Flamebreak", slug="batrider_flamebreak"))
    W(ul_open())
    W(li("Radius decreased from 450 to 400", b(450, 400)))
    W(ul_close())

    # Bloodseeker
    W(hero_header("Bloodseeker"))
    W(ability("Sanguivore", slug="bloodseeker_sanguivore"))
    W(ul_open())
    W(li("Aghanim's Scepter heal on Pure damage dealt increased from 30% to 35%", b(30, 35)))
    W(ul_close())
    W(ability("Blood Rite", slug="bloodseeker_blood_bath"))
    W(ul_open())
    W(li("Damage increased from 90/145/200/255 to 100/155/210/265", b([90, 145, 200, 255], [100, 155, 210, 265])))
    W(ul_close())

    # Bounty Hunter
    W(hero_header("Bounty Hunter"))
    W(ability("Track", slug="bounty_hunter_track"))
    W(ul_open())
    W(li("Allies Bonus Gold increased from 40/80/120 to 50/90/130", b([40, 80, 120], [50, 90, 130])))
    W(ul_close())

    # Crystal Maiden
    W(hero_header("Crystal Maiden"))
    W(ability("Freezing Field", slug="crystal_maiden_freezing_field"))
    W(ul_open())
    W(li("Damage increased from 105/170/250 to 110/180/250", b([105, 170, 250], [110, 180, 250])))
    W(ul_close())

    # Dark Willow
    W(hero_header("Dark Willow"))
    W(ability("Shadow Realm", slug="dark_willow_shadow_realm"))
    W(ul_open())
    W(li("Allies can no longer target Dark Willow while active (Dark Willow can still target herself)", t("MISC")))
    W(ul_close())

    # Dawnbreaker
    W(hero_header("Dawnbreaker"))
    W(facet_header("dawnbreaker_solar_charged"))
    W(ul_open())
    W(li("Luminosity: Cooldown Reduction decreased from 1s to 0.8s", b(1, 0.8)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Solar Guardian Cooldown Reduction decreased from 20s to 15s", b(20, 15)))
    W(ul_close())

    # Dazzle
    W(hero_header("Dazzle"))
    W(ability("Weave", slug="dazzle_innate_weave"))
    W(ul_open())
    W(li("Duration decreased from 10s to 8s", b(10, 8)))
    W(ul_close())
    W(ability("Shadow Wave", slug="dazzle_shadow_wave"))
    W(ul_open())
    W(li("Mana Cost increased from 75 to 90", b(75, 90, l=True)))
    W(ul_close())

    # Doom
    W(hero_header("Doom"))
    W(ability("Devour", slug="doom_bringer_devour"))
    W(ul_open())
    W(li("Bonus Gold decreased from 40/80/120/160 to 35/70/105/140", b([40, 80, 120, 160], [35, 70, 105, 140])))
    W(ul_close())

    # Earth Spirit
    W(hero_header("Earth Spirit"))
    W(ul_open())
    W(li("Min base damage increased by 6", bstat_h("Earth Spirit", "AttackDamageMin", "7.39c", 6), extra=note_box(hero="Earth Spirit", field="AttackDamageMin", before_patch="7.39c")))
    W(ul_close())

    # Ember Spirit
    W(hero_header("Ember Spirit"))
    W(ability("Searing Chains", slug="ember_spirit_searing_chains"))
    W(ul_open())
    W(li("Mana Cost increased from 95/100/105/110 to 95/105/115/125", b([95, 100, 105, 110], [95, 105, 115, 125], l=True)))
    W(ul_close())

    # Enchantress
    W(hero_header("Enchantress"))
    W(ability("Enchant", slug="enchantress_enchant"))
    W(ul_open())
    W(li("Experience bounty on creep cast increased from 35% to 40%", b(35, 40)))
    W(ul_close())

    # Faceless Void
    W(hero_header("Faceless Void"))
    W(facet_header("faceless_void_chronosphere"))
    W(ul_open())
    W(li("Cooldown decreased from 160/150/140s to 155/145/135s", b([160, 150, 140], [155, 145, 135], l=True)))
    W(ul_close())
    W(facet_header("faceless_void_time_zone"))
    W(ul_open())
    W(li("Cooldown decreased from 130/125/120s to 125/120/115s", b([130, 125, 120], [125, 120, 115], l=True)))
    W(ul_close())
    W(ul_open())
    W(li("Time Lock: Bonus Damage increased from 12/18/24/30 to 18/22/26/30", b([12, 18, 24, 30], [18, 22, 26, 30])))
    W(ul_close())

    # Grimstroke
    W(hero_header("Grimstroke"))
    W(ability("Phantom's Embrace", slug="grimstroke_ink_creature"))
    W(ul_open())
    W(li("Cooldown decreased from 36/30/24/18s to 30/26/22/18s", b([36, 30, 24, 18], [30, 26, 22, 18], l=True)))
    W(ul_close())
    W(ability("Ink Swell", slug="grimstroke_spirit_walk"))
    W(ul_open())
    W(li("Max Stun Duration increased from 1.3/1.8/2.3/2.8s to 1.6/2/2.4/2.8s", b([1.3, 1.8, 2.3, 2.8], [1.6, 2, 2.4, 2.8])))
    W(ul_close())

    # Io
    W(hero_header("Io"))
    W(ability("Spirits", slug="wisp_spirits"))
    W(ul_open())
    W(li("Cooldown decreased from 26/24/22/20s to 22/21/20/19s", b([26, 24, 22, 20], [22, 21, 20, 19], l=True)))
    W(ul_close())

    # Kunkka
    W(hero_header("Kunkka"))
    W(ability("Tidebringer", slug="kunkka_tidebringer"))
    W(ul_open())
    W(li("Cleave Range decreased from 650/800/950/1100 to 650/775/900/1025", b([650, 800, 950, 1100], [650, 775, 900, 1025])))
    W(ul_close())

    # Luna
    W(hero_header("Luna"))
    W(ability("Eclipse", slug="luna_eclipse"))
    W(ul_open())
    W(li("Cooldown decreased from 110s to 105s", b(110, 105, l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Lucent Beam Ministun increased from +0.4s to +0.5s", b(0.4, 0.5)))
    W(ul_close())

    # Mirana
    W(hero_header("Mirana"))
    W(ability("Sacred Arrow", slug="mirana_arrow"))
    W(ul_open())
    W(li("Maximum Bonus Damage increased from 150/160/170/180 to 180", b([150, 160, 170, 180], 180)))
    W(ul_close())

    # Monkey King
    W(hero_header("Monkey King"))
    W(facet_header("monkey_king_transfiguration"))
    W(ul_open())
    W(li("Initial cooldown increased from 0.5s to 1s", b(0.5, 1, l=True)))
    W(ul_close())
    W(ul_open())
    W(li("Boundless Strike: Aghanim's Shard portion of Primal Spring's max power decreased from 60% to 40%", b(60, 40)))
    W(ul_close())

    # Naga Siren
    W(hero_header("Naga Siren"))
    W(facet_header("naga_siren_active_riptide"))
    W(ul_open())
    W(li("Rip Tide: Duration decreased from 3.5s to 2.6/2.9/3.2/3.5s", b(3.5, [2.6, 2.9, 3.2, 3.5])))
    W(ul_close())
    W(ul_open())
    W(li("Song of the Siren: Radius decreased from 1000/1200/1400 to 900/1150/1400", b([1000, 1200, 1400], [900, 1150, 1400])))
    W(ul_close())

    # Nature's Prophet
    W(hero_header("Nature's Prophet"))
    W(ul_open())
    W(li("Agility gain decreased from 3.2 to 3.0", bstat_h("Nature's Prophet", "AttributeAgilityGain", "7.39c", -0.2)))
    W(ul_close())
    W(facet_header("furion_soothing_saplings"))
    W(ul_open())
    W(li("Sprout: Heal per second decreased from 14/26/38/50 to 10/15/20/25", b([14, 26, 38, 50], [10, 15, 20, 25])))
    W(ul_close())
    W(ul_open())
    W(li("Sprout: Damage decreased from 70/135/200/265 to 70/130/190/250", b([70, 135, 200, 265], [70, 130, 190, 250])))
    W(ul_close())

    # Necrophos
    W(hero_header("Necrophos"))
    W(ability("Sadist", slug="necrolyte_sadist"))
    W(ul_open())
    W(li("Health Regen per kill increased from 3/4.5/6/7.5 to 3.5/5/6.5/8", b([3, 4.5, 6, 7.5], [3.5, 5, 6.5, 8])))
    W(ul_close())
    W(ability("Ghost Shroud", slug="necrolyte_ghost_shroud"))
    W(ul_open())
    W(li("Slow Radius decreased from 750 to 700", b(750, 700)))
    W(ul_close())

    # Nyx Assassin
    W(hero_header("Nyx Assassin"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Impale Damage increased from +100 to +140", b(100, 140)))
    W(li("Level 20 Talent Spiked Carapace Stun Duration increased from +0.5s to +0.6s", b(0.5, 0.6)))
    W(ul_close())

    # Pangolier
    W(hero_header("Pangolier"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Lucky Shot Armor Reduction decreased from +4 to +3", b(4, 3)))
    W(ul_close())

    # Phantom Assassin
    W(hero_header("Phantom Assassin"))
    W(ability("Blur", slug="phantom_assassin_blur"))
    W(ul_open())
    W(li("Cooldown decreased from 50s to 45s", b(50, 45, l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Immaterial Evasion increased from +15% to +20%", b(15, 20)))
    W(ul_close())

    # Primal Beast
    W(hero_header("Primal Beast"))
    W(ability("Pulverize", slug="primal_beast_pulverize"))
    W(ul_open())
    W(li("Cooldown decreased from 40/36/32s to 40/35/30s", b([40, 36, 32], [40, 35, 30], l=True)))
    W(ul_close())

    # Puck
    W(hero_header("Puck"))
    W(ul_open())
    W(li("Agility gain decreased from 2.5 to 2.3", bstat_h("Puck", "AttributeAgilityGain", "7.39c", -0.2)))
    W(ul_close())

    # Queen of Pain
    W(hero_header("Queen of Pain"))
    W(ability("Succubus", slug="queenofpain_succubus"))
    W(ul_open())
    W(li("Range for Max Lifesteal decreased from 300 to 150", b(300, 150)))
    W(ul_close())

    # Sand King
    W(hero_header("Sand King"))
    W(ul_open())
    W(li("Base Strength increased from 22 to 23", b(22, 23)))
    W(ul_close())
    W(ability("Sand Storm", slug="sandking_sand_storm"))
    W(ul_open())
    W(li("Radius increased from 425/500/575/650 to 475/550/625/700", b([425, 500, 575, 650], [475, 550, 625, 700])))
    W(ul_close())

    # Shadow Demon
    W(hero_header("Shadow Demon"))
    W(ability("Disruption", slug="shadow_demon_disruption"))
    W(ul_open())
    W(li("Cast Range increased from 650 to 675", b(650, 675)))
    W(ul_close())

    # Shadow Fiend
    W(hero_header("Shadow Fiend"))
    W(ul_open())
    W(li("Base Armor decreased by 1", bstat_h("Shadow Fiend", "ArmorPhysical", "7.39c", -1), extra=note_box(hero="Shadow Fiend", field="ArmorPhysical", before_patch="7.39c")))
    W(ul_close())
    W(ability("Presence of the Dark Lord", slug="nevermore_dark_lord"))
    W(ul_open())
    W(li("Armor Reduction decreased from 4/5/6/7 to 3/4/5/6", b([4, 5, 6, 7], [3, 4, 5, 6])))
    W(ul_close())

    # Shadow Shaman
    W(hero_header("Shadow Shaman"))
    W(ability("Mass Serpent Ward", slug="shadow_shaman_mass_serpent_ward"))
    W(ul_open())
    W(li("Wards' base attack time increased from 1.5s to 1.6s", b(1.5, 1.6, l=True)))
    W(li("Wards no longer deal 50% extra damage against Roshan", t("DEL")))
    W(ul_close())

    # Silencer
    W(hero_header("Silencer"))
    W(ul_open())
    W(li("Base Strength decreased from 19 to 18", b(19, 18)))
    W(ul_close())

    # Skywrath Mage
    W(hero_header("Skywrath Mage"))
    W(ability("Arcane Bolt", slug="skywrath_mage_arcane_bolt"))
    W(ul_open())
    W(li("Aghanim's Shard number of bolts increased from 2 to 3", b(2, 3)))
    W(ul_close())

    # Snapfire
    W(hero_header("Snapfire"))
    W(ability("Firesnap Cookie", slug="snapfire_firesnap_cookie"))
    W(ul_open())
    W(li("Cooldown decreased from 21/19/17/15s to 18/17/16/15s", b([21, 19, 17, 15], [18, 17, 16, 15], l=True)))
    W(ul_close())
    W(ability("Mortimer Kisses", slug="snapfire_mortimer_kisses"))
    W(ul_open())
    W(li("Firespit Pool Duration increased from 3 to 3.5s", b(3, 3.5)))
    W(ul_close())

    # Spirit Breaker
    W(hero_header("Spirit Breaker"))
    W(ul_open())
    W(li("Min base damage increased by 3", bstat_h("Spirit Breaker", "AttackDamageMin", "7.39c", 3), extra=note_box(hero="Spirit Breaker", field="AttackDamageMin", before_patch="7.39c")))
    W(ul_close())

    # Techies
    W(hero_header("Techies"))
    W(ul_open())
    W(li("Intelligence gain increased from 2.8 to 3.0", b(2.8, 3)))
    W(ul_close())

    # Templar Assassin
    W(hero_header("Templar Assassin"))
    W(ul_open())
    W(li("Base Damage decreased by 2–3", bstat_h("Templar Assassin", "AttackDamageMin", "7.39c", -2), extra=note_box(hero="Templar Assassin", field="AttackDamageMin", before_patch="7.39c")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Meld Bash duration decreased from 1s to 0.8s", b(1, 0.8)))
    W(ul_close())

    # Tinker
    W(hero_header("Tinker"))
    W(ability("Keen Conveyance", slug="tinker_keen_teleport"))
    W(ul_open())
    W(li("Cooldown decreased from 80s to 50s", b(80, 50, l=True)))
    W(ul_close())

    # Treant Protector
    W(hero_header("Treant Protector"))
    W(ability("Overgrowth", slug="treant_overgrowth"))
    W(ul_open())
    W(li("Damage per second increased from 85 to 95", b(85, 95)))
    W(ul_close())

    # Undying
    W(hero_header("Undying"))
    W(facet_header("undying_rotting_mitts"))
    W(ul_open())
    W(li("Flesh Golem: Zombies summoned by the facet effect now die when Undying dies", t("MISC")))
    W(ul_close())
    W(ul_open())
    W(li("Tombstone: Zombie vision range decreased from 900/900 to 800/800", b([900, 900], [800, 800])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Decay Damage decreased from +40 to +30", b(40, 30)))
    W(ul_close())

    # Ursa
    W(hero_header("Ursa"))
    W(ability("Maul", slug="ursa_maul"))
    W(ul_open())
    W(li("Health As Damage rescaled from 1.2/1.3/1.4/1.5% to 1.25%", b([1.2, 1.3, 1.4, 1.5], 1.25)))
    W(ul_close())
    W(ability("Earthshock", slug="ursa_earthshock"))
    W(ul_open())
    W(li("Aghanim's Shard Enrage duration decreased from 1.4s to 1.3s", b(1.4, 1.3)))
    W(ul_close())

    # Vengeful Spirit
    W(hero_header("Vengeful Spirit"))
    W(ul_open())
    W(li("Min base damage increased by 2", bstat_h("Vengeful Spirit", "AttackDamageMin", "7.39c", 2), extra=note_box(hero="Vengeful Spirit", field="AttackDamageMin", before_patch="7.39c")))
    W(li("Agility gain decreased from 3.2 to 3.0", bstat_h("Vengeful Spirit", "AttributeAgilityGain", "7.39c", -0.2)))
    W(ul_close())

    # Viper
    W(hero_header("Viper"))
    W(ability("Nethertoxin", slug="viper_nethertoxin"))
    W(ul_open())
    W(li("Min DPS increased from 15/20/25/30 to 15/25/35/45", b([15, 20, 25, 30], [15, 25, 35, 45])))
    W(ul_close())

    # Wraith King
    W(hero_header("Wraith King"))
    W(ability("Reincarnation", slug="skeleton_king_reincarnation"))
    W(ul_open())
    W(li("Slow Duration decreased from 5s to 4s", b(5, 4)))
    W(ul_close())

    # Zeus
    W(hero_header("Zeus"))
    W(ability("Heavenly Jump", slug="zuus_heavenly_jump"))
    W(ul_open())
    W(li("Leap Distance increased from 300/400/500/600 to 375/450/525/600", b([300, 400, 500, 600], [375, 450, 525, 600])))
    W(ul_close())

    write_footer()
    save_html('patches/7.39d.html')
