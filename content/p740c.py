from patch.api import *

def build():
    write_head("7.40c", "21.01.2026")

    # ===== ITEM UPDATES =====
    W(section("Item Updates"))

    W(item_header("Khanda"))
    W(ul_open())
    W(li("Can now be disassembled", t("NEW")))
    W(ul_close())

    W(item_header("Phylactery"))
    W(ul_open())
    W(li("All Attributes bonus decreased from 7 to 6", b(7, 6)))
    W(li("Mana Regen decreased from 2.5 to 2.25", b(2.5, 2.25)))
    W(ul_close())

    # ===== HERO UPDATES =====
    W(section("Hero Updates"))

    # Abaddon
    W(hero_header("Abaddon"))
    W(ability("Curse of Avernus", slug="abaddon_frostmourne"))
    W(ul_open())
    W(li("No longer applied by illusions", t("DEL")))
    W(ul_close())

    # Axe
    W(hero_header("Axe"))
    W(ul_open())
    W(li("Strength gain decreased from 2.8 to 2.7", b(2.8, 2.7)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Battle Hunger Damage Per Second decreased from +10 to +8", b(10, 8)))
    W(ul_close())

    # Batrider
    W(hero_header("Batrider"))
    W(ul_open())
    W(li("Agility gain increased from 1.8 to 2.0", b(1.8, 2.0)))
    W(li("Damage gain per level increased from 3.4 to 3.5", b(3.4, 3.5)))
    W(ul_close())

    # Bloodseeker
    W(hero_header("Bloodseeker"))
    W(ability("Bloodrage"))
    W(ul_open())
    W(li("Max Health Damage per second decreased from 1.4% to 1.2%", b(1.4, 1.2)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Health increased from +175 to +200", b(175, 200)))
    W(li("Level 20 Talent Agility decreased from +20 to +15", b(20, 15)))
    W(li("Level 20 Talent Rupture Cast Range decreased from +425 to +400", b(425, 400)))
    W(ul_close())

    # Brewmaster
    W(hero_header("Brewmaster"))
    W(ability("Liquid Courage"))
    W(ul_open())
    W(li("Aghanim's Shard Max HP Regen per second increased from 2% to 2.5%", b(2, 2.5)))
    W(ul_close())
    W(ability("Drunken Brawler"))
    W(ul_open())
    W(li("Earth Brawler Armor increased from 2/4/6/8 to 3/5/7/9", b([2, 4, 6, 8], [3, 5, 7, 9])))
    W(ul_close())

    # Broodmother
    W(hero_header("Broodmother"))
    W(facet_header("broodmother_necrotic_webs"))
    W(ul_open())
    W(li("Spin Web enemy Restoration Reduction decreased from 10/30/50/70% to 10/25/40/55%", b([10, 30, 50, 70], [10, 25, 40, 55])))
    W(ul_close())
    W(ability("Spin Web"))
    W(ul_open())
    W(li("Max Charges decreased from 4/6/8/10 to 3/5/7/9", b([4, 6, 8, 10], [3, 5, 7, 9])))
    W(ul_close())
    W(ability("Incapacitating Bite"))
    W(ul_open())
    W(li("No longer applied by illusions", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Incapacitating Bite Attack Bonus decreased from +8 to +6", b(8, 6)))
    W(li("Level 25 Talent BAT Reduction during Insatiable Hunger decreased from 0.2s to 0.15s", b(0.2, 0.15)))
    W(ul_close())

    # Clinkz
    W(hero_header("Clinkz"))
    W(ability("Skeleton Walk", slug="clinkz_wind_walk"))
    W(ul_open())
    W(li("Skeleton Building Damage penalty increased from 25% to 75%", b(25, 75, l=True),
         extra=inline_note("Also applies to Burning Army skeletons.")))
    W(li("No longer upgraded with Aghanim's Scepter", t("DEL")))
    W(li("Aghanim's Scepter now only provides Burning Army ability without increasing Skeleton Archer Hits to Kill by 1", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Attack Range decreased from +60 to +50", b(60, 50)))
    W(li("Level 25 Talent Searing Arrows Multishot no longer applies to Skeleton Archers", t("NERF")))
    W(ul_close())

    # Dark Seer
    W(hero_header("Dark Seer"))
    W(ul_open())
    W(li("Base Armor increased by 1", t("BUFF")))
    W(ul_close())

    # Doom
    W(hero_header("Doom"))
    W(ability("Infernal Blade"))
    W(ul_open())
    W(li("Mana Cost decreased from 40 to 35", b(40, 35, l=True)))
    W(ul_close())

    # Drow Ranger
    W(hero_header("Drow Ranger"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Marksmanship Chance decreased from +10% to +8%", b(10, 8)))
    W(ul_close())

    # Earthshaker
    W(hero_header("Earthshaker"))
    W(ability("Fissure"))
    W(ul_open())
    W(li("Mana Cost decreased from 120/125/130/135 to 115/120/125/130", b([120, 125, 130, 135], [115, 120, 125, 130], l=True)))
    W(ul_close())

    # Ember Spirit
    W(hero_header("Ember Spirit"))
    W(ability("Searing Chains"))
    W(ul_open())
    W(li("Duration decreased from 1.5/2/2.5/3s to 1.25/1.75/2.25/2.75s", b([1.5, 2, 2.5, 3], [1.25, 1.75, 2.25, 2.75])))
    W(li("Damage Per Second rescaled from 50/70/90/110 to 100", b([50, 70, 90, 110], 100)))
    W(ul_close())

    # Grimstroke
    W(hero_header("Grimstroke"))
    W(ul_open())
    W(li("Base damage increased by 1", bstat_h("Grimstroke", "AttackDamageMin", "7.40b", 1), extra=note_box(hero="Grimstroke", field="AttackDamageMin", before_patch="7.40b")))
    W(li("Damage at level 1 changed from 46–50 to 47–51", br(46, 50, 47, 51)))
    W(ul_close())
    W(ability("Ink Swell", slug="grimstroke_spirit_walk"))
    W(ul_open())
    W(li("Cast Range increased from 500/600/700/800 to 650/700/750/800", b([500, 600, 700, 800], [650, 700, 750, 800])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Ink Swell Movement Speed increased from +12% to +15%", b(12, 15)))
    W(ul_close())

    # Gyrocopter
    W(hero_header("Gyrocopter"))
    W(ul_open())
    W(li("Base Attack Speed decreased from 125 to 115", b(125, 115)))
    W(li("Agility gain increased from 3.2 to 3.4", b(3.2, 3.4)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Call Down Cooldown Reduction increased from 30s to 40s", b(30, 40)))
    W(ul_close())

    # Huskar
    W(hero_header("Huskar"))
    W(facet_header("huskar_cauterize"))
    W(ul_open())
    W(li("Berserker's Blood cooldown increased from 50/40/30/20s to 60/50/40/30s", b([50, 40, 30, 20], [60, 50, 40, 30], l=True)))
    W(ul_close())

    # Jakiro
    W(hero_header("Jakiro"))
    W(ul_open())
    W(li("Base Intelligence decreased from 26 to 25", b(26, 25)))
    W(li("Damage at level 1 decreased from 53–61 to 52–60", br(53, 61, 52, 60)))
    W(ul_close())
    W(ability("Ice Path"))
    W(ul_open())
    W(li("Path Duration decreased from 3/3.5/4/4.5s to 2.6/3.1/3.6/4.1s", b([3, 3.5, 4, 4.5], [2.6, 3.1, 3.6, 4.1])))
    W(ul_close())

    # Largo
    W(hero_header("Largo"))
    W(ul_open())
    W(li("Added to Captains Mode", t("NEW")))
    W(li("Intelligence gain increased from 2.4 to 2.6", b(2.4, 2.6)))
    W(ul_close())
    W(ability("Frogstomp"))
    W(ul_open())
    W(li("Damage per stomp increased from 35/45/55/65 to 36/48/60/72", b([35, 45, 55, 65], [36, 48, 60, 72])))
    W(ul_close())
    W(ability("Amphibian Rhapsody"))
    W(ul_open())
    W(li("Now can be toggled while silenced", t("MISC")))
    W(li("Radius increased from 750 to 800", b(750, 800)))
    W(ul_close())

    # Legion Commander
    W(hero_header("Legion Commander"))
    W(ability("Duel"))
    W(ul_open())
    W(li("Aghanim's Scepter Duration decreased from 5.5/6/6.5s to 5/5.5/6s", b([5.5, 6, 6.5], [5, 5.5, 6])))
    W(ul_close())

    # Lone Druid
    W(hero_header("Lone Druid"))
    W(ul_open())
    W(li("Base Agility increased from 20 to 22", b(20, 22)))
    W(li("Damage at level 1 increased from 42–46 to 44–48", br(42, 46, 44, 48)))
    W(ul_close())
    W(ability("Savage Roar"))
    W(ul_open())
    W(li("Duration increased from 0.8/1.2/1.6/2s to 1.1/1.4/1.7/2s", b([0.8, 1.2, 1.6, 2], [1.1, 1.4, 1.7, 2])))
    W(ul_close())
    W(subnote("Same change applies to the Spirit Bear's Savage Roar"))
    W(ability("Return", slug="lone_druid_spirit_bear_return"))
    W(ul_open())
    W(li("Roots and leashes will now interrupt Return's channeling", t("NERF"),
         extra=inline_note("Previously they only prevented casting of Return, but had no effect if applied during the channeling.")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Slow Resistance during True Form increased from 60% to 70%", b(60, 70)))
    W(ul_close())

    # Meepo
    W(hero_header("Meepo"))
    W(ability("MegaMeepo", slug="meepo_megameepo"))
    W(ul_open())
    W(li("Poof damage factor per additional Meepo decreased from 75% to 50%", b(75, 50)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Poof Damage decreased from +50 to +40", b(50, 40)))
    W(li("Level 20 Talent Ransack Health Steal decreased from +8 to +7", b(8, 7)))
    W(ul_close())

    # Monkey King
    W(hero_header("Monkey King"))
    W(ability("Jingu Mastery"))
    W(ul_open())
    W(li("Bonus Damage increased from 30/75/120/165 to 30/80/130/180", b([30, 75, 120, 165], [30, 80, 130, 180])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Primal Spring Max Damage increased from +85 to +90", b(85, 90)))
    W(ul_close())

    # Nature's Prophet
    W(hero_header("Nature's Prophet"))
    W(ability("Nature's Call", slug="furion_force_of_nature"))
    W(ul_open())
    W(li("Treant Damage increased from 16/24/32/40 to 16/25/34/43", b([16, 24, 32, 40], [16, 25, 34, 43])))
    W(ul_close())

    # Pangolier
    W(hero_header("Pangolier"))
    W(ul_open())
    W(li("Base Strength increased from 19 to 20", b(19, 20)))
    W(ul_close())
    W(ability("Fortune Favors the Bold"))
    W(ul_open())
    W(li("Chance Reduction increased from 40% to 50%", b(40, 50)))
    W(ul_close())
    W(ability("Swashbuckle"))
    W(ul_open())
    W(li("Cooldown decreased from 20/17/14/11s to 19/16/13/10s", b([20, 17, 14, 11], [19, 16, 13, 10], l=True)))
    W(ul_close())

    # Phantom Assassin
    W(hero_header("Phantom Assassin"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Stifling Dagger Cooldown Reduction increased from 1.5s to 2s", b(1.5, 2)))
    W(ul_close())

    # Phantom Lancer
    W(hero_header("Phantom Lancer"))
    W(ability("Illusory Armaments"))
    W(ul_open())
    W(li("Min Damage at level 1 decreased from 18% to 17%", b(18, 17),
         extra=inline_note("Increment value per 3 level-ups is still 2%.")))
    W(ul_close())
    W(ability("Doppelganger", slug="phantom_lancer_doppelwalk"))
    W(ul_open())
    W(li("Mana Cost increased from 50 to 70", b(50, 70, l=True)))
    W(ul_close())

    # Pudge
    W(hero_header("Pudge"))
    W(ability("Meat Shield", slug="pudge_flesh_heap"))
    W(ul_open())
    W(li("Mana Cost increased from 50/60/70/80 to 65/70/75/80", b([50, 60, 70, 80], [65, 70, 75, 80], l=True)))
    W(ul_close())

    # Ringmaster
    W(hero_header("Ringmaster"))
    W(ul_open())
    W(li("Base Agility decreased from 13 to 11", b(13, 11)))
    W(li("Agility gain increased from 1.4 to 1.6", b(1.4, 1.6)))
    W(ul_close())
    W(facet_header("ringmaster_carny_classics"))
    W(ul_open())
    W(li("Whoopee Cushion stink cloud radius increased from 200 to 250", b(200, 250)))
    W(ul_close())

    # Rubick
    W(hero_header("Rubick"))
    W(ability("Telekinesis"))
    W(ul_open())
    W(li("Cooldown decreased from 23/20/17/14s to 22/19/16/13s", b([23, 20, 17, 14], [22, 19, 16, 13], l=True)))
    W(ul_close())

    # Shadow Demon
    W(hero_header("Shadow Demon"))
    W(facet_header("shadow_demon_promulgate"))
    W(ul_open())
    W(li("Disseminate health loss decreased from 9/11/13/15% to 9/10/11/12%", b([9, 11, 13, 15], [9, 10, 11, 12], l=True)))
    W(ul_close())

    # Slardar
    W(hero_header("Slardar"))
    W(ul_open())
    W(li("Strength gain decreased from 3.6 to 3.4", b(3.6, 3.4)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Health decreased from +300 to +250", b(300, 250)))
    W(ul_close())

    # Slark
    W(hero_header("Slark"))
    W(ability("Saltwater Shiv"))
    W(ul_open())
    W(li("Stack Restoration Steal rescaled from 3/4/5/6% to 2/4/6/8%", b([3, 4, 5, 6], [2, 4, 6, 8])))
    W(li("Stack Regen Steal increased from 2/3/4/5 to 2/4/6/8", b([2, 3, 4, 5], [2, 4, 6, 8])))
    W(li("Stack Speed Steal increased from 2/3/4/5 to 2/4/6/8", b([2, 3, 4, 5], [2, 4, 6, 8])))
    W(ul_close())

    # Spectre
    W(hero_header("Spectre"))
    W(ul_open())
    W(li("Strength gain decreased from 2.5 to 2.4", b(2.5, 2.4)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Health decreased from +350 to +325", b(350, 325)))
    W(li("Level 25 Talent All Spectre Illusion Damage decreased from +20% to +15%", b(20, 15)))
    W(ul_close())

    # Terrorblade
    W(hero_header("Terrorblade"))
    W(ability("Conjure Image"))
    W(ul_open())
    W(li("Mana Cost decreased from 55/65/75/85 to 50/60/70/80", b([55, 65, 75, 85], [50, 60, 70, 80], l=True)))
    W(ul_close())
    W(ability("Sunder"))
    W(ul_open())
    W(li("Cooldown decreased from 120/80/40s to 110/75/40s", b([120, 80, 40], [110, 75, 40], l=True)))
    W(ul_close())
    W(ability("Demon Zeal"))
    W(ul_open())
    W(li("No longer affects Reflection illusions", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Reflection Slow/Damage increased from +10% to +15%", b(10, 15)))
    W(ul_close())

    # Tidehunter
    W(hero_header("Tidehunter"))
    W(ul_open())
    W(li("Base Strength decreased from 27 to 26", b(27, 26)))
    W(li("Damage at level 1 decreased from 52–58 to 51–57", br(52, 58, 51, 57)))
    W(ul_close())

    # Timbersaw
    W(hero_header("Timbersaw"))
    W(ul_open())
    W(li("Base Strength decreased from 26 to 23", b(26, 23)))
    W(li("Strength gain increased from 3.5 to 3.6", b(3.5, 3.6)))
    W(li("Damage at level 1 decreased from 49–53 to 46–50", br(49, 53, 46, 50)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Whirling Death Stat Loss decreased from +2.5% to +2%", b(2.5, 2)))
    W(ul_close())

    # Treant Protector
    W(hero_header("Treant Protector"))
    W(ability("Eyes In The Forest"))
    W(ul_open())
    W(li("Eyes now have a 50g bounty when killed", t("NERF")))
    W(ul_close())

    # Ursa
    W(hero_header("Ursa"))
    W(ability("Fury Swipes"))
    W(ul_open())
    W(li("Damage per attack decreased from 13/21/29/37 to 12/20/28/36", b([13, 21, 29, 37], [12, 20, 28, 36])))
    W(ul_close())

    # Viper
    W(hero_header("Viper"))
    W(ability("Corrosive Skin"))
    W(ul_open())
    W(li("Damage per second rescaled from 8/16/24/32 to 10/15/20/25", b([8, 16, 24, 32], [10, 15, 20, 25])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Predator Damage Per Missing Health increased from +0.25 to +0.3", b(0.25, 0.3)))
    W(li("Level 20 Talent Viper Strike DPS decreased from +80 to +70", b(80, 70)))
    W(ul_close())

    write_footer()
    save_html('patches/7.40c.html')

