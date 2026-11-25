from patch.api import *

def build():
    write_head("7.42a", "24.11.2026")

    # ===== GENERAL UPDATES =====
    W(section("General Updates"))

    W(plain_header("Global Mechanics"))
    W(ul_open())
    W(li("Vector-targeted abilities that are reflected will now reflect in the opposite direction of the initial cast (Walrus Kick, Nightmare, and Rebound. Dead Shot already did this)", t("MISC")))
    W(li("Damaging neutral creeps while under the effect of Smoke of Deceit will now make them attempt to flee", t("MISC")))
    W(ul_close())

    # ===== NEUTRAL CREEP UPDATES =====
    W(section("Neutral Creep Updates"))

    # Radigull
    W(unit_header("Radigull", NEUTRAL_CDN + "radigull.png"))
    W(ul_open())
    W(li("Eggstremism Fuse Duration increased from 2s to 2.5s", b(2, 2.5, l=True)))
    W(ul_close())

    # ===== ITEM UPDATES =====
    W(section("Item Updates"))
    W(item_header("Bloodslinger"))
    W(ul_open())
    W(li("Sling Grenade Health Cost increased from 75 to 100", b(75, 100, l=True)))
    W(ul_close())
    W(item_header("Eye of Skadi"))
    W(ul_open())
    W(li("All Attributes bonus decreased from +35 to +32", b(35, 32)))
    W(ul_close())
    W(item_header("Greater Horn of Battle"))
    W(ul_open())
    W(li("Now correctly states that it summons Super Creeps when used, and Mega Creeps when all enemy barracks are destroyed", t("QoL")))
    W(ul_close())

    # ===== NEUTRAL ITEM UPDATES =====
    W(section("Neutral Item Updates"))
    W(item_header("Safety Bubble"))
    W(ul_open())
    W(li("Bubbled Up damage taken by barrier on illusions now is amplified by the illusion's incoming damage taken percentage", t("NERF")))
    W(ul_close())

    # ===== HERO UPDATES =====
    W(section("Hero Updates"))

    # Abaddon
    W(hero_header("Abaddon"))
    W(ability("Withering Mist", slug="abaddon_withering_mist", innate=True))
    W(ul_open())
    W(li_formula("Max Health Restoration Reduction decreased", "40% + 1% per level", "35% + 1% per level", lambda L: 40 + 1*L, lambda L: 35 + 1*L, value_fmt="{:g}%"))
    W(ul_close())
    W(ability("Aphotic Shield", slug="abaddon_aphotic_shield"))
    W(ul_open())
    W(li("Cooldown increased from 12/10/8/6s to 13/11/9/7s", b([12, 10, 8, 6], [13, 11, 9, 7], l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Curse of Avernus DPS decreased from +25 to +20", b(25, 20)))
    W(ul_close())

    # Beastmaster
    W(hero_header("Beastmaster"))
    W(ability("Summon Ancient Thunderhide", slug="beastmaster_summon_thunderhide"))
    W(ul_open())
    W(li("Thunderhide Base Health decreased from 2200 to 2100", b(2200, 2100)))
    W(li("Thunderhide Base Magic Resistance decreased from 35% to 30%", b(35, 30)))
    W(li("Slam Slow Duration decreased from 4s (3s for heroes) to 2s", t("NERF")))
    W(ul_close())

    # Brewmaster
    W(hero_header("Brewmaster"))
    W(ability("Thunder Clap", slug="brewmaster_thunder_clap"))
    W(ul_open())
    W(li("Movement Slow rescaled from 15/30/45/60% to 20/30/40/50%", b([15, 30, 45, 60], [20, 30, 40, 50])))
    W(li("Attack Slow rescaled from 15/30/45/60 to 20/30/40/50", b([15, 30, 45, 60], [20, 30, 40, 50])))
    W(ul_close())

    # Bristleback
    W(hero_header("Bristleback"))
    W(ul_open())
    W(li("Base Intelligence increased from 14 to 15", b(14, 15)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Bristleback Damage Threshold Reduction increased from 30 to 35", b(30, 35)))
    W(ul_close())

    # Broodmother
    W(hero_header("Broodmother"))
    W(ability("Spawn Spiderlings", slug="broodmother_spawn_spiderlings"))
    W(ul_open())
    W(li("Mana cost increased from 100 to 100/125/150", b(100, [100, 125, 150], l=True)))
    W(ul_close())

    # Centaur Warrunner
    W(hero_header("Centaur Warrunner"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Health Regen increased from +4 to +4.5", b(4, 4.5)))
    W(li("Level 20 Talent Stampede Cooldown Reduction increased from 25s to 30s", b(25, 30)))
    W(ul_close())

    # Chaos Knight
    W(hero_header("Chaos Knight"))
    W(ability("Ahead, Armageddon", slug="chaos_knight_armageddon", innate=True))
    W(ul_open())
    W(li("Now is refreshed on Phantasm cast", t("BUFF")))
    W(li("Now can be used only once per Phantasm cast", t("NERF")))
    W(ul_close())

    # Dazzle
    W(hero_header("Dazzle"))
    W(ul_open())
    W(li("Base Intelligence reduced from 25 to 23", b(25, 23), extra=inline_note("Damage at level 1 decreased from 47-53 to 46-52")))
    W(ul_close())
    W(ability("Nothl Projection", slug="dazzle_nothl_projection"))
    W(ul_open())
    W(li("Aghanim's Shard bonus cast range and leash range decreased from 250/500 to 200/450", b([250, 500], [200, 450]), extra=inline_note("Total Cast Range: from 700 to 650; Total Leash Range: from 2100 to 2050 — " + b(700, 650))))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Shadow Wave Cast Range decreased from +125 to +100", b(125, 100)))
    W(ul_close())

    # Enigma
    W(hero_header("Enigma"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Eidolon Damage decreased from +30 to +25", b(30, 25)))
    W(ul_close())

    # Faceless Void
    W(hero_header("Faceless Void"))
    W(ability("Time Dilation", slug="faceless_void_time_dilation"))
    W(ul_open())
    W(li("Bonus DPS per Stack increased from 6/8/10/12 to 9/10/11/12", b([6, 8, 10, 12], [9, 10, 11, 12])))
    W(ul_close())

    # Grimstroke
    W(hero_header("Grimstroke"))
    W(ability("Stroke of Fate", slug="grimstroke_dark_artistry"))
    W(ul_open())
    W(li("Base Damage rescaled from 100/160/220/280 to 110/160/210/260", b([100, 160, 220, 280], [110, 160, 210, 260])))
    W(ul_close())
    W(ability("Soulbind", slug="grimstroke_soul_chain"))
    W(ul_open())
    W(li("Cast Range rescaled from 700/800/900 to 800", b([700, 800, 900], 800)))
    W(ul_close())
    W(ability("Dark Portrait", slug="grimstroke_dark_portrait"))
    W(ul_open())
    W(li("Illusion Bonus Movespeed decreased from 30% to 25%", b(30, 25)))
    W(ul_close())

    # Gyrocopter
    W(hero_header("Gyrocopter"))
    W(ability("Flak Cannon", slug="gyrocopter_flak_cannon"))
    W(ul_open())
    W(li("Cooldown decreased from 25s to 24s", b(25, 24, l=True)))
    W(ul_close())

    # Huskar
    W(hero_header("Huskar"))
    W(ability("Burning Spear", slug="huskar_burning_spear"))
    W(ul_open())
    W(li("Max Health Burn increased from 0.5% to 0.6%", b(0.5, 0.6)))
    W(ul_close())
    W(ability("Life Break", slug="huskar_life_break"))
    W(ul_open())
    W(li("Cooldown decreased from 16/14/12s to 15/13/11s", b([16, 14, 12], [15, 13, 11], l=True)))
    W(li("Magic Resistance while leaping increased from 60% to 80%", b(60, 80)))
    W(ul_close())

    # Juggernaut
    W(hero_header("Juggernaut"))
    W(ability("Bladeform", slug="juggernaut_bladeform", innate=True))
    W(ul_open())
    W(li("Max Stacks increased from 10 to 12", b(10, 12)))
    W(ul_close())
    W(ability("Healing Ward", slug="juggernaut_healing_ward"))
    W(ul_open())
    W(li("Mana Cost decreased from 120 to 110", b(120, 110, l=True)))
    W(ul_close())

    # Kez
    W(hero_header("Kez"))
    W(ul_open())
    W(li("Base Intelligence decreased from 20 to 18", b(20, 18)))
    W(li("Intelligence gain increased from 1.7 to 1.9", b(1.7, 1.9)))
    W(ul_close())
    W(ability("Talon Toss", slug="kez_talon_toss"))
    W(ul_open())
    W(li("Damage increased from 60/120/180/240 to 80/140/200/260", b([60, 120, 180, 240], [80, 140, 200, 260])))
    W(ul_close())

    # Largo
    W(hero_header("Largo"))
    W(ability("Amphibian Rhapsody", slug="largo_amphibian_rhapsody"))
    W(ul_open())
    W(li("Max Stacks rescaled from 5 to 4/5/6", b(5, [4, 5, 6])))
    W(ul_close())

    # Lina
    W(hero_header("Lina"))
    W(ul_open())
    W(li("Base Strength increased from 20 to 21", b(20, 21)))
    W(li("Agility gain increased from 2.4 to 2.6", b(2.4, 2.6)))
    W(ul_close())
    W(ability("Flame Cloak", slug="lina_flame_cloak"))
    W(ul_open())
    W(li("Magic Resistance increased from 35% to 40%", b(35, 40)))
    W(li("Duration increased from 7s to 8s", b(7, 8)))
    W(ul_close())

    # Lone Druid
    W(hero_header("Lone Druid"))
    W(ul_open())
    W(li("Moving Aghanim's Scepter from Lone Druid to Spirit Bear and vice versa puts the item on a 6s cooldown, preventing it from being used", t("NERF")))
    W(ul_close())
    # Spirit Bear (Valve's hero_id 1961) as a unit block of Lone Druid
    W(unit_header("Spirit Bear", "../icons/abilities/lone_druid_spirit_bear.png", kind="Creep-hero"))
    W(ability("Summon Lone Druid", slug="lone_druid_spirit_bear_summon_druid"))
    W(ul_open())
    W(li("Now Lone Druid drops Everlasting items (Divine Rapier, Gem of True Sight) before his spirit is stored with the Spirit Bear", t("NERF")))
    W(ul_close())

    # Lycan
    W(hero_header("Lycan"))
    W(ability("Pack Hunter", slug="lycan_pack_hunter", innate=True))
    W(ul_open())
    W(li("Now marks can only be applied by Lycan's units within 1200 units of him", t("NERF"), extra=inline_note("Still benefit from attacking marked units even outside of this radius")))
    W(li("Can now be dispelled", t("NERF")))
    W(ul_close())

    # Medusa
    W(hero_header("Medusa"))
    W(ability("Stone Gaze", slug="medusa_stone_gaze"))
    W(ul_open())
    W(li("Duration decreased from 5/5.5/6s to 4.5/5/5.5s", b([5, 5.5, 6], [4.5, 5, 5.5])))
    W(ul_close())

    # Meepo
    W(hero_header("Meepo"))
    W(ul_open())
    W(li("Base Movement Speed decreased from 310 to 305", b(310, 305)))
    W(li("Agility gain decreased from 2.1 to 2.0", b(2.1, 2)))
    W(ul_close())
    W(ability("Divided We Stand", slug="meepo_divided_we_stand"))
    W(ul_open())
    W(li("Experience penalty time increased from 5s to 10s", b(5, 10, l=True)))
    W(ul_close())

    # Morphling
    W(hero_header("Morphling"))
    W(ul_open())
    W(li("Aghanim's Scepter no longer triggers additional casts on certain abilities", t("DEL"), extra=inline_note("Chen's Holy Persuasion<br>Enchantress' Enchant<br>Phantom Assassin's Phantom Strike<br>Snapfire's Gobble Up<br>Spirit Breaker's Charge of Darkness<br>Spirit Breaker's Planar Pocket<br>Underlord’s Fiend’s Gate Portal")))
    W(ul_close())
    W(ability("Morph", slug="morphling_replicate"))
    W(ul_open())
    W(li("No longer allows Morphling to Multicast when morphed into Ogre Magi", t("DEL")))
    W(ul_close())

    # Naga Siren
    W(hero_header("Naga Siren"))
    W(ability("Eelskin", slug="naga_siren_eelskin", innate=True))
    W(ul_open())
    W(li_formula("Evasion per Naga increased", "4% + 0.1% per level", "5% + 0.1% per level", lambda L: 4 + 0.1*L, lambda L: 5 + 0.1*L, value_fmt="{:g}%"))
    W(li("Radius increased from 900 to 1200", b(900, 1200)))
    W(ul_close())

    # Nature's Prophet
    W(hero_header("Nature's Prophet"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Wrath of Nature Base Damage increased from +25 to +30", b(25, 30)))
    W(ul_close())

    # Necrophos
    W(hero_header("Necrophos"))
    W(ability("Reaper's Scythe", slug="necrolyte_reapers_scythe"))
    W(ul_open())
    W(li("Cooldown decreased from 100s to 95s", b(100, 95, l=True)))
    W(ul_close())

    # Omniknight
    W(hero_header("Omniknight"))
    W(ul_open())
    W(li("Agility Gain decreased from 1.7 to 1.5", b(1.7, 1.5)))
    W(ul_close())

    # Phantom Assassin
    W(hero_header("Phantom Assassin"))
    W(ability("Stifling Dagger", slug="phantom_assassin_stifling_dagger"))
    W(ul_open())
    W(li("Attack Damage decreased from 30/45/60/75% to 25/40/55/70%", b([30, 45, 60, 75], [25, 40, 55, 70])))
    W(ul_close())
    W(ability("Phantom Strike", slug="phantom_assassin_phantom_strike"))
    W(ul_open())
    W(li("Bonus Attack Speed decreased from 80/120/160/200 to 75/100/125/150", b([80, 120, 160, 200], [75, 100, 125, 150])))
    W(ul_close())

    # Phantom Lancer
    W(hero_header("Phantom Lancer"))
    W(ability("Illusory Armaments", slug="phantom_lancer_illusory_armaments", innate=True))
    W(ul_open())
    W(li_formula("Damage decreased", "17% + 2% per 3 levels", "15% + 2% per 3 levels", lambda L: 17 + 2 * (L // 3), lambda L: 15 + 2 * (L // 3), value_fmt="{:g}%"))
    W(ul_close())

    # Primal Beast
    W(hero_header("Primal Beast"))
    W(ability("Colossal", slug="primal_beast_colossal", innate=True))
    W(ul_open())
    W(li("Slow Resistance per 100 Max Health decreased from 1% to 0.75%", b(1, 0.75)))
    W(ul_close())

    # Riki
    W(hero_header("Riki"))
    W(ul_open())
    W(li("Base Agility decreased from 30 to 26", b(30, 26), extra=inline_note("Damage at level 1 decreased from 52-56 to 48-52")))
    W(ul_close())
    W(ability("Smoke Screen", slug="riki_smoke_screen"))
    W(ul_open())
    W(li("Cooldown increased from 15/14/13/12s to 16/15/14/13s", b([15, 14, 13, 12], [16, 15, 14, 13], l=True)))
    W(ul_close())
    W(ability("Cloak and Dagger", slug="riki_backstab"))
    W(ul_open())
    W(li("Bonus XP Hero Kill decreased from 130/260/390 to 100/200/300", b([130, 260, 390], [100, 200, 300])))
    W(li("Bonus XP Assist decreased from 100 to 50", b(100, 50)))
    W(ul_close())

    # Sand King
    W(hero_header("Sand King"))
    W(ability("Burrowstrike", slug="sandking_burrowstrike"))
    W(ul_open())
    W(li("Aghanim's Scepter Stinger damage decreased from 75% to 70%", b(75, 70)))
    W(ul_close())

    # Shadow Demon
    W(hero_header("Shadow Demon"))
    W(ability("Disruption", slug="shadow_demon_disruption"))
    W(ul_open())
    W(li("Bonus Base Damage decreased from 20/35/50/65 to 15/30/45/60", b([20, 35, 50, 65], [15, 30, 45, 60])))
    W(ul_close())

    # Shadow Shaman
    W(hero_header("Shadow Shaman"))
    W(ability("Shackles", slug="shadow_shaman_shackles"))
    W(ul_open())
    W(li("Cooldown increased from 14/13/12/11s to 15/14/13/12s", b([14, 13, 12, 11], [15, 14, 13, 12], l=True)))
    W(ul_close())

    # Snapfire
    W(hero_header("Snapfire"))
    W(ability("Firesnap Cookie", slug="snapfire_firesnap_cookie"))
    W(ul_open())
    W(li("Cooldown decreased from 18/17/16/15s to 17/16/15/14s", b([18, 17, 16, 15], [17, 16, 15, 14], l=True)))
    W(ul_close())
    W(ability("Lil' Shredder", slug="snapfire_lil_shredder"))
    W(ul_open())
    W(li("Mana Cost decreased from 70/80/90/100 to 60/65/70/75", b([70, 80, 90, 100], [60, 65, 70, 75], l=True)))
    W(ul_close())

    # Sven
    W(hero_header("Sven"))
    W(ability("Wrath of God", slug="sven_wrath_of_god", innate=True))
    W(ul_open())
    W(li_formula("Damage per Strength rescaled", "0.08 + 0.02 per level", "0.15 + 0.01 per level", lambda L: 0.08 + 0.02*L, lambda L: 0.15 + 0.01*L, value_fmt="{:g}", inline_note_text="From 0.1-0.68 to 0.16-0.45"))
    W(ul_close())
    W(ability("God's Strength", slug="sven_gods_strength"))
    W(ul_open())
    W(li("Slow Resistance decreased from 40% to 30%", b(40, 30)))
    W(ul_close())

    # Timbersaw
    W(hero_header("Timbersaw"))
    W(ul_open())
    W(li("Attacks that miss Timbersaw (due to evasion, blindness, or uphill disadvantage) now provide Reactive Armor stacks", t("BUFF")))
    W(ul_close())

    # Troll Warlord
    W(hero_header("Troll Warlord"))
    W(ability("Berserker's Rage", slug="troll_warlord_berserkers_rage"))
    W(ul_open())
    W(li("Bonus Move Speed decreased from 15/25/35/45 to 15/20/25/30", b([15, 25, 35, 45], [15, 20, 25, 30])))
    W(ul_close())
    W(ability("Battle Trance", slug="troll_warlord_battle_trance"))
    W(ul_open())
    W(li("Movement Speed Bonus decreased from 35% to 30%", b(35, 30)))
    W(ul_close())

    # Visage
    W(hero_header("Visage"))
    W(ul_open())
    W(li("Intelligence gain decreased from 2.9 to 2.6", b(2.9, 2.6), extra=inline_note("Damage gain per level decreased from 3.1 to 3.0")))
    W(ul_close())
    W(ability("Silent as the Grave", slug="visage_silent_as_the_grave", innate=True))
    W(ul_open())
    W(li_formula("Cooldown increased", "45.75s - 0.75s per level", "45.5s - 0.5s per level", lambda L: 45.75 - 0.75*L, lambda L: 45.5 - 0.5*L, l=True, value_fmt="{:g}s", inline_note_text="From 45-23.25s to 45-30.5s"))
    W(ul_close())

    # Wraith King
    W(hero_header("Wraith King"))
    W(ul_open())
    W(li("Agility gain decreased from 1.7 to 1.5", b(1.7, 1.5)))
    W(ul_close())
    W(ability("Bone Guard", slug="skeleton_king_bone_guard"))
    W(ul_open())
    W(li("Mana Cost increased from 70/80/90/100 to 70/85/100/115", b([70, 80, 90, 100], [70, 85, 100, 115], l=True)))
    W(ul_close())

    write_footer()
    save_html('patches/7.42a.html')
