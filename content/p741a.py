from patch.api import *

def build():
    write_head("7.41a", "28.03.2026")

    # ===== ITEM UPDATES =====
    W(section("Item Updates"))

    W(item_header("Consecrated Wraps"))
    W(ul_open())
    W(li("Magic Resistance bonus decreased from +15% to +12%", b(15, 12)))
    W(li("Hallowed movement speed on stack gain decreased from 20% to 15%", b(20, 15)))
    W(li("Hallowed barrier and movement speed duration decreased from 7s to 5s", b(7, 5)))
    W(ul_close())

    # ===== NEUTRAL ITEM UPDATES =====
    W(section("Neutral Item Updates"))
    W(plain_header("Enchantment changes", dynamics=False))
    W(enchant_header("Crude", "crude"))
    W(ul_open())
    W(li("Base Attack Time Reduction bonus worsened from 8/12/16% to 6/9/12%", b([8, 12, 16], [6, 9, 12])))
    W(ul_close())

    # ===== HERO UPDATES =====
    W(section("Hero Updates"))


    # Alchemist
    W(hero_header("Alchemist"))
    W(ul_open())
    W(li("Base movement speed decreased from 295 to 290", b(295, 290)))
    W(ul_close())
    W(ability("Greevil's Greed", slug="alchemist_goblins_greed"))
    W(ul_open())
    W(li("Max Bonus Gold Per Kill decreased from 18 to 16", b(18, 16)))
    W(li("Bonus Damage per Scepter decreased from +25 to +15", b(25, 15)))
    W(ul_close())

    # Ancient Apparition
    W(hero_header("Ancient Apparition"))
    W(ability("Bone Chill"))
    W(ul_open())
    W(li("Base Strength Reduction increased from 0.1 to 0.2", b(0.1, 0.2)))
    W(ul_close())

    # Anti-Mage
    W(hero_header("Anti-Mage"))
    W(ul_open())
    W(li("Base Movement Speed increased from 310 to 315", b(310, 315)))
    W(li("Base Health Regen increased by 0.5", bstat_h("Anti-Mage", "StatusHealthRegen", "7.41", 0.5), extra=note_box(hero="Anti-Mage", field="StatusHealthRegen", before_patch="7.41")))
    W(ul_close())
    W(ability("Mana Break"))
    W(ul_open())
    W(li("Mana Burned As Damage increased from 50% to 60%", b(50, 60)))
    W(ul_close())

    # Bloodseeker
    W(hero_header("Bloodseeker"))
    W(ability("Bloodrage"))
    W(ul_open())
    W(li("Attack Speed decreased from 60/90/120/150 to 55/80/105/130", b([60, 90, 120, 150], [55, 80, 105, 130])))
    W(li("Aghanim's Shard target's max health as damage decreased from 2% to 1.5%", b(2, 1.5)))
    W(ul_close())

    # Centaur Warrunner
    W(hero_header("Centaur Warrunner"))
    W(ability("Horsepower"))
    W(ul_open())
    W(li("Strength as Bonus Movement Speed increased from 30% to 40%", b(30, 40)))
    W(ul_close())

    # Chaos Knight
    W(hero_header("Chaos Knight"))
    W(ul_open())
    W(li("Base Damage increased by 3", bstat_h("Chaos Knight", "AttackDamageMin", "7.41", 3), extra=note_box(hero="Chaos Knight", field="AttackDamageMin", before_patch="7.41")))
    W(li("Damage at level 1 increased from 53–73 to 56–76", br(53, 73, 56, 76)))
    W(ul_close())

    # Chen
    W(hero_header("Chen"))
    W(ability("Penitence"))
    W(ul_open())
    W(li("Damage increased from 50/75/100/125 to 50/100/150/200", b([50, 75, 100, 125], [50, 100, 150, 200])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Penitence Slow increased from +14% to +15%", b(14, 15)))
    W(ul_close())

    # Clockwerk
    W(hero_header("Clockwerk"))
    W(ability("Power Cogs"))
    W(ul_open())
    W(li("Mana Burn increased from 35/75/115/155 to 40/80/120/160", b([35, 75, 115, 155], [40, 80, 120, 160])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Battery Assault Damage increased from +24 to +25", b(24, 25)))
    W(li("Level 20 Talent Power Cogs Mana Burn increased from +70 to +80", b(70, 80)))
    W(ul_close())

    # Death Prophet
    W(hero_header("Death Prophet"))
    W(ability("Spirit Siphon"))
    W(ul_open())
    W(li("Mana Cost decreased from 80 to 60", b(80, 60, l=True)))
    W(ul_close())

    # Doom
    W(hero_header("Doom"))
    W(ul_open())
    W(li("Base Armor decreased by 1", bstat_h("Doom", "ArmorPhysical", "7.41", -1), extra=note_box(hero="Doom", field="ArmorPhysical", before_patch="7.41")))
    W(ul_close())
    W(ability("Lvl ? Pain", slug="doom_bringer_lvl_pain"))
    W(ul_open())
    W(li("Curse Damage decreased from 15% to 10%", b(15, 10)))
    W(ul_close())

    # Invoker
    W(hero_header("Invoker"))
    W(ul_open())
    W(li("Base Intelligence increased from 20 to 22", b(20, 22)))
    W(li("Damage at level 1 increased from 39–45 to 41–47", br(39, 45, 41, 47)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Tornado Cooldown Reduction increased from 4s to 5s", b(4, 5, l=True)))
    W(ul_close())

    # Io
    W(hero_header("Io"))
    W(ability("Equilibrium"))
    W(ul_open())
    W(li_formula("Max Damage Amp and Max Heal Amplification decreased", "5% + 0.5% per level", "4% + 0.4% per level", lambda L: 5.0 + 0.5*L, lambda L: 4.0 + 0.4*L))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Attack Tethered Ally's Target Damage decreased from 75% to 50%", b(75, 50)))
    W(ul_close())

    # Juggernaut
    W(hero_header("Juggernaut"))
    W(ability("Blade Fury"))
    W(ul_open())
    W(li("Cooldown decreased from 36/30/24/18s to 30/26/22/18s", b([36, 30, 24, 18], [30, 26, 22, 18], l=True)))
    W(ul_close())
    W(ability("Blade Dance"))
    W(ul_open())
    W(li("Critical Damage increased from 130/150/170/190% to 140/160/180/200%", b([130, 150, 170, 190], [140, 160, 180, 200])))
    W(ul_close())

    # Kez
    W(hero_header("Kez"))
    W(ability("Raptor Dance"))
    W(ul_open())
    W(li("Base Damage increased from 30/60/90 to 40/70/100", b([30, 60, 90], [40, 70, 100])))
    W(ul_close())
    W(ability("Raven's Veil"))
    W(ul_open())
    W(li("Buff Duration increased from 7/8/9s to 8/10/12s", b([7, 8, 9], [8, 10, 12])))
    W(ul_close())

    # Legion Commander
    W(hero_header("Legion Commander"))
    W(ability("Outfight Them!", slug="legion_commander_outfight_them"))
    W(ul_open())
    W(li("No longer grants a passive armor bonus before casting abilities", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Duel Duration decreased from +1s to +0.75s", b(1, 0.75)))
    W(li("Level 25 Talent Moment of Courage Lifesteal increased from +75% to +100%", b(75, 100)))
    W(ul_close())

    # Leshrac
    W(hero_header("Leshrac"))
    W(ul_open())
    W(li("Strength gain decreased from 2.8 to 2.5", b(2.8, 2.5)))
    W(ul_close())
    W(ability("Diabolic Edict"))
    W(ul_open())
    W(li("Damage per explosion decreased from 10/18/26/34 to 9/16/23/30", b([10, 18, 26, 34], [9, 16, 23, 30])))
    W(ul_close())

    # Lifestealer
    W(hero_header("Lifestealer"))
    W(ul_open())
    W(li("Base Damage decreased by 3", bstat_h("Lifestealer", "AttackDamageMin", "7.41", -3), extra=note_box(hero="Lifestealer", field="AttackDamageMin", before_patch="7.41")))
    W(li("Damage at level 1 decreased from 49–55 to 46–52", br(49, 55, 46, 52)))
    W(ul_close())
    W(ability("Ghoul Frenzy"))
    W(ul_open())
    W(li_formula("Bonus Attack Speed decreased", "5 per level", "4 per level", lambda L: 5.0*L, lambda L: 4.0*L))
    W(ul_close())
    W(ability("Rage"))
    W(ul_open())
    W(li("Movespeed Bonus decreased from 9/12/15/18% to 6/9/12/15%", b([9, 12, 15, 18], [6, 9, 12, 15])))
    W(ul_close())
    W(ability("Feast"))
    W(ul_open())
    W(li("Max HP per Hero Kill decreased from 10/15/20/25 to 10", b([10, 15, 20, 25], 10)))
    W(ul_close())

    # Meepo
    W(hero_header("Meepo"))
    W(ability("Divided We Stand"))
    W(ul_open())
    W(li("Evasion no longer diminishes when shared between Meepos and has full strength on each", t("BUFF")))
    W(li("Clones can no longer copy Bottle", t("NERF")))
    W(ul_close())

    # Mirana
    W(hero_header("Mirana"))
    W(ability("Celestial Quiver"))
    W(ul_open())
    W(li_formula("Bonus Damage changed", "3 per level", "5 + 3 per level", lambda L: 3.0*L, lambda L: 5.0 + 3.0*L))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Celestial Quiver Damage increased from +35 to +40", b(35, 40)))
    W(ul_close())

    # Morphling
    W(hero_header("Morphling"))
    W(ul_open())
    W(li("Agility gain increased from 3.9 to 4.2", b(3.9, 4.2)))
    W(ul_close())

    # Muerta
    W(hero_header("Muerta"))
    W(ability("The Calling"))
    W(ul_open())
    W(li("Cooldown decreased from 30s to 30/28/26/24s", b(30, [30, 28, 26, 24], l=True)))
    W(ul_close())
    W(ability("Pierce the Veil"))
    W(ul_open())
    W(li("Base Damage Bonus rescaled from 75% to 70/85/100%", b(75, [70, 85, 100])))
    W(ul_close())

    # Oracle
    W(hero_header("Oracle"))
    W(ability("Fortune's End"))
    W(ul_open())
    W(li("Mana Cost decreased from 100 to 80", b(100, 80, l=True)))
    W(ul_close())

    # Pangolier
    W(hero_header("Pangolier"))
    W(ability("Rolling Thunder", slug="pangolier_gyroshell"))
    W(ul_open())
    W(li("Cooldown increased from 90/85/80s to 100/90/80s", b([90, 85, 80], [100, 90, 80], l=True)))
    W(ul_close())

    # Phantom Lancer
    W(hero_header("Phantom Lancer"))
    W(ability("Spirit Lance"))
    W(ul_open())
    W(li("Slow Duration decreased from 3.75s to 3s", b(3.75, 3)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Spirit Lance Slow Duration decreased from +1.25s to +1s", b(1.25, 1)))
    W(ul_close())

    # Primal Beast
    W(hero_header("Primal Beast"))
    W(ability("Colossal"))
    W(ul_open())
    W(li("Now slightly grows in size when crossing an HP threshold", t("MISC")))
    W(ul_close())

    # Puck
    W(hero_header("Puck"))
    W(ability("Illusory Orb"))
    W(ul_open())
    W(li("Impact Damage decreased from 75/150/225/300 to 70/140/210/280", b([75, 150, 225, 300], [70, 140, 210, 280])))
    W(ul_close())

    # Slark
    W(hero_header("Slark"))
    W(ability("Shadow Dance"))
    W(ul_open())
    W(li("Bonus Movement Speed decreased from 24/36/48% to 20/30/40%", b([24, 36, 48], [20, 30, 40])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent +1 Agility gain/stolen per Essence Shift Stack replaced with +25s Essence Shift Duration", t("REWORK")))
    W(li("Level 25 Talent +35s Essence Shift Duration replaced with +1 Agility gain/stolen per Essence Shift Stack", t("REWORK")))
    W(ul_close())

    # Spectre
    W(hero_header("Spectre"))
    W(ability("Spectral Dagger"))
    W(ul_open())
    W(li("Damage rescaled from 70/120/170/220 to 80/120/160/200", b([70, 120, 170, 220], [80, 120, 160, 200])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Health decreased from +325 to +300", b(325, 300)))
    W(li("Level 25 Talent Dispersion decreased from +5% to +4%", b(5, 4)))
    W(ul_close())

    # Spirit Breaker
    W(hero_header("Spirit Breaker"))
    W(ability("Greater Bash"))
    W(ul_open())
    W(li("Aghanim's Scepter upgrade unit collision radius no longer affected by Area of Effect bonuses", t("NERF")))
    W(ul_close())

    # Techies
    W(hero_header("Techies"))
    W(ability("Proximity Mines", slug="techies_land_mines"))
    W(ul_open())
    W(li("Damage decreased from 450/575/750 to 400/550/700", b([450, 575, 750], [400, 550, 700])))
    W(li("Portion of damage dealt on the edge of AoE decreased from 60% to 50%", b(60, 50)))
    W(li("Minimum Damage decreased from 240/345/450 to 200/225/350", b([240, 345, 450], [200, 225, 350])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Proximity Mines Cooldown Reduction decreased from 3s to 2s", b(3, 2, l=True)))
    W(ul_close())

    # Tidehunter
    W(hero_header("Tidehunter"))
    W(ability("Leviathan's Catch"))
    W(ul_open())
    W(li("Fish spawn launch distance decreased from 400 to 200", b(400, 200)))
    W(ul_close())

    # Timbersaw
    W(hero_header("Timbersaw"))
    W(ability("Exposure Therapy"))
    W(ul_open())
    W(li_formula("Mana Restore increased", "3.75 + 0.25 per level", "4 + 0.5 per level", lambda L: 3.75 + 0.25*L, lambda L: 4.0 + 0.5*L))
    W(ul_close())
    W(ability("Chakram"))
    W(ul_open())
    W(li("Mana Cost decreased from 100/140/180 to 90/120/150", b([100, 140, 180], [90, 120, 150], l=True)))
    W(li("Mana Cost per second decreased from 14/22/30 to 10/15/20", b([14, 22, 30], [10, 15, 20], l=True)))
    W(ul_close())

    # Tinker
    W(hero_header("Tinker"))
    W(ability("Deploy Turrets"))
    W(ul_open())
    W(li("Tinker Knockback increased from 350 to 400", b(350, 400)))
    W(ul_close())

    # Tiny
    W(hero_header("Tiny"))
    W(ability("Tree Grab"))
    W(ul_open())
    W(li("Number of Attacks increased from 4/5/6/7 to 5/6/7/8", b([4, 5, 6, 7], [5, 6, 7, 8])))
    W(ul_close())
    W(ability("Grow"))
    W(ul_open())
    W(li("Bonus Damage increased from 55/110/165 to 60/120/180", b([55, 110, 165], [60, 120, 180])))
    W(li("Movement Speed Bonus increased from 10/15/20 to 10/20/30", b([10, 15, 20], [10, 20, 30])))
    W(ul_close())

    # Void Spirit
    W(hero_header("Void Spirit"))
    W(ul_open())
    W(li("Base Mana Regen decreased by 0.6", bstat_h("Void Spirit", "StatusManaRegen", "7.41", -0.6), extra=note_box(hero="Void Spirit", field="StatusManaRegen", before_patch="7.41")))
    W(ul_close())

    # Windranger
    W(hero_header("Windranger"))
    W(ul_open())
    W(li("Base Agility increased from 17 to 20", b(17, 20)))
    W(li("Damage at level 1 increased from 47–59 to 49–61", br(47, 59, 49, 61)))
    W(ul_close())
    W(ability("Tailwind"))
    W(ul_open())
    W(li("Duration increased from 2s to 2.5s", b(2, 2.5)))
    W(li("Aghanim's Scepter bonus is still +1s, so it's increased to 3.5s", t("BUFF")))
    W(ul_close())
    W(ability("Focus Fire", slug="windrunner_focusfire"))
    W(ul_open())
    W(li("Cooldown decreased from 70/50/30s to 50/40/30s", b([70, 50, 30], [50, 40, 30], l=True)))
    W(ul_close())

    # Wraith King
    W(hero_header("Wraith King"))
    W(ul_open())
    W(li("Base Attack Time worsened from 1.7s to 1.8s", b(1.7, 1.8, l=True)))
    W(li("Intelligence gain decreased from 1.6 to 1.4", b(1.6, 1.4)))
    W(ul_close())
    W(ability("Bone Guard"))
    W(ul_open())
    W(li("Skeleton Duration decreased from 46s to 40s", b(46, 40)))
    W(ul_close())
    W(ability("Mortal Strike"))
    W(ul_open())
    W(li("Cooldown rescaled from 6/5.5/5/4.5s to 5s", b([6, 5.5, 5, 4.5], 5, l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Health decreased from +350 to +300", b(350, 300)))
    W(li("Level 15 Talent Wraithfire Blast Stun Duration decreased from +1s to +0.75s", b(1, 0.75)))
    W(ul_close())

    write_footer()
    save_html('patches/7.41a.html')

