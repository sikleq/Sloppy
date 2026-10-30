from patch.api import *

def build():
    write_head("7.37b", "14.08.2024")

    # ===== ITEM UPDATES =====
    W(section("Item Updates"))
    W(item_header("Gleipnir"))
    W(ul_open())
    W(li("Eternal Chains radius decreased from 375 to 350", b(375, 350)))
    W(ul_close())
    W(item_header("Kaya"))
    W(ul_open())
    W(li("Mana Regen Amplification no longer stacks with other Kaya-based items", t("DEL")))
    W(li("Spell Lifesteal Amplification no longer stacks with other Kaya-based items", t("DEL")))
    W(ul_close())
    W(item_header("Yasha and Kaya"))
    W(ul_open())
    W(li("Mana Regen Amplification no longer stacks with other Kaya-based items", t("DEL")))
    W(li("Spell Lifesteal Amplification no longer stacks with other Kaya-based items", t("DEL")))
    W(ul_close())
    W(item_header("Kaya and Sange"))
    W(ul_open())
    W(li("Mana Regen Amplification no longer stacks with other Kaya-based items", t("DEL")))
    W(li("Spell Lifesteal Amplification no longer stacks with other Kaya-based items", t("DEL")))
    W(ul_close())
    W(item_header("Meteor Hammer"))
    W(ul_open())
    W(li("Mana Regen Amplification no longer stacks with other Kaya-based items", t("DEL")))
    W(li("Spell Lifesteal Amplification no longer stacks with other Kaya-based items", t("DEL")))
    W(ul_close())

    # ===== NEUTRAL ITEM UPDATES =====
    W(section("Neutral Item Updates"))
    W(item_header("Ironwood Tree"))
    W(ul_open())
    W(li("Plant Tree cast range decreased from 800 to 400", b(800, 400)))
    W(ul_close())

    # ===== HERO UPDATES =====
    W(section("Hero Updates"))

    # Abaddon
    W(hero_header("Abaddon"))
    W(ability("Mist Coil", slug="abaddon_death_coil"))
    W(ul_open())
    W(li("Mana Cost increased from 50 to 50/55/60/65", b(50, [50, 55, 60, 65], l=True)))
    W(ul_close())
    W(ability("Curse of Avernus", slug="abaddon_frostmourne"))
    W(ul_open())
    W(li("DPS increased from 10/20/30/40 to 15/25/35/45", b([10, 20, 30, 40], [15, 25, 35, 45])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Aphotic Shield HP Regeneration decreased from +15 to +12", b(15, 12)))
    W(li("Level 15 Talent Mist Coil Heal/Damage decreased from +40 to +35", b(40, 35)))
    W(li("Level 25 Talent Mist Coil AoE decreased from 400 to 350", b(400, 350)))
    W(ul_close())

    # Alchemist
    W(hero_header("Alchemist"))
    W(ability("Greevil's Greed", slug="alchemist_goblins_greed", innate=True))
    W(ul_open())
    W(li("Recent Kill Window increased from 36s to 40s", b(36, 40)))
    W(ul_close())
    W(ability("Berserk Potion", slug="alchemist_berserk_potion"))
    W(ul_open())
    W(li("Duration increased from 10s to 15s", b(10, 15)))
    W(ul_close())

    # Ancient Apparition
    W(hero_header("Ancient Apparition"))
    W(ability("Death Rime", slug="ancient_apparition_death_rime", innate=True))
    W(ul_open())
    W(li("Movement Slow per stack increased from 1.5% to 2.0%", b(1.5, 2)))
    W(ul_close())

    # Anti-Mage
    W(hero_header("Anti-Mage"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Mana Void Radius increased from +150 to +200", b(150, 200)))
    W(li("Level 15 Talent Persecutor Max Movement Slow increased from +10% to +15%", b(10, 15)))
    W(ul_close())

    # Arc Warden
    W(hero_header("Arc Warden"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Magnetic Field Attack Speed/Bonus Damage decreased from +20 to +16", b(20, 16)))
    W(li("Level 20 Talent Spark Wraith Damage increased from +35% to +40%", b(35, 40)))
    W(ul_close())

    # Axe
    W(hero_header("Axe"))
    W(ability("Counter Helix", slug="axe_counter_helix"))
    W(ul_open())
    W(li("Radius decreased from 300 to 275", b(300, 275)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +20 Counter Helix Damage replaced with +10 Berserker's Call Armor", t("SWAP")))
    W(li("Level 20 Talent +12 Berserker's Call Armor replaced with +25 Counter Helix Damage", t("SWAP")))
    W(ul_close())

    # Bane
    W(hero_header("Bane"))
    W(facet_header("bane_sleepwalk"))
    W(ul_open())
    W(li("Nightmare: Walk Speed increased from 75 to 85", b(75, 85)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Brain Sap Damage/Heal increased from +250 to +275", b(250, 275)))
    W(ul_close())

    # Batrider
    W(hero_header("Batrider"))
    W(ul_open())
    W(li("Base Strength decreased from 28 to 25", b(28, 25)))
    W(li("Strength gain increased from 2.2 to 2.6", b(2.2, 2.6)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Sticky Napalm Damage increased from +10 to +15", b(10, 15)))
    W(ul_close())

    # Beastmaster
    W(hero_header("Beastmaster"))
    W(facet_header("beastmaster_wild_hunt"))
    W(ul_open())
    W(li("Inner Beast: Bonus Attack Speed per unit increased from 2/3/4/5 to 3/4/5/6", b([2, 3, 4, 5], [3, 4, 5, 6])))
    W(ul_close())

    # Brewmaster
    W(hero_header("Brewmaster"))
    W(facet_header("brewmaster_drunken_master"))
    W(ul_open())
    W(li("Max self movement slow decreased from 20% to 15%", b(20, 15)))
    W(ul_close())

    # Centaur Warrunner
    W(hero_header("Centaur Warrunner"))
    W(ability("Horsepower", slug="centaur_horsepower", innate=True))
    W(ul_open())
    W(li("Strength as movement speed decreased from 35% to 30%", b(35, 30)))
    W(ul_close())

    # Clockwerk
    W(hero_header("Clockwerk"))
    W(facet_header("rattletrap_hookup"))
    W(ul_open())
    W(li("Hookshot: Now refunds Clockwerk 75% of the mana spent", t("NEW")))
    W(li("Hookshot: Now grants allies and Clockwerk 15/20/25 armor instead of a barrier", t("REWORK")))
    W(ul_close())

    # Dark Seer
    W(hero_header("Dark Seer"))
    W(ability("Normal Punch", slug="dark_seer_normal_punch"))
    W(ul_open())
    W(li("Max Damage decreased from 450 to 400", b(450, 400)))
    W(ul_close())

    # Dark Willow
    W(hero_header("Dark Willow"))
    W(facet_header("dark_willow_throwing_shade"))
    W(ul_open())
    W(li("Shadow Realm: Aura radius increased from 600 to 700", b(600, 700)))
    W(ul_close())

    # Death Prophet
    W(hero_header("Death Prophet"))
    W(facet_header("death_prophet_suppress"))
    W(ul_open())
    W(li("Silence: Movement Slow increased from 15/20/25/30% to 20/24/28/32%", b([15, 20, 25, 30], [20, 24, 28, 32])))
    W(ul_close())
    W(facet_header("death_prophet_ghosts"))
    W(ul_open())
    W(li("Exorcism: Hero Spirit Damage increased from 84-90/92-98/100-106 to 88-94/96-102/104-110", b([87, 95, 103], [91, 99, 107])))
    W(ul_close())

    # Elder Titan
    W(hero_header("Elder Titan"))
    W(ability("Momentum", slug="elder_titan_momentum"))
    W(ul_open())
    W(li("Attack Speed Penalty increased from 75 to 85", b(75, 85, l=True)))
    W(ul_close())

    # Ember Spirit
    W(hero_header("Ember Spirit"))
    W(ability("Immolation", slug="ember_spirit_immolation", innate=True))
    W(ul_open())
    W(li("Damage decreased from 10/20/30/40 to 10/18/26/34", b([10, 20, 30, 40], [10, 18, 26, 34])))
    W(li("Damage debuff no longer has a linger duration", t("DEL")))
    W(ul_close())
    W(ability("Sleight of Fist", slug="ember_spirit_sleight_of_fist"))
    W(ul_open())
    W(li("Cooldown increased from 12/10/8/6s to 13/11/9/7s", b([12, 10, 8, 6], [13, 11, 9, 7], l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Flame Guard Barrier Amount decreased from +200 to +165", b(200, 165)))
    W(li("Level 20 Talent Sleight of Fist Hero Damage decreased from +55 to +50", b(55, 50)))
    W(ul_close())

    # Enchantress
    W(hero_header("Enchantress"))
    W(facet_header("enchantress_spellbound"))
    W(ul_open())
    W(li("Enchant: Now also increases attack range for units under Enchantress' control against the target", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +45 Damage replaced with +30 Attack Speed for Enchantress and her units", t("SWAP")))
    W(li("Level 20 Talent +150 Health / +25 Damage for Enchanted Creeps replaced with +150 Health and 25 Damage for Enchantress and her units", t("SWAP")))
    W(ul_close())

    # Faceless Void
    W(hero_header("Faceless Void"))
    W(ability("Time Lock", slug="faceless_void_time_lock"))
    W(ul_open())
    W(li("Bonus Damage increased from 10/15/20/25 to 12/18/24/30", b([10, 15, 20, 25], [12, 18, 24, 30])))
    W(ul_close())

    # Hoodwink
    W(hero_header("Hoodwink"))
    W(facet_header("hoodwink_hunter"))
    W(ul_open())
    W(li("Scurry: Now increases duration to 3.5/4/4.5/5s", t("NEW")))
    W(ul_close())
    W(ability("Scurry", slug="hoodwink_scurry"))
    W(ul_open())
    W(li("Duration decreased from 3.5/4/4.5/5s to 2/2.5/3/3.5s", b([3.5, 4, 4.5, 5], [2, 2.5, 3, 3.5])))
    W(ul_close())

    # Huskar
    W(hero_header("Huskar"))
    W(facet_header("huskar_nothl_conflagration"))
    W(ul_open())
    W(li("Burning Spear: Duration is no longer reduced", t("BUFF"),
         extra=inline_note("With Incendiary the burn lasted 6s (10s with the Level 25 talent); now 9s (15s), as without the facet")))
    W(li("Burning Spear: Max Health Burn decreased from 1% to 0.75%", b(1, 0.75)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Burning Spear Duration increased from +4s to +6s", b(4, 6), facet="huskar_nothl_conflagration"))
    W(ul_close())

    # Invoker
    W(hero_header("Invoker"))
    W(facet_header("invoker_elitist"))
    W(ul_open())
    W(li("Exort: Spell Amplification per instance increased from 2/3/4/5/6/7/8% to 3/4/5/6/7/8/9%", b([2, 3, 4, 5, 6, 7, 8], [3, 4, 5, 6, 7, 8, 9])))
    W(ul_close())
    W(ability_group(("Quas", "invoker_quas"), ("Wex", "invoker_wex"), ("Exort", "invoker_exort"), ("Invoke", "invoker_invoke")))
    W(ul_open())
    W(li("Can now be cast during channeling and does not break invisibility", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +50 Forged Spirit Attack Speed replaced with +1 Forged Spirit", t("SWAP")))
    W(ul_close())

    # Jakiro
    W(hero_header("Jakiro"))
    W(facet_header("jakiro_ice"))
    W(ul_open())
    W(li("Liquid Frost: Bonus Damage decreased from 15/20/25/30 to 12/18/24/30", b([15, 20, 25, 30], [12, 18, 24, 30])))
    W(ul_close())

    # Juggernaut
    W(hero_header("Juggernaut"))
    W(ul_open())
    W(li("Base Damage increased by 2", bstat_h("Juggernaut", "AttackDamageMin", "7.37", 2), extra=note_box(hero="Juggernaut", field="AttackDamageMin", before_patch="7.37")))
    W(ul_close())

    # Legion Commander
    W(hero_header("Legion Commander"))
    W(facet_header("legion_commander_stonehall_plate"))
    W(ul_open())
    W(li("Overwhelming Odds: Barrier Duration decreased from 8s to 6s (same as Overwhelming Odds speed bonus duration)", b(8, 6)))
    W(ul_close())

    # Lina
    W(hero_header("Lina"))
    W(facet_header("lina_supercharge"))
    W(ul_open())
    W(li("Laguna Blade: Supercharge Stacks decreased from 12 to 10/11/12", b(12, [10, 11, 12])))
    W(ul_close())

    # Magnus
    W(hero_header("Magnus"))
    W(ul_open())
    W(li("Base Agility increased by 3", bstat_h("Magnus", "AttributeBaseAgility", "7.37", 3), extra=note_box(hero="Magnus", field="AttributeBaseAgility", before_patch="7.37")))
    W(ul_close())
    W(ability("Solid Core", slug="magnataur_solid_core", innate=True))
    W(ul_open())
    W(li("Now also provides 20/30/40/50% slow resistance, scales with Reverse Polarity", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent All Stats per hero hit with Reverse Polarity now stacks instead of refreshing", t("NEW")))
    W(li("Level 15 Talent All Stats per hero hit with Reverse Polarity duration increased from 15s to 20s", b(15, 20)))
    W(ul_close())

    # Mars
    W(hero_header("Mars"))
    W(facet_header("mars_victory_feast"))
    W(ul_open())
    W(li("Arena Of Blood: Buff duration increased from 15s to 20s", b(15, 20)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +30% Bulwark Active Redirect Chance replaced with +10/5% Bulwark Front/Side damage reduction", t("SWAP")))
    W(li("Level 20 Talent +14/+7% Bulwark Front/Side damage reduction replaced with -20s Arena of Blood Cooldown", t("SWAP")))
    W(ul_close())

    # Mirana
    W(hero_header("Mirana"))
    W(ul_open())
    W(li("Base Agility increased by 2", bstat_h("Mirana", "AttributeBaseAgility", "7.37", 2), extra=note_box(hero="Mirana", field="AttributeBaseAgility", before_patch="7.37")))
    W(ul_close())
    W(facet_header("mirana_sunlight"))
    W(ul_open())
    W(li("Time to max damage/attack speed decreased from 8s to 6s (total duration unchanged)", b(8, 6, l=True)))
    W(ul_close())
    W(ability("Starstorm", slug="mirana_starfall"))
    W(ul_open())
    W(li("Secondary strike damage increased from 75% to 80%", b(75, 80)))
    W(li("Secondary strike radius increased from 650 to 675 (same as base radius)", b(650, 675)))
    W(ul_close())
    W(ability("Sacred Arrow", slug="mirana_arrow"))
    W(ul_open())
    W(li("Aghanim's Scepter Primary Hit Starstorm Damage increased from 75% to 80%", b(75, 80)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Leap Distance increased from +125 to +150", b(125, 150)))
    W(ul_close())

    # Monkey King
    W(hero_header("Monkey King"))
    W(ability("Primal Spring", slug="monkey_king_primal_spring"))
    W(ul_open())
    W(li("Max Channel Time increased from 1.5s to 1.75s", b(1.5, 1.75, l=True)))
    W(ul_close())
    W(ability("Jingu Mastery", slug="monkey_king_jingu_mastery"))
    W(ul_open())
    W(li("Bonus Damage rescaled from 40/80/120/160 to 30/75/120/165", b([40, 80, 120, 160], [30, 75, 120, 165])))
    W(ul_close())

    # Muerta
    W(hero_header("Muerta"))
    W(ul_open())
    W(li("Base Armor increased by 1", bstat_h("Muerta", "ArmorPhysical", "7.37", 1), extra=note_box(hero="Muerta", field="ArmorPhysical", before_patch="7.37")))
    W(ul_close())
    W(facet_header("muerta_ofrenda"))
    W(ul_open())
    W(li("Effect Radius rescaled from 450 to 400/450/500/550", b(450, [400, 450, 500, 550])))
    W(ul_close())
    W(ability("The Calling", slug="muerta_the_calling"))
    W(ul_open())
    W(li("Mana Cost decreased from 145/160/175/190 to 140/155/170/185", b([145, 160, 175, 190], [140, 155, 170, 185], l=True)))
    W(ul_close())

    # Naga Siren
    W(hero_header("Naga Siren"))
    W(facet_header("naga_siren_active_riptide"))
    W(ul_open())
    W(li("Duration increased from 3s to 4s", b(3, 4)))
    W(ul_close())

    # Necrophos
    W(hero_header("Necrophos"))
    W(ul_open())
    W(li("Base Intelligence increased by 1", bstat_h("Necrophos", "AttributeBaseIntelligence", "7.37", 1), extra=note_box(hero="Necrophos", field="AttributeBaseIntelligence", before_patch="7.37")))
    W(ul_close())
    W(facet_header("necrolyte_rapid_decay"))
    W(ul_open())
    W(li("Ghost Shroud: Movement Speed Steal increased from 40% to 50%", b(40, 50)))
    W(ul_close())

    # Night Stalker
    W(hero_header("Night Stalker"))
    W(ability("Hunter in the Night", slug="night_stalker_hunter_in_the_night"))
    W(ul_open())
    W(li("Aghanim's Shard Cooldown increased from 30s to 35s", b(30, 35, l=True)))
    W(ul_close())

    # Nyx Assassin
    W(hero_header("Nyx Assassin"))
    W(ability("Impale", slug="nyx_assassin_impale"))
    W(ul_open())
    W(li("Cooldown rescaled from 17/16/15/14s to 18/16/14/12s", b([17, 16, 15, 14], [18, 16, 14, 12], l=True)))
    W(ul_close())

    # Omniknight
    W(hero_header("Omniknight"))
    W(facet_header("omniknight_dmgheals"))
    W(ul_open())
    W(li("Damage as Healing decreased from 30% to 25%", b(30, 25)))
    W(ul_close())

    # Oracle
    W(hero_header("Oracle"))
    W(ability("Rain of Destiny", slug="oracle_rain_of_destiny"))
    W(ul_open())
    W(li("Damage/Heal per second decreased from 40 to 35", b(40, 35)))
    W(ul_close())

    # Outworld Destroyer
    W(hero_header("Outworld Destroyer"))
    W(ability("Essence Flux", slug="obsidian_destroyer_equilibrium"))
    W(ul_open())
    W(li("Aghanim's Scepter damage barrier decreased from 70% to 65% of maximum mana", b(70, 65)))
    W(ul_close())

    # Phantom Lancer
    W(hero_header("Phantom Lancer"))
    W(ability("Illusory Armaments", slug="phantom_lancer_illusory_armaments", innate=True))
    W(ul_open())
    W(li("100% of bonus damage is converted to base damage for Phantom Lancer. Phantom Lancer illusions still convert 65% of the bonus damage", t("BUFF")))
    W(ul_close())
    W(ability("Juxtapose", slug="phantom_lancer_juxtapose"))
    W(ul_open())
    W(li("Illusion Damage Taken decreased from 650% to 625%", b(650, 625, l=True)))
    W(ul_close())

    # Primal Beast
    W(hero_header("Primal Beast"))
    W(facet_header("primal_beast_romp_n_stomp"))
    W(ul_open())
    W(li("Trample: Now provides +10% Self Bonus Move Speed when activated", t("NEW"), extra=inline_note("Allied Bonus when activated stays +5%")))
    W(li("Trample: No longer provides passive +5% Self Bonus Move Speed", t("DEL")))
    W(ul_close())

    # Puck
    W(hero_header("Puck"))
    W(ability("Puckish", slug="puck_puckish", innate=True))
    W(ul_open())
    W(li("Now also restores a flat 20 health and mana per dodge, multiplied if dodging a targeted spell", t("NEW")))
    W(ul_close())

    # Queen of Pain
    W(hero_header("Queen of Pain"))
    W(ability("Shadow Strike", slug="queenofpain_shadow_strike"))
    W(ul_open())
    W(li("Cast Point improved from 0.4s to 0.3s", b(0.4, 0.3, l=True)))
    W(ul_close())

    # Riki
    W(hero_header("Riki"))
    W(ability("Tricks of the Trade", slug="riki_tricks_of_the_trade"))
    W(ul_open())
    W(li("Agility Bonus increased from 40/60/80/100 to 55/70/85/100", b([40, 60, 80, 100], [55, 70, 85, 100])))
    W(ul_close())

    # Rubick
    W(hero_header("Rubick"))
    W(ul_open())
    W(li("Base Intelligence decreased by 1", bstat_h("Rubick", "AttributeBaseIntelligence", "7.37", -1), extra=note_box(hero="Rubick", field="AttributeBaseIntelligence", before_patch="7.37")))
    W(ul_close())
    W(ability("Fade Bolt", slug="rubick_fade_bolt"))
    W(ul_open())
    W(li("Mana Cost increased from 110/120/130/140 to 110/125/140/155", b([110, 120, 130, 140], [110, 125, 140, 155], l=True)))
    W(ul_close())

    # Slardar
    W(hero_header("Slardar"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Health increased from +275 to +300", b(275, 300)))
    W(ul_close())

    # Snapfire
    W(hero_header("Snapfire"))
    W(ability("Scatterblast", slug="snapfire_scatterblast"))
    W(ul_open())
    W(li("Cooldown rescaled from 16/14/12/10 to 18/15/12/9", b([16, 14, 12, 10], [18, 15, 12, 9], l=True)))
    W(ul_close())
    W(ability("Firesnap Cookie", slug="snapfire_firesnap_cookie"))
    W(ul_open())
    W(li("Impact Damage increased from 70/145/220/295 to 75/150/225/300", b([70, 145, 220, 295], [75, 150, 225, 300])))
    W(ul_close())
    W(ability("Spit Out", slug="snapfire_spit_creep"))
    W(ul_open())
    W(li("Now applies the current level of Mortimer Kisses on impact", t("NEW")))
    W(ul_close())

    # Sven
    W(hero_header("Sven"))
    W(ability("Warcry", slug="sven_warcry"))
    W(ul_open())
    W(li("Cooldown increased from 35/30/25/20s to 40/35/30/25s", b([35, 30, 25, 20], [40, 35, 30, 25], l=True)))
    W(ul_close())

    # Terrorblade
    W(hero_header("Terrorblade"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Reflection Cooldown Reduction increased from 4s to 5s", b(4, 5)))
    W(ul_close())

    # Tinker
    W(hero_header("Tinker"))
    W(ability("Defense Matrix", slug="tinker_defense_matrix"))
    W(ul_open())
    W(li("Mana Cost increased from 70/80/90/100 to 80/95/110/125", b([70, 80, 90, 100], [80, 95, 110, 125], l=True)))
    W(ul_close())
    W(facet_header("tinker_repair_bots"))
    W(ul_open())
    W(li("March of the Machines: Heal per second decreased from 15/25/35/45 to 14/21/28/35", b([15, 25, 35, 45], [14, 21, 28, 35])))
    W(ul_close())
    W(ability("March of the Machines", slug="tinker_march_of_the_machines"))
    W(ul_open())
    W(li("Mana Cost increased from 90/110/130/150 to 100/120/140/160", b([90, 110, 130, 150], [100, 120, 140, 160], l=True)))
    W(ul_close())

    # Troll Warlord
    W(hero_header("Troll Warlord"))
    W(facet_header("troll_warlord_bad_influence"))
    W(ul_open())
    W(li("Battle Trance: Attack speed increased from 30% to 40%", b(30, 40)))
    W(ul_close())

    # Tusk
    W(hero_header("Tusk"))
    W(ability("Snowball", slug="tusk_snowball"))
    W(ul_open())
    W(li("Stun Duration now increases by 0.2s per ally in Snowball", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Walrus Punch Stun Duration increased from +0.5s to +0.75s", b(0.5, 0.75)))
    W(ul_close())

    # Ursa
    W(hero_header("Ursa"))
    W(ability("Maul", slug="ursa_maul", innate=True))
    W(ul_open())
    W(li("Health as Damage decreased from 1.5% to 1.2/1.3/1.4/1.5%, scales with Enrage", b(1.5, [1.2, 1.3, 1.4, 1.5])))
    W(ul_close())
    W(ability("Earthshock", slug="ursa_earthshock"))
    W(ul_open())
    W(li("Aghanim's Shard Enrage duration decreased from 1.5s to 1.4s", b(1.5, 1.4)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Earthshock Applies 2 Fury Swipes replaced with +7 Fury Swipes damage", t("SWAP")))
    W(li("Level 20 Talent +10 Fury Swipes Damage replaced with Earthshock Applies 2 Fury Swipes", t("SWAP")))
    W(ul_close())

    # Venomancer
    W(hero_header("Venomancer"))
    W(ability("Septic Shock", slug="venomancer_sepsis", innate=True))
    W(ul_open())
    W(li("Now counts one debuff per unique ability/item (e.g. Shiva's Guard will count as 1 debuff instead of 3)", t("NERF")))
    W(ul_close())

    # Viper
    W(hero_header("Viper"))
    W(ability("Predator", slug="viper_predator", innate=True))
    W(ul_open())
    W(li("Bonus damage is now decreased by the illusion damage reduction amount if applied by illusions", t("NERF")))
    W(li_formula("Damage per missing health decreased", "0.25 + 0.05 per Viper's level", "0.15 + 0.05 per Viper's level", lambda L: 0.25 + 0.05*L, lambda L: 0.15 + 0.05*L, value_fmt="{:g}"))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +20 Corrosive Skin Attack Speed Slow replaced with +15% Poison Attack slow/damage", t("SWAP")))
    W(li("Level 20 Talent +20% Poison Attack slow/damage replaced with +0.2 Predator Damage per missing health", t("SWAP")))
    W(ul_close())

    # Visage
    W(hero_header("Visage"))
    W(ability("Lurker", slug="visage_lurker", innate=True))
    W(ul_open())
    W(li("Max stacks decreased from 10 to 8", b(10, 8)))
    W(ul_close())

    # Void Spirit
    W(hero_header("Void Spirit"))
    W(facet_header("void_spirit_aether_artifice"))
    W(ul_open())
    W(li("Dissimilate: Remnant Effectiveness increased from 60% to 70%", b(60, 70)))
    W(ul_close())

    # Warlock
    W(hero_header("Warlock"))
    W(ability("Fatal Bonds", slug="warlock_fatal_bonds"))
    W(ul_open())
    W(li("Shared Damage increased from 12/16/20/24% to 15/18/21/24%", b([12, 16, 20, 24], [15, 18, 21, 24])))
    W(li("Cooldown increased from 36/30/24/18s to 42/34/26/18s", b([36, 30, 24, 18], [42, 34, 26, 18], l=True)))
    W(ul_close())
    W(ability("Shadow Word", slug="warlock_shadow_word"))
    W(ul_open())
    W(li("Cooldown rescaled from 14s to 15/14/13/12s", b(14, [15, 14, 13, 12], l=True)))
    W(li("Mana Cost decreased from 120/130/140/150 to 110/120/130/140", b([120, 130, 140, 150], [110, 120, 130, 140], l=True)))
    W(li('Cast Range rescaled from 600/700/800/<span class="wrong-word">950</span> to 650/700/750/800', b([600, 700, 800, 900], [650, 700, 750, 800]),
         extra=note_box('This change is wrongly stated. The real change is 600/700/800/900 &rarr; 650/700/750/800 (7.37 had 900 at level 4)')))
    W(ul_close())
    W(ability("Chaotic Offering", slug="warlock_rain_of_chaos"))
    W(ul_open())
    W(li("Golem Permanent Immolation Damage decreased from 30/50/70 to 30/45/60", b([30, 50, 70], [30, 45, 60])))
    W(ul_close())

    # Weaver
    W(hero_header("Weaver"))
    W(facet_header("weaver_hivemind"))
    W(ul_open())
    W(li("The Swarm: XP per attack increased from 4/6/8/10 to 5/8/11/14", b([4, 6, 8, 10], [5, 8, 11, 14])))
    W(ul_close())

    # Windranger
    W(hero_header("Windranger"))
    W(facet_header("windrunner_whirlwind"))
    W(ul_open())
    W(li("Focus Fire: Bonus Attack Range decreased from +150 to +125", b(150, 125)))
    W(ul_close())

    # Winter Wyvern
    W(hero_header("Winter Wyvern"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Damage decreased from +35 to +30", b(35, 30)))
    W(ul_close())

    # Witch Doctor
    W(hero_header("Witch Doctor"))
    W(facet_header("witch_doctor_cleft_death"))
    W(ul_open())
    W(li("Death Ward: Now has a primary and secondary target", t("NEW"), extra=inline_note("Damage to secondary target is equal to 65% of the primary")))
    W(li("Death Ward: Damage to primary target increased from 45/70/95 to 55/90/125", b([45, 70, 95], [55, 90, 125])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Maledict AoE increased from +100 to +125", b(100, 125)))
    W(ul_close())

    # Wraith King
    W(hero_header("Wraith King"))
    W(facet_header("skeleton_king_facet_cursed_blade"))
    W(ul_open())
    W(li("Base Damage decreased from 15/30/45/60 to 10/25/40/55", b([15, 30, 45, 60], [10, 25, 40, 55])))
    W(ul_close())

    # Zeus
    W(hero_header("Zeus"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent -4s Heavenly Jump Cooldown replaced with +1.75 Mana Regen", t("SWAP")))
    W(li("Level 15 Talent +25 Movement Speed after Heavenly Jump replaced with +75 Thundergod's Wrath Damage", t("SWAP")))
    W(li("Level 25 Talent +150 Thundergod's Wrath Damage replaced with +1% Static Field Damage", t("SWAP")))
    W(ul_close())

    write_footer()
    save_html('patches/7.37b.html')
