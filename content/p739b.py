from patch.api import *


def build():
    write_head("7.39b", "29.05.2025")

    # ===== GENERAL UPDATES =====
    W(section("General Updates"))

    W(plain_header("Terrain Changes", terrain_link="7.39b"))
    W(subgroup("Trees"))
    W(ul_open())
    W(li("Several trees have been added and adjusted above the Bottom Radiant Tier 1 tower and on the west side of the lane", t("MISC")))
    W(li("A tree has been removed to the south of the Top Dire Tier 1 tower", t("DEL")))
    W(ul_close())
    W(subgroup("Towers"))
    W(ul_open())
    W(li("The Bottom Radiant Tier 1 tower has been moved slightly to the south", t("MISC")))
    W(ul_close())
    W(subgroup("Other"))
    W(ul_open())
    W(li("Adjusted a juke path to the east of the Mid Radiant Tier 2 tower", t("MISC")))
    W(li("Fixed some locations that were incorrectly blocked for warding", t("MISC")))
    W(ul_close())

    # ===== NEUTRAL ITEM UPDATES =====
    W(section("Neutral Item Updates"))

    W(plain_header("Artifact changes", dynamics=False, sublabel=True))
    W(item_header("Jidi Pollen Bag"))
    W(ul_open())
    W(li("Pollinate health restoration loss increased from 20% to 30%", b(20, 30)))
    W(ul_close())
    W(item_header("Dezun Bloodrite"))
    W(ul_open())
    W(li("Abilities that are considered attacks are no longer impacted by Dezun Bloodrite (Including Outworld Destroyer's Arcane Orb, Viper's Poison Attack, etc.)", t("DEL")))
    W(li("Blood Invocation AoE bonus decreased from 15% to 12%", b(15, 12), extra=inline_note("Dormant Curio AoE bonus decreased from 19.5% to 15.6% — " + b(19.5, 15.6))))
    W(ul_close())
    W(item_header("Giant's Maul"))
    W(ul_open())
    W(li("Crushing Blow debuff duration decreased from 4s to 3s", b(4, 3)))
    W(ul_close())
    W(item_header("Magnifying Monocle"))
    W(ul_open())
    W(li("Keen Eye bonus cast range decreased from 125 to 100", b(125, 100), extra=inline_note("Dormant Curio cast range bonus decreased from 162.5 to 130 — " + b(162.5, 130))))
    W(ul_close())
    W(item_header("Helm of the Undying"))
    W(ul_open())
    W(li("Death Delay cooldown increased from 50s to 100s", b(50, 100, l=True)))
    W(ul_close())

    W(plain_header("Enchantment changes", dynamics=False, sublabel=True))
    W(enchant_header("Crude"))
    W(ul_open())
    W(li("Health Restoration bonus increased from +20/30% to +30/40%", b([20, 30], [30, 40])))
    W(li("Intelligence reduction decreased from 8% to 5%", b(8, 5)))
    W(ul_close())

    # ===== HERO UPDATES =====
    W(section("Hero Updates"))

    # Anti-Mage
    W(hero_header("Anti-Mage"))
    W(facet_header("antimage_magebanes_mirror"))
    W(ul_open())
    W(li("Counterspell: Mana Burn Percentage increased from 150/190/230/270% to 150/200/250/300%", b([150, 190, 230, 270], [150, 200, 250, 300])))
    W(li("Ally: Mana Burn Percentage increased from 270% to 300%", b(270, 300)))
    W(ul_close())

    # Axe
    W(hero_header("Axe"))
    W(ability("Counter Helix", slug="axe_counter_helix"))
    W(ul_open())
    W(li("Aghanim's Scepter Attack Damage Reduction decreased from 15% to 12%", b(15, 12)))
    W(ul_close())

    # Beastmaster
    W(hero_header("Beastmaster"))
    W(ability("Rugged", slug="beastmaster_rugged", innate=True))
    W(ul_open())
    W(li("No longer increases block chance against towers", t("DEL")))
    W(ul_close())

    # Bloodseeker
    W(hero_header("Bloodseeker"))
    W(facet_header("bloodseeker_old_blood"))
    W(ul_open())
    W(li("Bloodrage: Now has a 0.3s cast point when cast on units other than Bloodseeker himself", t("NERF")))
    W(li("Bonus Base damage increased from 10/15/20/25% to 15/20/25/30%", b([10, 15, 20, 25], [15, 20, 25, 30])))
    W(ul_close())

    # Bristleback
    W(hero_header("Bristleback"))
    W(facet_header("bristleback_snot_rocket"))
    W(ul_open())
    W(li("Bristleback: Nasal Goo Radius decreased from 900 to 750", b(900, 750)))
    W(ul_close())

    # Broodmother
    W(hero_header("Broodmother"))
    W(facet_header("broodmother_necrotic_webs"))
    W(ul_open())
    W(li("Spin Web: Health Regeneration Reduction now affects Health Restoration instead", t("MISC")))
    W(ul_close())

    # Centaur Warrunner
    W(hero_header("Centaur Warrunner"))
    W(ability("Horsepower", slug="centaur_horsepower"))
    W(ul_open())
    W(li("Max Movement Speed decreased from 600 to 575", b(600, 575)))
    W(ul_close())

    # Dark Seer
    W(hero_header("Dark Seer"))
    W(ability("Ion Shell", slug="dark_seer_ion_shell"))
    W(ul_open())
    W(li("Duration decreased from 21/24/27/30s to 20/22/24/26s", b([21, 24, 27, 30], [20, 22, 24, 26])))
    W(ul_close())
    W(ability("Wall of Replica", slug="dark_seer_wall_of_replica"))
    W(ul_open())
    W(li("Cast Range decreased from 1300 to 1000", b(1300, 1000)))
    W(ul_close())

    # Dazzle
    W(hero_header("Dazzle"))
    W(facet_header("dazzle_facet_nothl_boon"))
    W(ul_open())
    W(li("Weave: Heal amplification from Dazzle increased from 5% to 7.5%", b(5, 7.5)))
    W(ul_close())

    # Disruptor
    W(hero_header("Disruptor"))
    W(ability("Thunder Strike", slug="disruptor_thunder_strike"))
    W(ul_open())
    W(li("Slow duration decreased from 0.4s to 0.3s", b(0.4, 0.3), extra=inline_note("Slow duration with Thunderstorm facet decreased from 0.8s to 0.6s — " + b(0.8, 0.6))))
    W(ul_close())

    # Doom
    W(hero_header("Doom"))
    W(ul_open())
    W(li("Base Health Regen decreased from 1.25 to 0.66", b(1.25, 0.66)))
    W(ul_close())

    # Elder Titan
    W(hero_header("Elder Titan"))
    W(ul_open())
    W(li("Base movement speed decreased from 310 to 305", b(310, 305)))
    W(ul_close())

    # Enchantress
    W(hero_header("Enchantress"))
    W(ability("Nature's Attendants", slug="enchantress_natures_attendants"))
    W(ul_open())
    W(li("Wisp count increased from 8 to 9", b(8, 9)))
    W(ul_close())

    # Enigma
    W(hero_header("Enigma"))
    W(ability("Demonic Summoning", slug="enigma_demonic_conversion"))
    W(ul_open())
    W(li("Eidolons created from multiplying will now automatically attack the same target as their parent", t("QoL")))
    W(ul_close())

    # Kez
    W(hero_header("Kez"))
    W(ability("Falcon Rush", slug="kez_falcon_rush"))
    W(ul_open())
    W(li("Abilities that are unit targeted attacks now allow Kez to rush to the target", t("MISC"), extra=inline_note("As a result, Kazurai Katana's active will now cause Kez to rush if he is within rush range")))
    W(li("Duration increased from 3/4/5/6s to 3.75/4.5/5.25/6s", b([3, 4, 5, 6], [3.75, 4.5, 5.25, 6])))
    W(ul_close())
    W(ability("Talon Toss", slug="kez_talon_toss"))
    W(ul_open())
    W(li("Mana Cost decreased from 75 to 60/65/70/75", b(75, [60, 65, 70, 75], l=True)))
    W(ul_close())
    W(ability("Shodo Sai", slug="kez_shodo_sai"))
    W(ul_open())
    W(li("Once again grants bonus stun and critical strike from marks generated by parrying an enemy Hero", t("NEW")))
    W(li("Parry Bonus Critical Strike rescaled from 25/50/75/100% to 4% * Enemy Level", t("REWORK")))
    W(ul_close())

    # Lich
    W(hero_header("Lich"))
    W(ability("Death Charge", slug="lich_death_charge", innate=True))
    W(ul_open())
    W(li("Mana restored on Hero Death increased from 15% to 25%", b(15, 25)))
    W(ul_close())

    # Lifestealer
    W(hero_header("Lifestealer"))
    W(facet_header("life_stealer_gorestorm"))
    W(ul_open())
    W(li("Infest: Remaining Health as Gorestorm Damage increased from 25% to 30%", b(25, 30)))
    W(ul_close())

    # Morphling
    W(hero_header("Morphling"))
    W(ability("Attribute Shift (Strength Gain)", slug="morphling_morph_str"))
    W(ul_open())
    W(li("Health change is now affected by negative Health Restoration effects", t("REWORK")))
    W(ul_close())

    # Nature's Prophet
    W(hero_header("Nature's Prophet"))
    W(facet_header("furion_soothing_saplings"))
    W(ul_open())
    W(li("Sprout: Tree enchant radius decreased from 1200 to 900", b(1200, 900)))
    W(ul_close())
    W(facet_header("furion_natures_profit"))
    W(ul_open())
    W(li("Wrath of Nature Base Damage decreased from 100/140/180 to 90/130/170", b([100, 140, 180], [90, 130, 170])))
    W(ul_close())

    # Night Stalker
    W(hero_header("Night Stalker"))
    W(ability("Void", slug="night_stalker_void"))
    W(ul_open())
    W(li("Night Duration decreased from 2/2.5/3/3.5/4s to 1.6/2.2/2.8/3.4/4s", b([2, 2.5, 3, 3.5, 4], [1.6, 2.2, 2.8, 3.4, 4])))
    W(ul_close())

    # Omniknight
    W(hero_header("Omniknight"))
    W(ability("Hammer of Purity", slug="omniknight_hammer_of_purity"))
    W(ul_open())
    W(li("Cooldown increased from 16/12/8/4s to 20/15/10/5s", b([16, 12, 8, 4], [20, 15, 10, 5], l=True)))
    W(li("Damage decreased from 40/60/80/100 to 25/50/75/100", b([40, 60, 80, 100], [25, 50, 75, 100])))
    W(ul_close())

    # Oracle
    W(hero_header("Oracle"))
    W(ul_open())
    W(li("Strength gain decreased from 2.4 to 2.2", b(2.4, 2.2)))
    W(ul_close())
    W(ability("Rain of Destiny", slug="oracle_rain_of_destiny"))
    W(ul_open())
    W(li("Heal amplification decreased from 20% to 15%", b(20, 15)))
    W(ul_close())

    # Ringmaster
    W(hero_header("Ringmaster"))
    W(facet_header("ringmaster_sideshow_secrets"))
    W(ul_open())
    W(li("Crystal Ball: Clairvoyance Scan duration increased from 4s to 5s", b(4, 5)))
    W(li("Weighted Pie: Pie Toss vision recovery time increased from 2s to 3s", b(2, 3)))
    W(ul_close())

    # Sand King
    W(hero_header("Sand King"))
    W(ability("Burrowstrike", slug="sandking_burrowstrike"))
    W(ul_open())
    W(li("Mana Cost decreased from 110/120/130/140 to 100/110/120/130", b([110, 120, 130, 140], [100, 110, 120, 130], l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Stinger Slow increased from +8% to +12%", b(8, 12)))
    W(li("Level 15 Talent Burrowstrike Cast Range increased from +150 to +200", b(150, 200)))
    W(li("Level 15 Talent Sand Storm Damage Per Second increased from +20 to +25", b(20, 25)))
    W(ul_close())

    # Shadow Shaman
    W(hero_header("Shadow Shaman"))
    W(ability("Ether Shock", slug="shadow_shaman_ether_shock"))
    W(ul_open())
    W(li("Damage decreased from 140/200/260/320 to 125/190/255/320", b([140, 200, 260, 320], [125, 190, 255, 320])))
    W(ul_close())
    W(ability("Shackles", slug="shadow_shaman_shackles"))
    W(ul_open())
    W(li("Cooldown increased from 13/12/11/10s to 14/13/12/11s", b([13, 12, 11, 10], [14, 13, 12, 11], l=True)))
    W(ul_close())

    # Skywrath Mage
    W(hero_header("Skywrath Mage"))
    W(ability("Arcane Bolt", slug="skywrath_mage_arcane_bolt"))
    W(ul_open())
    W(li("Base Damage increased from 60/85/110/135 to 60/90/120/150", b([60, 85, 110, 135], [60, 90, 120, 150])))
    W(ul_close())

    # Slark
    W(hero_header("Slark"))
    W(ability("Barracuda", slug="slark_barracuda", innate=True))
    W(ul_open())
    W(li("Health Gained per second decreased from 10/70/100/130 to 5/70/100/130", b([10, 70, 100, 130], [5, 70, 100, 130])))
    W(ul_close())

    # Sniper
    W(hero_header("Sniper"))
    W(ul_open())
    W(li("Base armor increased by 1", bstat_h("Sniper", "ArmorPhysical", "7.39", 1), extra=note_box(hero="Sniper", field="ArmorPhysical", before_patch="7.39")))
    W(ul_close())

    # Techies
    W(hero_header("Techies"))
    W(ability("Sticky Bomb", slug="techies_sticky_bomb"))
    W(ul_open())
    W(li("Damage increased from 80/160/240/320 to 95/170/245/320", b([80, 160, 240, 320], [95, 170, 245, 320])))
    W(ul_close())

    # Templar Assassin
    W(hero_header("Templar Assassin"))
    W(ability("Refraction", slug="templar_assassin_refraction"))
    W(ul_open())
    W(li("Mana Cost increased from 85 to 95", b(85, 95, l=True)))
    W(li("Bonus Damage decreased from 20/40/60/80 to 15/30/45/60", b([20, 40, 60, 80], [15, 30, 45, 60])))
    W(ul_close())

    # Terrorblade
    W(hero_header("Terrorblade"))
    W(ability("Dark Unity", slug="terrorblade_dark_unity"))
    W(ul_open())
    W(li("Damage Penalty increased from 50% to 60%", b(50, 60, l=True)))
    W(ul_close())

    # Troll Warlord
    W(hero_header("Troll Warlord"))
    W(facet_header("troll_warlord_bad_influence"))
    W(ul_open())
    W(li("Battle Trance: Battle Trance Max Fervor Stacks decreased from 15 to 12", b(15, 12)))
    W(ul_close())

    # Underlord
    W(hero_header("Underlord"))
    W(ability("Fiend's Gate", slug="abyssal_underlord_dark_portal"))
    W(ul_open())
    W(li("Mana Cost decreased from 200 to 175", b(200, 175, l=True)))
    W(ul_close())

    # Ursa
    W(hero_header("Ursa"))
    W(ability("Overpower", slug="ursa_overpower"))
    W(ul_open())
    W(li("Slow Resistance rescaled from 10/20/30/40% to 25%", b([10, 20, 30, 40], 25)))
    W(ul_close())
    W(ability("Fury Swipes", slug="ursa_fury_swipes"))
    W(ul_open())
    W(li("Reset Time (Roshan) decreased from 10s to 8s", b(10, 8)))
    W(ul_close())

    # Visage
    W(hero_header("Visage"))
    W(facet_header("visage_sepulchre"))
    W(ul_open())
    W(li("Grave Chill: Secondary Target Penalty increased from 50% to 70%", b(50, 70, l=True)))
    W(ul_close())

    # Warlock
    W(hero_header("Warlock"))
    W(ability("Chaotic Offering", slug="warlock_rain_of_chaos"))
    W(ul_open())
    W(li("Golem's Permanent Immolation is now affected by Warlock's AoE increases", t("NEW")))
    W(ul_close())

    write_footer()
    save_html('patches/7.39b.html')
