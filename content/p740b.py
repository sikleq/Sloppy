from patch.api import *

def build():
    write_head("7.40b", "23.12.2025")

    # ===== ITEM UPDATES =====
    W(section("Item Updates"))

    W(item_header("Mask of Madness"))
    W(ul_open())
    W(li("Berserk now shows the overhead \"Silenced\" text when active", t("QoL")))
    W(ul_close())

    W(item_header("Silver Edge"))
    W(ul_open())
    W(li("Shadow Walk debuff duration decreased from 6s to 5s", b(6, 5)))
    W(ul_close())

    W(item_header("Spirit Vessel"))
    W(ul_open())
    W(li("Soul Release will gain charges only for Spirit Vessel if the same hero has both Spirit Vessel and Urn of Shadows", t("MISC")))
    W(ul_close())

    W(item_header("Urn of Shadows"))
    W(ul_open())
    W(li("Soul Release can no longer gain charges on multiple copies of this item if the copies are on the same hero", t("MISC")))
    W(ul_close())

    # ===== HERO UPDATES =====
    W(section("Hero Updates"))

    # Abaddon
    W(hero_header("Abaddon"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Aphotic Shield HP Regen decreased from +10 to +8", b(10, 8)))
    W(ul_close())

    # Axe
    W(hero_header("Axe"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Battle Hunger Damage Per Second decreased from +12 to +10", b(12, 10)))
    W(ul_close())

    # Batrider
    W(hero_header("Batrider"))
    W(ability("Flamebreak", slug="batrider_flamebreak"))
    W(ul_open())
    W(li("Mana Cost decreased from 110/115/120/125 to 110", b([110, 115, 120, 125], 110, l=True)))
    W(ul_close())

    # Beastmaster
    W(hero_header("Beastmaster"))
    W(ul_open())
    W(li("Agility gain increased from 1.9 to 2.0", b(1.9, 2)))
    W(li("Damage gain per level increased from 3.0 to 3.1", b(3, 3.1)))
    W(ul_close())
    W(ability("Wild Axes", slug="beastmaster_wild_axes"))
    W(ul_open())
    W(li("Damage Amp per stack increased from 6/8/10/12% to 7/9/11/13%", b([6, 8, 10, 12], [7, 9, 11, 13])))
    W(ul_close())

    # Brewmaster
    W(hero_header("Brewmaster"))
    W(ul_open())
    W(li("Base Strength increased from 23 to 24", b(23, 24)))
    W(li("Damage at level 1 increased from 52–59 to 53–60", br(52, 59, 53, 60)))
    W(ul_close())
    W(ability("Liquid Courage", slug="brewmaster_liquid_courage"))
    W(ul_open())
    W(li("Max Speed Increase increased from 25% to 30%", b(25, 30)))
    W(ul_close())
    W(ability("Thunder Clap", slug="brewmaster_thunder_clap"))
    W(ul_open())
    W(li("Radius increased from 375 to 400", b(375, 400)))
    W(ul_close())
    W(ability("Drunken Brawler", slug="brewmaster_drunken_brawler"))
    W(ul_open())
    W(li("Brewed Up extend duration increased from 1s to 2s", b(1, 2)))
    W(li("Toggling is no longer disabled by silence", t("MISC")))
    W(ul_close())
    W(ability("Primal Split", slug="brewmaster_primal_split"))
    W(ul_open())
    W(li("Earth Brewling's Earth Element now also provides 80% Slow Resistance", t("NEW")))
    W(ul_close())

    # Bristleback
    W(hero_header("Bristleback"))
    W(ability("Viscous Nasal Goo", slug="bristleback_viscous_nasal_goo"))
    W(ul_open())
    W(li("Base Movement Slow increased from 10% to 12%", b(10, 12)))
    W(ul_close())

    # Broodmother
    W(hero_header("Broodmother"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Incapacitating Bite Attack Bonus decreased from +10 to +8", b(10, 8)))
    W(li("Level 20 Talent Incapacitating Bite Slow/Miss Chance decreased from +25% to +20%", b(25, 20)))
    W(li("Level 25 Talent Spin Web Move Speed decreased from +14% to +7%", b(14, 7)))
    W(li("Level 25 Talent BAT Reduction During Insatiable Hunger decreased from 0.25s to 0.2s", b(0.25, 0.2)))
    W(ul_close())

    # Centaur Warrunner
    W(hero_header("Centaur Warrunner"))
    W(ul_open())
    W(li("Base Movement Speed decreased from 305 to 300", b(305, 300)))
    W(ul_close())
    W(ability("Work Horse", slug="centaur_work_horse"))
    W(ul_open())
    W(li("Total Duration decreased from 7s to 6s", b(7, 6)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Strength decreased from +12 to +10", b(12, 10)))
    W(ul_close())

    # Clinkz
    W(hero_header("Clinkz"))
    W(ul_open())
    W(li("Base Strength increased from 17 to 18", b(17, 18)))
    W(ul_close())
    W(ability("Infernal Shred", slug="clinkz_infernal_shred"))
    W(ul_open())
    W(li("Debuff per Clinkz' attack increased from 2% to 3%", b(2, 3)))
    W(ul_close())
    W(ability("Strafe", slug="clinkz_strafe"))
    W(ul_open())
    W(li("Now also applies to skeletons that were created after the cast", t("NEW")))
    W(li("Attack Speed Bonus increased from 100/140/180/220 to 120/160/200/240", b([100, 140, 180, 220], [120, 160, 200, 240])))
    W(ul_close())
    W(ability("Searing Arrows", slug="clinkz_searing_arrows"))
    W(ul_open())
    W(li("Bonus Damage increased from 18/32/46/60 to 20/35/50/65", b([18, 32, 46, 60], [20, 35, 50, 65])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +1 Death Pact Charge replaced with -10s Death Pact Charge Restore Time", t("REWORK")))
    W(ul_close())

    # Dazzle
    W(hero_header("Dazzle"))
    W(ability("Poison Touch", slug="dazzle_poison_touch"))
    W(ul_open())
    W(li("Slow decreased from 16/18/20/22% to 13/16/19/22%", b([16, 18, 20, 22], [13, 16, 19, 22])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Shallow Grave Cooldown Reduction decreased from 4s to 3s", b(4, 3, l=True)))
    W(ul_close())

    # Death Prophet
    W(hero_header("Death Prophet"))
    W(ability("Exorcism", slug="death_prophet_exorcism"))
    W(ul_open())
    W(li("Spirits increased from 10/17/24 to 10/18/26", b([10, 17, 24], [10, 18, 26])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Spirit Siphon Damage/Heal increased from +25 to +30", b(25, 30)))
    W(ul_close())

    # Doom
    W(hero_header("Doom"))
    W(ul_open())
    W(li("Strength gain increased from 3.5 to 3.6", b(3.5, 3.6)))
    W(ul_close())

    # Drow Ranger
    W(hero_header("Drow Ranger"))
    W(ul_open())
    W(li("Agility gain decreased from 2.9 to 2.8", b(2.9, 2.8)))
    W(ul_close())
    W(facet_header("drow_ranger_sidestep"))
    W(ul_open())
    W(li("Multishot: Movement speed penalty increased from 25% to 35%", b(25, 35, l=True)))
    W(ul_close())
    W(ul_open())
    W(li("Glacier: Cooldown increased from 20s to 25s", b(20, 25, l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Frost Arrows Mana Cost Reduction decreased from 25% to 18%", b(25, 18, l=True)))
    W(ul_close())

    # Enigma
    W(hero_header("Enigma"))
    W(ability("Black Hole", slug="enigma_black_hole"))
    W(ul_open())
    W(li("Aghanim's Scepter Pull AoE decreased from 1200 to 1000", b(1200, 1000)))
    W(ul_close())

    # Faceless Void
    W(hero_header("Faceless Void"))
    W(ul_open())
    W(li("Base Damage decreased by 3", t("MISC")))
    W(li("Base Agility increased from 21 to 24", b(21, 24), extra=inline_note("Damage at level 1 unchanged (58–64)")))
    W(ul_close())

    # Huskar
    W(hero_header("Huskar"))
    W(facet_header("huskar_cauterize"))
    W(ul_open())
    W(li("Berserker's Blood: Max HP heal per debuff decreased from 5% to 4%", b(5, 4)))
    W(ul_close())
    W(ul_open())
    W(li("Berserker's Blood: HP for Max bonus decreased from 12% to 10%", b(12, 10)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Lifesteal decreased from +15% to +12%", b(15, 12)))
    W(li("Level 25 Talent Life Break Damage decreased from +25% to +22%", b(25, 22)))
    W(ul_close())

    # Invoker
    W(hero_header("Invoker"))
    W(facet_header("invoker_wex_focus"))
    W(ul_open())
    _twister_old = [3.2, 3.4, 3.6, 3.8, 4.0, 4.2, 4.4, 4.6, 4.8, 5.0]
    _twister_new = [2.7, 2.9, 3.1, 3.3, 3.5, 3.7, 3.9, 4.1, 4.3, 4.5]
    W(li_formula(
        "Tornado Aghanim's Scepter Twister Duration decreased by 0.5s",
        "3.2-5.0s", "2.7-4.5s",
        lambda L, o=_twister_old: o[L - 1],
        lambda L, n=_twister_new: n[L - 1],
        levels=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        level_prefix='W',
        rework_badge=False,
        value_fmt="{:.1f}s",
    ))
    W(li("E.M.P. Aghanim's Shard burn damage decreased from 90% to 80%", b(90, 80)))
    W(ul_close())

    # Jakiro
    W(hero_header("Jakiro"))
    W(ability("Liquid Fire", slug="jakiro_liquid_fire"))
    W(ul_open())
    W(li("Burn Damage decreased from 20/30/40/50 to 15/25/35/45", b([20, 30, 40, 50], [15, 25, 35, 45])))
    W(ul_close())
    W(ability("Liquid Frost", slug="jakiro_liquid_ice"))
    W(ul_open())
    W(li("Impact Damage rescaled from 15/20/25/30 to 8/16/24/32", b([15, 20, 25, 30], [8, 16, 24, 32])))
    W(ul_close())

    # Juggernaut
    W(hero_header("Juggernaut"))
    W(ability("Healing Ward", slug="juggernaut_healing_ward"))
    W(ul_open())
    W(li("Duration decreased from 25s to 18/20/22/24s", b(25, [18, 20, 22, 24])))
    W(ul_close())
    W(ability("Omnislash", slug="juggernaut_omni_slash"))
    W(ul_open())
    W(li("Slashes Rate Multiplier decreased from 1.5 to 1.4", b(1.5, 1.4, l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Blade Dance Lifesteal decreased from +50% to +40%", b(50, 40)))
    W(ul_close())

    # Kez
    W(hero_header("Kez"))
    W(ability("Switch Discipline", slug="kez_switch_weapons"))
    W(ul_open())
    W(li("Katana Base Attack Time worsened from 1.8s to 1.9s", b(1.8, 1.9, l=True)))
    W(li("Katana Bonus Agility Base Damage increased from 12% to 16%", b(12, 16)))
    W(li("Can no longer be disabled by Silence", t("MISC")))
    W(ul_close())
    W(ability("Falcon Rush", slug="kez_falcon_rush"))
    W(ul_open())
    W(li("Can no longer rush towards buildings or trigger on them", t("DEL")))
    W(li("Echo Attack Damage decreased from 35/40/45/50% to 30/35/40/45%", b([35, 40, 45, 50], [30, 35, 40, 45])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Attack Speed During Falcon Rush decreased from +60 to +40", b(60, 40)))
    W(ul_close())

    # Kunkka
    W(hero_header("Kunkka"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Tidebringer Cleave Damage increased from +120% to +130%", b(120, 130)))
    W(ul_close())

    # Largo
    W(hero_header("Largo"))
    W(ability("Catchy Lick", slug="largo_catchy_lick"))
    W(ul_open())
    W(li("Enemy Pull Distance increased from 210/240/270/300 to 235/265/295/325", b([210, 240, 270, 300], [235, 265, 295, 325])))
    W(li("Bonus Health Regen increased from 4/6/8/10 to 4/7/10/13", b([4, 6, 8, 10], [4, 7, 10, 13])))
    W(ul_close())
    W(ability("Croak of Genius", slug="largo_croak_of_genius"))
    W(ul_open())
    W(li("Reverberated damage is now only applied if the target is within 2000 range of the caster", t("REWORK")))
    W(li("Duration is no longer decreased on Largo from his own abilities", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Catchy Lick Damage increased from +140 to +170", b(140, 170)))
    W(ul_close())

    # Legion Commander
    W(hero_header("Legion Commander"))
    W(facet_header("legion_commander_spoils_of_war"))
    W(ul_open())
    W(li("Press the Attack: Duration on allies after Duel win decreased from 50% to 25%", b(50, 25),
         extra=inline_note("From 2.5s to 1.25s")))
    W(ul_close())
    W(ul_open())
    W(li("Press The Attack: Mana Cost decreased from 100 to 90", b(100, 90, l=True)))
    W(li("Bonus Move Speed increased from 10/14/18/22% to 13/16/19/22%", b([10, 14, 18, 22], [13, 16, 19, 22])))
    W(ul_close())
    W(ul_open())
    W(li("Duel: Aghanim's Scepter duration bonus decreased from +2s to +1.5s", b(2, 1.5),
         extra=inline_note("Total Duration decreased from 6/6.5/7s to 5.5/6/6.5s")))
    W(ul_close())

    # Lich
    W(hero_header("Lich"))
    W(ul_open())
    W(li("Agility gain decreased from 2.0 to 1.7", b(2, 1.7)))
    W(ul_close())

    # Lone Druid
    W(hero_header("Lone Druid"))
    W(ul_open())
    W(li("Base Strength increased from 18 to 20", b(18, 20)))
    W(li("Base Movement Speed increased from 295 to 300", b(295, 300)))
    W(ul_close())
    W(ability("Entangle", slug="lone_druid_entangle"))
    W(ul_open())
    W(li("Root Damage per second increased from 60/70/80/90 to 90", b([60, 70, 80, 90], 90)))
    W(li("Cooldown decreased from 24/22/20/18s to 20/19/18/17s", b([24, 22, 20, 18], [20, 19, 18, 17], l=True)))
    W(ul_close())
    W(ability("Savage Roar", slug="lone_druid_savage_roar"))
    W(ul_open())
    W(li("Cooldown decreased from 38/32/26/20s to 29/26/23/20s", b([38, 32, 26, 20], [29, 26, 23, 20], l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Entangle Root Damage Per Second increased from +15 to +20", b(15, 20)))
    W(ul_close())
    # Spirit Bear (Lone Druid pet — unit, not a hero). Placed inside LD's
    # section, mirroring 7.41c convention. Gold + Experience bounty share
    # the same formula change, so they merge into one combined row.
    W(unit_header("Spirit Bear", "../icons/abilities/lone_druid_spirit_bear.png", kind="Creep-hero"))
    W(ul_open())
    W(li_formula("Gold/Experience Bounty changed",
                 "300", "175 + 8 per Spirit Bear level up",
                 lambda L: 300, lambda L: 175 + 8 * L,
                 levels=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 25, 30],
                 l=True,
                 rework_badge=False))
    W(ul_close())
    W(ability("Entangling Claws", slug="lone_druid_spirit_bear_entangle"))
    W(ul_open())
    W(li("Root Damage per second increased from 60/70/80/90 to 90", b([60, 70, 80, 90], 90)))
    W(ul_close())

    # Marci
    W(hero_header("Marci"))
    W(ul_open())
    W(li("Strength gain increased from 3.0 to 3.2", b(3, 3.2)))
    W(li("Damage gain per level increased from 3.2 to 3.3", b(3.2, 3.3)))
    W(ul_close())
    W(ability("Rebound", slug="marci_companion_run"))
    W(ul_open())
    W(li("Radius increased from 275 to 300", b(275, 300)))
    W(ul_close())
    W(ability("Unleash", slug="marci_unleash"))
    W(ul_open())
    W(li("Cooldown decreased from 90/75/60s to 80/70/60s", b([90, 75, 60], [80, 70, 60], l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +75 Rebound Landing Radius decreased to +50", t("NERF")))
    W(ul_close())

    # Mars
    W(hero_header("Mars"))
    W(ul_open())
    W(li("Base Agility decreased from 20 to 18", b(20, 18)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent God's Rebuke Cooldown Reduction increased from 2s to 2.5s", b(2, 2.5, l=True)))
    W(li("Level 20 Talent Spear of Mars Stun increased from +0.4 to +0.5s", b(0.4, 0.5)))
    W(ul_close())

    # Meepo
    W(hero_header("Meepo"))
    W(ability("Dig", slug="meepo_petrify"))
    W(ul_open())
    W(li("Now has a 0.3s cast point", t("NEW")))
    W(ul_close())
    W(ability("MegaMeepo", slug="meepo_megameepo"))
    W(ul_open())
    W(li("Poof damage factor per additional Meepo decreased from 100% to 75%", b(100, 75)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Poof Cast Duration Reduction decreased from 1s to 0.75s", b(1, 0.75)))
    W(ul_close())

    # Monkey King
    W(hero_header("Monkey King"))
    W(ability("Wukong's Command", slug="monkey_king_wukongs_command"))
    W(ul_open())
    W(li("Duration increased from 13s to 14s", b(13, 14)))
    W(li("Aghanim's Scepter Soldier Duration increased from 12s to 15s", b(12, 15)))
    W(ul_close())

    # Morphling
    W(hero_header("Morphling"))
    W(ul_open())
    W(li("Base armor increased by 1", t("BUFF")))
    W(ul_close())

    # Muerta
    W(hero_header("Muerta"))
    W(ability("Gunslinger", slug="muerta_gunslinger"))
    W(ul_open())
    W(li("Toggling is no longer disabled by silence", t("MISC")))
    W(ul_close())

    # Necrophos
    W(hero_header("Necrophos"))
    W(ability("Ghost Shroud", slug="necrolyte_ghost_shroud"))
    W(ul_open())
    W(li("Restoration Amplification rescaled from 45/55/65/75% to 55/60/65/70%", b([45, 55, 65, 75], [55, 60, 65, 70])))
    W(ul_close())

    # Omniknight
    W(hero_header("Omniknight"))
    W(ability("Repel", slug="omniknight_martyr"))
    W(ul_open())
    W(li("Bonus Strength decreased from 7/14/21/28 to 6/12/18/24", b([7, 14, 21, 28], [6, 12, 18, 24])))
    W(ul_close())

    # Outworld Destroyer
    W(hero_header("Outworld Destroyer"))
    W(ability("Sanity's Eclipse", slug="obsidian_destroyer_sanity_eclipse"))
    W(ul_open())
    W(li("No longer deals bonus damage to illusions", t("DEL")))
    W(ul_close())
    W(ability("Essence Flux", slug="obsidian_destroyer_equilibrium", innate=False))
    W(ul_open())
    W(li("Aghanim's Scepter barrier duration decreased from 15s to 12s", b(15, 12)))
    W(ul_close())

    # Pangolier
    W(hero_header("Pangolier"))
    W(ul_open())
    W(li("Intelligence gain increased from 2.2 to 2.5", b(2.2, 2.5)))
    W(li("Damage gain per level increased from 3.6 to 3.8", b(3.6, 3.8)))
    W(li("Base Movement Speed increased from 295 to 300", b(295, 300)))
    W(ul_close())
    W(ability("Swashbuckle", slug="pangolier_swashbuckle"))
    W(ul_open())
    W(li("Cast Range and Dash Range increased from 400/500/600/700 to 575/650/725/800", b([400, 500, 600, 700], [575, 650, 725, 800])))
    W(li("Slash Range increased from 700 to 850", b(700, 850)))
    W(li("Damage per Strike increased from 30/60/90/120 to 35/65/95/125", b([30, 60, 90, 120], [35, 65, 95, 125])))
    W(ul_close())
    W(ability("Shield Crash", slug="pangolier_shield_crash"))
    W(ul_open())
    W(li("Cooldown decreased from 16/13/10/7s to 15/12/9/6s", b([16, 13, 10, 7], [15, 12, 9, 6], l=True)))
    W(ul_close())
    W(ability("Rolling Thunder", slug="pangolier_gyroshell"))
    W(ul_open())
    W(li("Duration increased from 9/10/11s to 10/11/12s", b([9, 10, 11], [10, 11, 12])))
    W(li("Damage increased from 75/150/225 to 100/200/300", b([75, 150, 225], [100, 200, 300])))
    W(li("Magic Resistance increased from 60% to 80%", b(60, 80)))
    W(ul_close())
    W(ability("Roll Up", slug="pangolier_rollup"))
    W(ul_open())
    W(li("Magic Resistance increased from 60% to 80%", b(60, 80)))
    W(ul_close())

    # Phantom Assassin
    W(hero_header("Phantom Assassin"))
    W(ability("Fan of Knives", slug="phantom_assassin_fan_of_knives"))
    W(ul_open())
    W(li("Now pierces Debuff Immunity", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Phantom Strike Duration increased from +0.5s to +0.6s", b(0.5, 0.6)))
    W(ul_close())

    # Phantom Lancer
    W(hero_header("Phantom Lancer"))
    W(ability("Spirit Lance", slug="phantom_lancer_spirit_lance"))
    W(ul_open())
    W(li("Damage increased from 70/140/210/280 to 100/160/220/280", b([70, 140, 210, 280], [100, 160, 220, 280])))
    W(ul_close())
    W(ability("Phantom Rush", slug="phantom_lancer_phantom_edge"))
    W(ul_open())
    W(li("Toggling is no longer disabled by silence", t("MISC")))
    W(ul_close())

    # Primal Beast
    W(hero_header("Primal Beast"))
    W(ability("Onslaught", slug="primal_beast_onslaught"))
    W(ul_open())
    W(li("Stun Duration rescaled from 0.8/1/1.2/1.4s to 0.7/1/1.3/1.6s", b([0.8, 1, 1.2, 1.4], [0.7, 1, 1.3, 1.6])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Basic Self-Dispel on Uproar Cast replaced with +6 Uproar Armor Per Stack", t("REWORK")))
    W(li("Level 20 Talent +7 Uproar Armor Per Stack replaced with Basic Self-Dispel on Uproar Cast", t("REWORK")))
    W(ul_close())

    # Pudge
    W(hero_header("Pudge"))
    W(facet_header("pudge_fresh_meat"))
    W(ul_open())
    W(li("Dismember: Strength increase decreased from 2/4/6 to 2/3/4", b([2, 4, 6], [2, 3, 4])))
    W(ul_close())
    W(ul_open())
    W(li("Meat Hook: Mana Cost increased from 110 to 120", b(110, 120, l=True)))
    W(ul_close())

    # Pugna
    W(hero_header("Pugna"))
    W(ability("Life Drain", slug="pugna_life_drain"))
    W(ul_open())
    W(li("Mana Cost increased from 100/150/200 to 115/160/205", b([100, 150, 200], [115, 160, 205], l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Health decreased from +300 to +250", b(300, 250)))
    W(ul_close())

    # Riki
    W(hero_header("Riki"))
    W(ability("Tricks of the Trade", slug="riki_tricks_of_the_trade"))
    W(ul_open())
    W(li("Attack Damage rescaled from 30/50/70/90 to 25/50/75/100", b([30, 50, 70, 90], [25, 50, 75, 100])))
    W(ul_close())

    # Ringmaster
    W(hero_header("Ringmaster"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Impalement Arts Impact Damage increased from +75 to +85", b(75, 85)))
    W(ul_close())

    # Shadow Demon
    W(hero_header("Shadow Demon"))
    W(ability("Disseminate", slug="shadow_demon_disseminate"))
    W(ul_open())
    W(li("Cast Range decreased from 700/800/900/1000 to 700/775/850/925", b([700, 800, 900, 1000], [700, 775, 850, 925])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Strength decreased from +10 to +8", b(10, 8)))
    W(ul_close())

    # Shadow Fiend
    W(hero_header("Shadow Fiend"))
    W(ability("Necromastery", slug="nevermore_necromastery"))
    W(ul_open())
    W(li("Base Max Souls increased from 20 to 20/22/24/26", b(20, [20, 22, 24, 26])))
    W(li("No longer upgraded with Aghanim's Scepter", t("DEL")))
    W(ul_close())
    W(ability("Requiem of Souls", slug="nevermore_requiem"))
    W(ul_open())
    W(li("Magic Resist Reduction rescaled from 5/10/15% to 10%", b([5, 10, 15], 10)))
    W(ul_close())

    # Silencer
    W(hero_header("Silencer"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Attack Speed increased from +20 to +25", b(20, 25)))
    W(ul_close())

    # Slark
    W(hero_header("Slark"))
    W(ability("Saltwater Shiv", slug="slark_saltwater_shiv"))
    W(ul_open())
    W(li("Duration increased from 6/8/10/12s to 12s", b([6, 8, 10, 12], 12)))
    W(li("Stack Regen Steal rescaled from 3 to 2/3/4/5", b(3, [2, 3, 4, 5])))
    W(li("Stack Speed Steal rescaled from 3 to 2/3/4/5", b(3, [2, 3, 4, 5])))
    W(ul_close())

    # Spectre
    W(hero_header("Spectre"))
    W(ul_open())
    W(li("Base Agility increased from 25 to 26", b(25, 26)))
    W(li("Damage at level 1 increased from 48–52 to 49–53", br(48, 52, 49, 53)))
    W(li("Agility gain increased from 2.1 to 2.4", b(2.1, 2.4)))
    W(ul_close())
    W(ability("Shadow Step", slug="spectre_shadow_step"))
    W(ul_open())
    W(li("Cooldown decreased from 32/28/24/20s to 30/26/22/18s", b([32, 28, 24, 20], [30, 26, 22, 18], l=True)))
    W(li("Cast Range increased from 700/850/1000/1150 to 750/900/1050/1200", b([700, 850, 1000, 1150], [750, 900, 1050, 1200])))
    W(li("Illusion Damage increased from 20/30/40/50% to 32/38/44/50%", b([20, 30, 40, 50], [32, 38, 44, 50])))
    W(ul_close())
    W(ability("Dispersion", slug="spectre_dispersion"))
    W(ul_open())
    W(li("Damage Reflected increased from 7/11/15/19% to 8/12/16/20%", b([7, 11, 15, 19], [8, 12, 16, 20])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Desolate Damage increased from +10 to +12", b(10, 12)))
    W(ul_close())

    # Techies
    W(hero_header("Techies"))
    W(ability("Proximity Mines", slug="techies_land_mines"))
    W(ul_open())
    W(li("Cast range increased from 400 to 450", b(400, 450)))
    W(ul_close())

    # Terrorblade
    W(hero_header("Terrorblade"))
    W(ul_open())
    W(li("Base agility increased from 22 to 23", b(22, 23)))
    W(li("Damage at level 1 increased from 48–54 to 49–55", br(48, 54, 49, 55)))
    W(ul_close())
    W(ability("Metamorphosis", slug="terrorblade_metamorphosis"))
    W(ul_open())
    W(li("Cooldown decreased from 155/150/145/140s to 145/140/135/130s", b([155, 150, 145, 140], [145, 140, 135, 130], l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Metamorphosis Cooldown Reduction decreased from 20s to 10s", b(20, 10, l=True)))
    W(ul_close())

    # Tidehunter
    W(hero_header("Tidehunter"))
    W(ability("Dead in the Water", slug="tidehunter_dead_in_the_water"))
    W(ul_open())
    W(li("No longer deals 100 damage", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Anchor Smash Damage Reduction decreased from +20% to +10%", b(20, 10)))
    W(li("Level 20 Talent Blubber effect triggers Anchor Smash now deals 50% less damage on the triggered Anchor Smash and is now considered reflection damage", t("NERF")))
    W(ul_close())

    # Timbersaw
    W(hero_header("Timbersaw"))
    W(ability("Whirling Death", slug="shredder_whirling_death"))
    W(ul_open())
    W(li("Stat Loss Duration decreased from 12/13/14/15s to 11/12/13/14s", b([12, 13, 14, 15], [11, 12, 13, 14])))
    W(li("Base Damage decreased from 85/130/175/220 to 75/120/165/210", b([85, 130, 175, 220], [75, 120, 165, 210])))
    W(ul_close())
    W(ability("Reactive Armor", slug="shredder_reactive_armor"))
    W(ul_open())
    W(li("Aghanim's Scepter effect radius decreased from 600 to 450", b(600, 450)))
    W(ul_close())

    # Tinker
    W(hero_header("Tinker"))
    W(ability("Laser", slug="tinker_laser"))
    W(ul_open())
    W(li("Now shows the overhead \"Blinded\" text over affected units", t("QoL")))
    W(ul_close())

    # Tiny
    W(hero_header("Tiny"))
    W(ability("Tree Grab", slug="tiny_tree_grab"))
    W(ul_open())
    W(li("Splash Damage increased from 55/70/85/100% to 70/80/90/100%", b([55, 70, 85, 100], [70, 80, 90, 100])))
    W(ul_close())

    # Treant Protector
    W(hero_header("Treant Protector"))
    W(ul_open())
    W(li("Base Armor increased by 1", t("BUFF")))
    W(ul_close())
    W(ability("Nature's Guise", slug="treant_natures_guise"))
    W(ul_open())
    W(li_formula("Cooldown decreased",
                 "50s − 3s per 2 level ups", "35s − 1s per level up",
                 lambda L: 50 - 3 * ((L - 1) // 2), lambda L: 35 - (L - 1), l=True,
                 value_fmt="{:g}s"))
    W(ul_close())
    W(ability("Living Armor", slug="treant_living_armor"))
    W(ul_open())
    W(li("Damage Blocked increased from 100 to 120", b(100, 120)))
    W(li("Cooldown decreased from 30/25/20/15s to 24/21/18/15s", b([30, 25, 20, 15], [24, 21, 18, 15], l=True)))
    W(ul_close())
    W(ability("Overgrowth", slug="treant_overgrowth"))
    W(ul_open())
    W(li("Aghanim's Scepter Cooldown increased from 80/70/60s to 85/75/65s", b([80, 70, 60], [85, 75, 65], l=True)))
    W(ul_close())

    # Troll Warlord
    W(hero_header("Troll Warlord"))
    W(ability("Battle Stance", slug="troll_warlord_switch_stance"))
    W(ul_open())
    W(li("Toggling is no longer disabled by silence", t("MISC")))
    W(ul_close())

    # Underlord
    W(hero_header("Underlord"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Firestorm Cooldown Reduction increased from 3s to 4s", b(3, 4, l=True)))
    W(ul_close())

    # Ursa
    W(hero_header("Ursa"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +5 Fury Swipes Damage replaced with +0.5% Maul Health as Damage", t("REWORK")))
    W(li("Level 20 Talent +0.5% Maul Health as Damage replaced with +6 Fury Swipes Damage", t("REWORK")))
    W(li("Level 20 Talent Earthshock Radius decreased from +400 to +300", b(400, 300)))
    W(ul_close())

    # Viper
    W(hero_header("Viper"))
    W(facet_header("viper_caustic_bath"))
    W(ul_open())
    W(li("Corrosive Skin: Max bonus effect decreased from 100% to 75%", b(100, 75)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +20 Corrosive Skin Damage Per Second replaced with +10% Poison Attack Slow/Damage", t("REWORK")))
    W(li("Level 15 Talent +15% Poison Attack Slow/Damage replaced with +20 Corrosive Skin Damage Per Second", t("REWORK")))
    W(li("Level 15 Talent Nethertoxin Min/Max Damage decreased from +40 to +30", b(40, 30)))
    W(ul_close())

    # Void Spirit
    W(hero_header("Void Spirit"))
    W(ability("Aether Remnant", slug="void_spirit_aether_remnant"))
    W(ul_open())
    W(li("Remnant Lifetime decreased from 20s to 17s", b(20, 17)))
    W(ul_close())

    # Warlock
    W(hero_header("Warlock"))
    W(ability("Eldritch Summoning", slug="warlock_eldritch_summoning"))
    W(ul_open())
    W(li("Imp explosion damage decreased from 25/70/115/160/205 to 20/65/110/155/200", b([25, 70, 115, 160, 205], [20, 65, 110, 155, 200])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Upheaval Damage increased from +40 to +45", b(40, 45)))
    W(li("Level 25 Talent Fatal Bonds Targets increased from +3 to +4", b(3, 4)))
    W(ul_close())

    # Windranger
    W(hero_header("Windranger"))
    W(facet_header("windrunner_tangled"))
    W(ul_open())
    W(li("Shackleshot: Bonus damage per hero decreased from 40 to 35", b(40, 35)))
    W(ul_close())
    W(ul_open())
    W(li("Powershot: Slow duration decreased from 4s to 3s", b(4, 3)))
    W(ul_close())
    W(ul_open())
    W(li("Windrun: Aghanim's Scepter physical damage reduction decreased from 45% to 35%", b(45, 35)))
    W(ul_close())

    # Winter Wyvern
    W(hero_header("Winter Wyvern"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent HP/s Cold Embrace Heal decreased from +25 to +20", b(25, 20)))
    W(li("Level 15 Talent Splinter Blast Shatter Radius decreased from +300 to +250", b(300, 250)))
    W(li("Level 25 Talent Splinter Blast Stun Duration decreased from +1.25s to +1s", b(1.25, 1)))
    W(ul_close())

    # Witch Doctor
    W(hero_header("Witch Doctor"))
    W(facet_header("witch_doctor_cleft_death"))
    W(ul_open())
    W(li("Death Ward: Damage decreased from 55/90/125 to 55/85/115", b([55, 90, 125], [55, 85, 115])))
    W(ul_close())
    W(ul_open())
    W(li("Death Ward: Damage decreased from 60/95/130 to 60/90/120", b([60, 95, 130], [60, 90, 120])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Death Ward Damage decreased from +45 to +40", b(45, 40)))
    W(ul_close())

    # Wraith King
    W(hero_header("Wraith King"))
    W(facet_header("skeleton_king_facet_bone_guard"))
    W(ul_open())
    W(li("Bone Guard: Skeleton movement speed decreased from 350 to 340", b(350, 340)))
    W(ul_close())

    # Zeus
    W(hero_header("Zeus"))
    W(ability("Static Field", slug="zuus_static_field"))
    W(ul_open())
    W(li("Current HP Damage increased from 2.5/3/3.5/4% to 2.5/3.25/4/4.75%", b([2.5, 3, 3.5, 4], [2.5, 3.25, 4, 4.75])))
    W(ul_close())

    write_footer()
    save_html('patches/7.40b.html')

