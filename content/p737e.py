from patch.api import *

def build():
    write_head("7.37e", "19.11.2024")

    # ===== ITEM UPDATES =====
    W(section("Item Updates"))
    W(item_header("Khanda"))
    W(auto_components_change("Khanda", "7.37e"))
    W(ul_open())
    W(li("Recipe cost decreased from 600 to 500. Total cost decreased from 5200 to 5100", b([600, 5200], [500, 5100], l=True, slash=True)))
    W(li("Empower Spell: Bonus Damage from caster's Attack Damage decreased from 75% to 60%", b(75, 60)))
    W(ul_close())

    # ===== HERO UPDATES =====
    W(section("Hero Updates"))

    # Alchemist
    W(hero_header("Alchemist"))
    W(facet_header("alchemist_mixologist"))
    W(ul_open())
    W(li("Unstable Concoction: Cooldown reduction increased from 30% to 35%", b(30, 35)))
    W(ul_close())
    W(ability("Acid Spray", slug="alchemist_acid_spray"))
    W(ul_open())
    W(li("Mana Cost rescaled from 110 to 105/110/115/120", b(110, [105, 110, 115, 120], l=True)))
    W(ul_close())
    W(ability("Unstable Concoction", slug="alchemist_unstable_concoction"))
    W(ul_open())
    W(li("Cooldown increased from 15s to 17s", b(15, 17, l=True)))
    W(ul_close())

    # Anti-Mage
    W(hero_header("Anti-Mage"))
    W(ul_open())
    W(li("Base Strength increased from 19 to 21", b(19, 21)))
    W(ul_close())

    # Axe
    W(hero_header("Axe"))
    W(ability("One Man Army", slug="axe_one_man_army"))
    W(ul_open())
    W(li("Armor as Strength decreased from 50% to 40%", b(50, 40)))
    W(ul_close())
    W(ability("Battle Hunger", slug="axe_battle_hunger"))
    W(ul_open())
    W(li("Movement Slow rescaled from 11/19/27/35% to 15/20/25/30%", b([11, 19, 27, 35], [15, 20, 25, 30])))
    W(ul_close())

    # Bane
    W(hero_header("Bane"))
    W(ability("Enfeeble", slug="bane_enfeeble"))
    W(ul_open())
    W(li("Mana Cost rescaled from 120 to 100/110/120/130", b(120, [100, 110, 120, 130], l=True)))
    W(ul_close())

    # Batrider
    W(hero_header("Batrider"))
    W(ability("Smoldering Resin", slug="batrider_smoldering_resin", innate=True))
    W(ul_open())
    W(li("Damage increased from 15% to 20%", b(15, 20)))
    W(ul_close())

    # Beastmaster
    W(hero_header("Beastmaster"))
    W(ability("Drums of Slom", slug="beastmaster_drums_of_slom"))
    W(ul_open())
    W(li("Drum Hit Damage decreased from 85 to 80", b(85, 80)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Inner Beast Magic Resist decreased from 10% to 8%", b(10, 8)))
    W(ul_close())

    # Bounty Hunter
    W(hero_header("Bounty Hunter"))
    W(ability("Shuriken Toss", slug="bounty_hunter_shuriken_toss"))
    W(ul_open())
    W(li("Mana Cost increased from 65/70/75/80 to 75/80/85/90", b([65, 70, 75, 80], [75, 80, 85, 90], l=True)))
    W(ul_close())

    # Brewmaster
    W(hero_header("Brewmaster"))
    W(ul_open())
    W(li("Base Intelligence increased from 15 to 17", b(15, 17)))
    W(ul_close())
    W(ability("Drunken Brawler", slug="brewmaster_drunken_brawler"))
    W(ul_open())
    W(li("Earth Brawler stance armor increased from 1/3/5/7 to 2/4/6/8", b([1, 3, 5, 7], [2, 4, 6, 8])))
    W(ul_close())

    # Bristleback
    W(hero_header("Bristleback"))
    W(ability("Hairball", slug="bristleback_hairball"))
    W(ul_open())
    W(li("Cast Range decreased from 1000 to 750", b(1000, 750)))
    W(ul_close())

    # Clockwerk
    W(hero_header("Clockwerk"))
    W(ability("Battery Assault", slug="rattletrap_battery_assault"))
    W(ul_open())
    W(li("Bonus damage against creeps decreased from 2x to 1.5x", b(2, 1.5)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent -2s Power Cogs Cooldown replaced with +75 Hookshot Damage", t("SWAP")))
    W(ul_close())

    # Dazzle
    W(hero_header("Dazzle"))
    W(ability("Weave", slug="dazzle_innate_weave", innate=True))
    W(ul_open())
    W(li("Duration increased from 8s to 10s", b(8, 10)))
    W(ul_close())

    # Disruptor
    W(hero_header("Disruptor"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Glimpse Max Damage increased from 280 to 300", b(280, 300)))
    W(ul_close())

    # Earth Spirit
    W(hero_header("Earth Spirit"))
    W(ability("Boulder Smash", slug="earth_spirit_boulder_smash"))
    W(ul_open())
    W(li("Bonus damage against creeps decreased from 1.4x to 1.25x", b(1.4, 1.25)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Spell Amplification decreased from +10% to +8%", b(10, 8)))
    W(li("Level 15 Talent Magnetize Damage & Duration decreased from +30% to +25%", b(30, 25)))
    W(li("Level 10 Talent +200 Rolling Boulder Distance replaced with -2s Geomagnetic Grip Cooldown", t("SWAP")))
    W(li("Level 20 Talent -3s Geomagnetic Grip Cooldown replaced with +250 Rolling Boulder Distance", t("SWAP")))
    W(ul_close())

    # Elder Titan
    W(hero_header("Elder Titan"))
    W(facet_header("elder_titan_deconstruction"))
    W(ul_open())
    W(li("Natural Order: Enemies that leave the AoE now lose 1 stack per second instead of all stacks instantly", t("BUFF")))
    W(ul_close())
    W(ability("Echo Stomp", slug="elder_titan_echo_stomp"))
    W(ul_open())
    W(li("Damage rescaled from 70/100/130/160 to 60/100/140/180", b([70, 100, 130, 160], [60, 100, 140, 180])))
    W(ul_close())

    # Enchantress
    W(hero_header("Enchantress"))
    W(ability("Enchant", slug="enchantress_enchant"))
    W(ul_open())
    W(li("Mana Cost increased from 40/50/60/70 to 70", b([40, 50, 60, 70], 70, l=True)))
    W(ul_close())
    W(ability("Nature's Attendants", slug="enchantress_natures_attendants"))
    W(ul_open())
    W(li("Duration decreased from 10/11/12/13s to 7/9/11/13s", b([10, 11, 12, 13], [7, 9, 11, 13])))
    W(ul_close())

    # Enigma
    W(hero_header("Enigma"))
    W(ability("Demonic Summoning", slug="enigma_demonic_conversion"))
    W(ul_open())
    W(li("Eidolon gold bounty increased from 14-20 to 17-20", br(14, 20, 17, 20, l=True)))
    W(ul_close())

    # Grimstroke
    W(hero_header("Grimstroke"))
    W(facet_header("grimstroke_fine_art"))
    W(ul_open())
    W(li("Stroke of Fate: Improved behavior when casting at maximum cast range", t("QoL")))
    W(ul_close())

    # Gyrocopter
    W(hero_header("Gyrocopter"))
    W(ability("Rocket Barrage", slug="gyrocopter_rocket_barrage"))
    W(ul_open())
    W(li("Mana Cost rescaled from 75/80/85/90 to 85", b([75, 80, 85, 90], 85, l=True)))
    W(ul_close())

    # Invoker
    W(hero_header("Invoker"))
    W(ability("E.M.P.", slug="invoker_emp"))
    W(ul_open())
    W(li("Aghanim's Shard pull speed decreased from 175 to 150", b(175, 150)))
    W(ul_close())
    W(ability("Cold Snap", slug="invoker_cold_snap"))
    W(ul_open())
    W(li("Mana Cost increased from 90 to 100", b(90, 100, l=True)))
    W(ul_close())

    # Jakiro
    W(hero_header("Jakiro"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent -10%/10 Dual Breath Movement/Attack Speed Slow replaced with -2s Dual Breath Cooldown", t("SWAP")))
    W(ul_close())

    # Juggernaut
    W(hero_header("Juggernaut"))
    W(ability("Blade Fury", slug="juggernaut_blade_fury"))
    W(ul_open())
    W(li("Cooldown decreased from 42/34/26/18s to 36/30/24/18s", b([42, 34, 26, 18], [36, 30, 24, 18], l=True)))
    W(ul_close())

    # Kez
    W(hero_header("Kez"))
    W(ability("Echo Slash", slug="kez_echo_slash"))
    W(ul_open())
    W(li("Bonus Hero Damage rescaled from 30/45/60/75 to 25/45/65/85", b([30, 45, 60, 75], [25, 45, 65, 85])))
    W(ul_close())
    W(ability("Grappling Claw", slug="kez_grappling_claw"))
    W(ul_open())
    W(li("Hero Bonus Lifesteal decreased from 50/100/150/200 to 40/80/120/160", b([50, 100, 150, 200], [40, 80, 120, 160])))
    W(ul_close())

    # Legion Commander
    W(hero_header("Legion Commander"))
    W(ability("Overwhelming Odds", slug="legion_commander_overwhelming_odds"))
    W(ul_open())
    W(li("Aghanim's Shard Radius Bonus in Duel decreased from 150 to 100", b(150, 100)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Press The Attack Movement Speed increased from +10% to +12%", b(10, 12)))
    W(ul_close())

    # Lich
    W(hero_header("Lich"))
    W(facet_header("lich_frostbound"))
    W(ul_open())
    W(li("Chain Frost: Frostbound Duration decreased from 2/3/4s to 2/2.75/3.5s", b([2, 3, 4], [2, 2.75, 3.5])))
    W(li("Chain Frost: If the affected hero dies and buys back, Chain Frost will no longer follow that hero", t("DEL")))
    W(ul_close())

    # Lina
    W(hero_header("Lina"))
    W(ability("Fiery Soul", slug="lina_fiery_soul"))
    W(ul_open())
    W(li("Aghanim's Shard Spell Damage per charge increased from 20 to 25", b(20, 25)))
    W(ul_close())

    # Lion
    W(hero_header("Lion"))
    W(ul_open())
    W(li("Base Intelligence decreased from 20 to 19", b(20, 19)))
    W(ul_close())

    # Luna
    W(hero_header("Luna"))
    W(ability("Lunar Blessing", slug="luna_lunar_blessing", innate=True))
    W(ul_open())
    W(li_formula("Bonus Night Vision rescaled", "400 + 20 per level", "250 + 25 per level", lambda L: 400 + 20*L, lambda L: 250 + 25*L, value_fmt="{:g}"))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Moon Glaives Damage Penalty Reduction decreased from 8% to 5%", b(8, 5)))
    W(li("Level 15 Talent +80 Lucent Beam Damage replaced with +1 Lunar Orbit glaive", t("SWAP")))
    W(li("Level 20 Talent 2 Moon Glaives fired on Lucent Beam replaced with +110 Lucent Beam Damage", t("SWAP")))
    W(ul_close())

    # Lycan
    W(hero_header("Lycan"))
    W(facet_header("lycan_spirit_wolves"))
    W(ul_open())
    W(li("Summon Wolves: Fixed spirit wolves being visible when Lycan himself is invisible", t("MISC")))
    W(ul_close())
    W(ability("Apex Predator", slug="lycan_apex_predator", innate=True))
    W(ul_open())
    W(li("Now also applies to units under Lycan's control. Bonus is still based on Lycan's level", t("BUFF")))
    W(ul_close())

    # Medusa
    W(hero_header("Medusa"))
    W(facet_header("medusa_slow_attacks"))
    W(ul_open())
    W(li("Now scales with Split Shot", t("REWORK")))
    W(li("Movement Slow rescaled from 35% to 15/20/25/30/35%", b(35, [15, 20, 25, 30, 35])))
    W(li("Attack speed slow rescaled from 80 to 20/35/50/65/80", b(80, [20, 35, 50, 65, 80])))
    W(li("Poison is no longer applied by illusions", t("DEL")))
    W(ul_close())
    W(ability("Mana Shield", slug="medusa_mana_shield", innate=True))
    W(ul_open())
    W(li("Base Damage per mana decreased from 2.4 to 2.2", b(2.4, 2.2)))
    W(ul_close())
    W(ability("Split Shot", slug="medusa_split_shot"))
    W(ul_open())
    W(li("Outgoing damage rescaled from 40/55/70/85% to 50/60/70/80%", b([40, 55, 70, 85], [50, 60, 70, 80])))
    W(ul_close())

    # Monkey King
    W(hero_header("Monkey King"))
    W(ability("Mischief", slug="monkey_king_mischief", innate=True))
    W(ul_open())
    W(li("Damage immunity duration decreased from 0.2s to 0.1s", b(0.2, 0.1)))
    W(ul_close())

    # Muerta
    W(hero_header("Muerta"))
    W(ability("The Calling", slug="muerta_the_calling"))
    W(ul_open())
    W(li("Movement Slow rescaled from 15/20/25/30% to 20%", b([15, 20, 25, 30], 20)))
    W(ul_close())

    # Naga Siren
    W(hero_header("Naga Siren"))
    W(facet_header("naga_siren_active_riptide"))
    W(ul_open())
    W(li("Mana Cost increased from 50/60/70/80 to 80", b([50, 60, 70, 80], 80, l=True)))
    W(li("Duration decreased from 4s to 3.5s", b(4, 3.5)))
    W(ul_close())
    W(ability("Song of the Siren", slug="naga_siren_song_of_the_siren"))
    W(ul_open())
    W(li("Aghanim's Shard Max HP per second decreased from 6/7/8% to 5/6/7%", b([6, 7, 8], [5, 6, 7])))
    W(ul_close())

    # Nature's Prophet
    W(hero_header("Nature's Prophet"))
    W(facet_header("furion_ironwood_treant"))
    W(ul_open())
    W(li("Nature's Call: Treant XP bounty increased from 30 to 30/40/50/60", b(30, [30, 40, 50, 60], l=True)))
    W(li("Nature's Call: Treant gold bounty rescaled from 18-24 on all levels to 16/24/32/40", b(21, [16, 24, 32, 40], l=True)))
    W(ul_close())

    # Outworld Destroyer
    W(hero_header("Outworld Destroyer"))
    W(ability("Ominous Discernment", slug="obsidian_destroyer_ominous_discernment", innate=True))
    W(ul_open())
    W(li("Bonus mana per Intelligence increased from 2 to 2.5", b(2, 2.5)))
    W(ul_close())

    # Pangolier
    W(hero_header("Pangolier"))
    W(facet_header("pangolier_thunderbolt"))
    W(ul_open())
    W(li("Rolling Thunder: Turn Rate bonus changed from flat +110 to +40% (results in +48)", b(230, 168)))
    W(ul_close())

    # Phantom Lancer
    W(hero_header("Phantom Lancer"))
    W(ability("Phantom Rush", slug="phantom_lancer_phantom_edge"))
    W(ul_open())
    W(li("Bonus Agility Duration increased from 1.5s to 2s", b(1.5, 2)))
    W(ul_close())

    # Primal Beast
    W(hero_header("Primal Beast"))
    W(ability("Trample", slug="primal_beast_trample"))
    W(ul_open())
    W(li("Mana Cost increased from 90 to 100", b(90, 100, l=True)))
    W(ul_close())
    W(ability("Pulverize", slug="primal_beast_pulverize"))
    W(ul_open())
    W(li("Hit Damage rescaled from 125/175/225 to 100/175/250", b([125, 175, 225], [100, 175, 250], force_overall="buff")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Onslaught Damage decreased from +90 to +80", b(90, 80)))
    W(ul_close())

    # Puck
    W(hero_header("Puck"))
    W(ability("Puckish", slug="puck_puckish", innate=True))
    W(ul_open())
    W(li("Spell Dodge multiplier decreased from 4x to 3.5x", b(4, 3.5)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Illusory Orb Damage decreased from +50 to +40", b(50, 40)))
    W(ul_close())

    # Queen of Pain
    W(hero_header("Queen of Pain"))
    W(facet_header("queenofpain_selfdmg"))
    W(ul_open())
    W(li("Spell Amplification decreased from 15% to 14%", b(15, 14)))
    W(li("Outgoing Spell Damage reflected increased from 20% to 21%", b(20, 21, l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Strength decreased from +8 to +7", b(8, 7)))
    W(ul_close())

    # Ringmaster
    W(hero_header("Ringmaster"))
    W(ability("Escape Act", slug="ringmaster_the_box"))
    W(ul_open())
    W(li("Aghanim's Scepter: Replaces cooldown with 2 charges. When the box pops open, it deals 300 magical damage to all enemies in a 275 radius and throws 8 Impalement Art daggers with 50% range in all directions.", t("NEW")))
    W(ul_close())
    W(ability("Spotlight", slug="ringmaster_spotlight"))
    W(ul_open())
    W(li("Now summons 3 separate spotlights each sweeping independently from each other", t("NEW")))
    W(li("Spotlight Radius decreased from 550 to 275", b(550, 275)))
    W(ul_close())

    # Sand King
    W(hero_header("Sand King"))
    W(facet_header("sand_king_sandshroud"))
    W(ul_open())
    W(li("Sand Storm: Duration decreased from 20/25/30/35s to 16/20/24/28s", b([20, 25, 30, 35], [16, 20, 24, 28]), extra=inline_note("Now it's the same for both Facets")))
    W(ul_close())
    W(ability("Sand Storm", slug="sandking_sand_storm"))
    W(ul_open())
    W(li("Damage per Second rescaled from 25/50/75/100 to 30/50/70/90", b([25, 50, 75, 100], [30, 50, 70, 90])))
    W(ul_close())

    # Shadow Demon
    W(hero_header("Shadow Demon"))
    W(ability("Disruption", slug="shadow_demon_disruption"))
    W(ul_open())
    W(li("Bonus Base Damage rescaled from 30/40/50/60 to 25/40/55/70", b([30, 40, 50, 60], [25, 40, 55, 70])))
    W(ul_close())
    W(ability_group(("Demonic Purge", "shadow_demon_demonic_purge"), ("Demonic Cleanse", "shadow_demon_demonic_cleanse")))
    W(ul_open())
    W(li("Cooldown increased from 60s to 70/65/60s", b(60, [70, 65, 60], l=True)))
    W(li("Aghanim's Scepter charge restoration time increased from 60s to 70/65/60s", b(60, [70, 65, 60], l=True)))
    W(ul_close())

    # Shadow Fiend
    W(hero_header("Shadow Fiend"))
    W(facet_header("nevermore_lasting_presence"))
    W(ul_open())
    W(li("Presence of the Dark Lord: Hero Reduction Duration decreased from 70s to 60s", b(70, 60)))
    W(li("Presence of the Dark Lord: Now Bonus Armor Reduction buff is removed when Shadow Fiend dies", t("NERF")))
    W(ul_close())
    W(ability("Necromastery", slug="nevermore_necromastery", innate=True))
    W(ul_open())
    W(li("Damage per soul decreased from 1/3/4/5 to 1/2/3/4", b([1, 3, 4, 5], [1, 2, 3, 4])))
    W(ul_close())
    W(ability("Feast of Souls", slug="nevermore_frenzy"))
    W(ul_open())
    W(li("Now increases Max Necromastery Souls by 5 for the duration of the buff", t("NEW")))
    W(li("Bonus Attack Speed rescaled from 40/50/60/70 to 30/50/70/90", b([40, 50, 60, 70], [30, 50, 70, 90])))
    W(ul_close())

    # Shadow Shaman
    W(hero_header("Shadow Shaman"))
    W(ul_open())
    W(li("Base Attack Speed increased from 90 to 100", b(90, 100)))
    W(ul_close())
    W(ability("Hex", slug="shadow_shaman_voodoo"))
    W(ul_open())
    W(li("Mana Cost rescaled from 110/140/170/200 to 130/150/170/190", b([110, 140, 170, 200], [130, 150, 170, 190], l=True)))
    W(ul_close())

    # Storm Spirit
    W(hero_header("Storm Spirit"))
    W(ability("Overload", slug="storm_spirit_overload"))
    W(ul_open())
    W(li("Fixed Overload proccing an extra time when using Aghanim's Shard", t("MISC")))
    W(ul_close())

    # Sven
    W(hero_header("Sven"))
    W(ability("Vanquisher", slug="sven_vanquisher", innate=True))
    W(ul_open())
    W(li("Bonus damage increased from 17% to 20%", b(17, 20)))
    W(ul_close())
    W(ability("God's Strength", slug="sven_gods_strength"))
    W(ul_open())
    W(li("Mana Cost decreased from 100/150/200 to 100/125/150", b([100, 150, 200], [100, 125, 150], l=True)))
    W(ul_close())

    # Terrorblade
    W(hero_header("Terrorblade"))
    W(ability("Reflection", slug="terrorblade_reflection"))
    W(ul_open())
    W(li("Mana Cost increased from 35/40/45/50 to 45/50/55/60", b([35, 40, 45, 50], [45, 50, 55, 60], l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Reflection Cooldown Reduction decreased from 5s to 4s", b(5, 4)))
    W(ul_close())

    # Tidehunter
    W(hero_header("Tidehunter"))
    W(ability("Anchor Smash", slug="tidehunter_anchor_smash"))
    W(ul_open())
    W(li("Mana Cost decreased from 45/50/55/60 to 40/45/50/55", b([45, 50, 55, 60], [40, 45, 50, 55], l=True)))
    W(ul_close())

    # Treant Protector
    W(hero_header("Treant Protector"))
    W(facet_header("treant_primeval_power"))
    W(ul_open())
    W(li("Damage per level increased from 5 to 6", b(5, 6)))
    W(ul_close())

    # Tusk
    W(hero_header("Tusk"))
    W(ability("Bitter Chill", slug="tusk_bitter_chill", innate=True))
    W(ul_open())
    W(li("Now scales with Walrus Punch instead of Tag Team or Drinking Buddies", t("REWORK")))
    W(li("Attack Speed Slow rescaled from 20/30/40/50/60 to 15/35/55/75", b([20, 30, 40, 50, 60], [15, 35, 55, 75])))
    W(ul_close())

    # Undying
    W(hero_header("Undying"))
    W(ability("Decay", slug="undying_decay"))
    W(ul_open())
    W(li("Base Damage increased from 0/40/80/120 to 10/50/90/130", b([0, 40, 80, 120], [10, 50, 90, 130])))
    W(ul_close())

    # Venomancer
    W(hero_header("Venomancer"))
    W(facet_header("venomancer_plague_carrier"))
    W(ul_open())
    W(li("Ward Health from Carrier's Max Health increased from 1/1.5/2/2.5% to 1.5/2/2.5/3%", b([1, 1.5, 2, 2.5], [1.5, 2, 2.5, 3])))
    W(ul_close())

    # Visage
    W(hero_header("Visage"))
    W(facet_header("visage_gold_assumption"))
    W(ul_open())
    W(li("Soul Assumption: Bonus Gold per Charge decreased from 35 to 30", b(35, 30)))
    W(ul_close())

    # Warlock
    W(hero_header("Warlock"))
    W(ability("Eldritch Summoning", slug="warlock_eldritch_summoning", innate=True))
    W(ul_open())
    W(li("Imps no longer explode if killed by enemy heroes", t("DEL")))
    W(ul_close())

    # Witch Doctor
    W(hero_header("Witch Doctor"))
    W(ability("Voodoo Switcheroo", slug="witch_doctor_voodoo_switcheroo"))
    W(ul_open())
    W(li("Duration decreased from 3s to 2.5s", b(3, 2.5)))
    W(ul_close())

    # Wraith King
    W(hero_header("Wraith King"))
    W(ul_open())
    W(li("Base Armor increased by 2", bstat_h("Wraith King", "ArmorPhysical", "7.37d", 2), extra=note_box(hero="Wraith King", field="ArmorPhysical", before_patch="7.37d")))
    W(ul_close())
    W(ability("Vampiric Spirit", slug="skeleton_king_vampiric_spirit", innate=True))
    W(ul_open())
    W(li('Lifesteal decreased from <span class="wrong-word">20/30/40</span>/50% to 16/24/32/40%', b([26, 34, 42, 50], [16, 24, 32, 40]),
         extra=note_box('This change is wrongly stated. The real change is 26/34/42/50% &rarr; 16/24/32/40% (the whole 7.37 cycle had 26/34/42/50%)')))
    W(ul_close())
    W(ability("Mortal Strike", slug="skeleton_king_mortal_strike"))
    W(ul_open())
    W(li("Critical Damage rescaled from 150/200/250/300% to 160/200/240/280%", b([150, 200, 250, 300], [160, 200, 240, 280])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Attack Speed decreased from +70 to +60", b(70, 60)))
    W(li("Level 20 Talent Cleave increased from +35% to +40%", b(35, 40)))
    W(ul_close())

    write_footer()
    save_html('patches/7.37e.html')
