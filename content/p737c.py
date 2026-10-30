from patch.api import *

def build():
    write_head("7.37c", "28.08.2024")

    # ===== NEUTRAL CREEP UPDATES =====
    W(section("Neutral Creep Updates"))

    # Harpy Stormcrafter
    W(unit_header("Harpy Stormcrafter", NEUTRAL_CDN + "harpy_storm.png"))
    W(ability("Chain Lightning", icon_url="../icons/abilities/harpy_storm_chain_lightning.png"))
    W(ul_open())
    W(li("Chain Lightning Mana Cost increased from 50 to 60", b(50, 60, l=True)))
    W(ul_close())

    # ===== ITEM UPDATES =====
    W(section("Item Updates"))
    W(item_header("Gleipnir"))
    W(ul_open())
    W(li("Health bonus decreased from 350 to 300", b(350, 300)))
    W(li("Eternal Chains damage decreased from 180 to 165", b(180, 165)))
    W(ul_close())
    W(item_header("Guardian Greaves"))
    W(ul_open())
    W(li("Mend health restored decreased from 350 to 325", b(350, 325)))
    W(ul_close())
    W(item_header("Holy Locket"))
    W(ul_open())
    W(li("Holy Blessing heal amplification decreased from 30% to 25%", b(30, 25)))
    W(ul_close())
    W(item_header("Mekansm"))
    W(ul_open())
    W(li("Restore health restored decreased from 275 to 250", b(275, 250)))
    W(ul_close())
    W(item_header("Pipe of Insight"))
    W(ul_open())
    W(li("Barrier absorbed damage decreased from 450 to 425", b(450, 425)))
    W(ul_close())
    W(item_header("Rod of Atos"))
    W(ul_open())
    W(li("Health bonus decreased from 300 to 275", b(300, 275)))
    W(ul_close())
    W(item_header("Solar Crest"))
    W(ul_open())
    W(li("Shine bonus armor decreased from 7 to 5", b(7, 5)))
    W(ul_close())

    # ===== HERO UPDATES =====
    W(section("Hero Updates"))

    # Ancient Apparition
    W(hero_header("Ancient Apparition"))
    W(ability("Ice Blast", slug="ancient_apparition_ice_blast"))
    W(ul_open())
    W(li("Frostbitten Duration increased from 10s to 10/11/12s", b(10, [10, 11, 12])))
    W(ul_close())

    # Anti-Mage
    W(hero_header("Anti-Mage"))
    W(facet_header("antimage_magebanes_mirror"))
    W(ul_open())
    W(li("Counterspell: Reflected Spell Amp increased from 20% to 30%", b(20, 30)))
    W(li("Counterspell: Ally: Reflected Spell Amp increased from 20% to 30%", b(20, 30)))
    W(ul_close())
    W(ability("Blink", slug="antimage_blink"))
    W(ul_open())
    W(li("Cooldown decreased from 13.5/11/8.5/6s to 12/10/8/6s", b([13.5, 11, 8.5, 6], [12, 10, 8, 6], l=True)))
    W(ul_close())

    # Arc Warden
    W(hero_header("Arc Warden"))
    W(ul_open())
    W(li("Base Damage increased by 2", bstat_h("Arc Warden", "AttackDamageMin", "7.37b", 2), extra=note_box(hero="Arc Warden", field="AttackDamageMin", before_patch="7.37b")))
    W(ul_close())

    # Bane
    W(hero_header("Bane"))
    W(ability("Nightmare", slug="bane_nightmare"))
    W(ul_open())
    W(li("Cast Range increased from 500/550/600/650 to 550/600/650/700", b([500, 550, 600, 650], [550, 600, 650, 700])))
    W(ul_close())

    # Dawnbreaker
    W(hero_header("Dawnbreaker"))
    W(ul_open())
    W(li("Base Health Regen increased from 0.25 to 0.5", b(0.25, 0.5)))
    W(ul_close())

    # Death Prophet
    W(hero_header("Death Prophet"))
    W(facet_header("death_prophet_delayed_damage"))
    W(ul_open())
    W(li("Damage Delayed decreased from 20/30/40/50% to 15/25/35/45%", b([20, 30, 40, 50], [15, 25, 35, 45])))
    W(ul_close())

    # Doom
    W(hero_header("Doom"))
    W(facet_header("doom_bringer_boost_selling"))
    W(ul_open())
    W(li("Buyback cost penalty increased from 15% to 20%", b(15, 20, l=True)))
    W(ul_close())

    # Drow Ranger
    W(hero_header("Drow Ranger"))
    W(ability("Marksmanship", slug="drow_ranger_marksmanship"))
    W(ul_open())
    W(li("Bonus Proc Damage increased from 40/60/80 to 50/70/90", b([40, 60, 80], [50, 70, 90])))
    W(ul_close())

    # Earthshaker
    W(hero_header("Earthshaker"))
    W(facet_header("earthshaker_slugger"))
    W(ul_open())
    W(li("No longer requires Enchant Totem to be leveled to be active", t("NEW")))
    W(li("Now scales with Echo Slam instead of Enchant Totem (values unchanged)", t("REWORK")))
    W(ul_close())

    # Ember Spirit
    W(hero_header("Ember Spirit"))
    W(ability("Sleight of Fist", slug="ember_spirit_sleight_of_fist"))
    W(ul_open())
    W(li("Mana Cost rescaled from 65 to 60/65/70/75", b(65, [60, 65, 70, 75], l=True)))
    W(ul_close())
    W(ability("Flame Guard", slug="ember_spirit_flame_guard"))
    W(ul_open())
    W(li("Damage per second decreased from 20/30/40/50 to 15/25/35/45", b([20, 30, 40, 50], [15, 25, 35, 45])))
    W(ul_close())

    # Enchantress
    W(hero_header("Enchantress"))
    W(ability("Enchant", slug="enchantress_enchant"))
    W(ul_open())
    W(li("Experience received on cast decreased from 50% to 35%", b(50, 35)))
    W(ul_close())

    # Hoodwink
    W(hero_header("Hoodwink"))
    W(ability("Acorn Shot", slug="hoodwink_acorn_shot"))
    W(ul_open())
    W(li("Slow Duration decreased from 0.35s to 0.3s", b(0.35, 0.3)))
    W(ul_close())

    # Lich
    W(hero_header("Lich"))
    W(ability("Death Charge", slug="lich_death_charge", innate=True))
    W(ul_open())
    W(li("Mana restoration range increased from 1200 to 1500", b(1200, 1500)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Sinister Gaze Duration decreased from +0.4s to +0.3s", b(0.4, 0.3)))
    W(ul_close())

    # Lina
    W(hero_header("Lina"))
    W(ability("Combustion", slug="lina_combustion", innate=True))
    W(ul_open())
    W(li("Damage threshold increased from 150 to 175", b(150, 175, l=True)))
    W(ul_close())
    W(ability("Light Strike Array", slug="lina_light_strike_array"))
    W(ul_open())
    W(li("Stun Duration decreased from 1.3/1.6/1.9/2.2s to 1/1.4/1.8/2.2s", b([1.3, 1.6, 1.9, 2.2], [1, 1.4, 1.8, 2.2])))
    W(ul_close())

    # Lion
    W(hero_header("Lion"))
    W(ability("Hex", slug="lion_voodoo"))
    W(ul_open())
    W(li("Cast Range increased from 550/575/600/625 to 575/600/625/650", b([550, 575, 600, 625], [575, 600, 625, 650])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Hex Cooldown Reduction increased from 2s to 2.5s", b(2, 2.5)))
    W(ul_close())

    # Magnus
    W(hero_header("Magnus"))
    W(ability("Skewer", slug="magnataur_skewer"))
    W(ul_open())
    W(li("Damage increased from 75/150/225/300 to 80/160/240/320", b([75, 150, 225, 300], [80, 160, 240, 320])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Shockwave Slow Duration increased from +0.5s to +0.75s", b(0.5, 0.75)))
    W(ul_close())

    # Marci
    W(hero_header("Marci"))
    W(ability("Rebound", slug="marci_companion_run"))
    W(ul_open())
    W(li("Ally movement speed bonus duration decreased from 5s to 4s", b(5, 4)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Unleash Movement Speed decreased from +12% to +10%", b(12, 10)))
    W(ul_close())

    # Naga Siren
    W(hero_header("Naga Siren"))
    W(facet_header("naga_siren_active_riptide"))
    W(ul_open())
    W(li("Max Movement Speed increased from 225 to 240", b(225, 240)))
    W(ul_close())

    # Nature's Prophet
    W(hero_header("Nature's Prophet"))
    W(facet_header("furion_ironwood_treant"))
    W(ul_open())
    W(li("Nature's Call: Treant's Base Attack Time increased from 1.4s to 1.6s", b(1.4, 1.6, l=True)))
    W(ul_close())
    W(ability("Wrath of Nature", slug="furion_wrath_of_nature"))
    W(ul_open())
    W(li("Base Damage decreased from 120/155/190 to 100/140/180", b([120, 155, 190], [100, 140, 180])))
    W(ul_close())

    # Necrophos
    W(hero_header("Necrophos"))
    W(ul_open())
    W(li("Base Intelligence increased from 22 to 23", b(22, 23)))
    W(ul_close())
    W(ability("Ghost Shroud", slug="necrolyte_ghost_shroud"))
    W(ul_open())
    W(li("Increased Magic Damage decreased from 25% to 20%", b(25, 20)))
    W(ul_close())

    # Ogre Magi
    W(hero_header("Ogre Magi"))
    W(ability("Bloodlust", slug="ogre_magi_bloodlust"))
    W(ul_open())
    W(li("Bonus Attack Speed increased from 30/45/60/75 to 35/50/65/80", b([30, 45, 60, 75], [35, 50, 65, 80])))
    W(ul_close())
    W(ability("Fire Shield", slug="ogre_magi_smash"))
    W(ul_open())
    W(li("Multicasts now prioritize Ogre Magi himself, followed by heroes, then buildings, then creeps, skipping units that already have the buff", t("NEW")))
    W(ul_close())

    # Omniknight
    W(hero_header("Omniknight"))
    W(ability("Purification", slug="omniknight_purification"))
    W(ul_open())
    W(li("Aghanim's Shard secondary Purification effectiveness decreased from 75% to 65%", b(75, 65)))
    W(ul_close())
    W(ability("Repel", slug="omniknight_martyr"))
    W(ul_open())
    W(li("Duration decreased from 6s to 5s", b(6, 5)))
    W(ul_close())
    W(ability("Hammer of Purity", slug="omniknight_hammer_of_purity"))
    W(ul_open())
    W(li("Damage decreased from 55/70/85/100 to 40/60/80/100", b([55, 70, 85, 100], [40, 60, 80, 100])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +1s Guardian Angel Duration replaced with +1s Repel Duration", t("SWAP")))
    W(li("Level 20 Talent +2s Repel Duration replaced with +2s Guardian Angel Duration", t("SWAP")))
    W(ul_close())

    # Pangolier
    W(hero_header("Pangolier"))
    W(facet_header("pangolier_double_jump"))
    W(ul_open())
    W(li("Shield Crash: Max Damage Increase decreased from 50% to 40%", b(50, 40)))
    W(li("Shield Crash: Max Barrier Increase decreased from 50% to 40%", b(50, 40)))
    W(ul_close())

    # Phantom Lancer
    W(hero_header("Phantom Lancer"))
    W(facet_header("phantom_lancer_convergence"))
    W(ul_open())
    W(li("Juxtapose: Illusion Damage increased from 13/15/17% to 15/17/19%", b([13, 15, 17], [15, 17, 19])))
    W(ul_close())
    W(facet_header("phantom_lancer_divergence"))
    W(ul_open())
    W(li("Juxtapose: Illusion Damage increased from 15/17/19% to 17/19/21%", b([15, 17, 19], [17, 19, 21])))
    W(ul_close())
    W(ability("Spirit Lance", slug="phantom_lancer_spirit_lance"))
    W(ul_open())
    W(li("Illusion Duration increased from 2/4/6/8s to 3.5/5/6.5/8s", b([2, 4, 6, 8], [3.5, 5, 6.5, 8])))
    W(ul_close())
    W(ability("Phantom Rush", slug="phantom_lancer_phantom_edge"))
    W(ul_open())
    W(li("Bonus Agility is now applied during the rush as well as the 1.5s after it ends", t("NEW")))
    W(ul_close())

    # Primal Beast
    W(hero_header("Primal Beast"))
    W(ul_open())
    W(li("Base Movement Speed decreased from 310 to 305", b(310, 305)))
    W(ul_close())

    # Pugna
    W(hero_header("Pugna"))
    W(ability("Life Drain", slug="pugna_life_drain"))
    W(ul_open())
    W(li("Enemy Drain per second rescaled from 160/240/320 to 150/250/350", b([160, 240, 320], [150, 250, 350])))
    W(ul_close())

    # Riki
    W(hero_header("Riki"))
    W(ability("Backstab", slug="riki_innate_backstab", innate=True))
    W(ul_open())
    W(li("Agi Damage Mult increased from 0.4/0.8/1.2/1.6 to 0.55/0.9/1.25/1.6", b([0.4, 0.8, 1.2, 1.6], [0.55, 0.9, 1.25, 1.6])))
    W(ul_close())

    # Ringmaster
    W(hero_header("Ringmaster"))
    W(ul_open())
    W(li("Base Movement Speed decreased from 315 to 310", b(315, 310)))
    W(ul_close())
    W(ability("Strongman Tonic", slug="ringmaster_strongman_tonic"))
    W(ul_open())
    W(li("Bonus Strength per Ringmaster's level decreased from 1.5 to 1", b(1.5, 1)))
    W(ul_close())
    W(ability("Wheel of Wonder", slug="ringmaster_wheel"))
    W(ul_open())
    W(li("Timer Duration decreased from 2.75/3.0/3.25s to 2.5/2.75/3s", b([2.75, 3, 3.25], [2.5, 2.75, 3])))
    W(li("Automatic explosion time decreased from 8s to 6s", b(8, 6)))
    W(ul_close())
    W(ability("Spotlight", slug="ringmaster_spotlight"))
    W(ul_open())
    W(li("Linger duration increased from 0.1s to 0.3s", b(0.1, 0.3)))
    W(ul_close())

    # Rubick
    W(hero_header("Rubick"))
    W(ul_open())
    W(li("Base Damage decreased by 2", bstat_h("Rubick", "AttackDamageMin", "7.37b", -2), extra=note_box(hero="Rubick", field="AttackDamageMin", before_patch="7.37b")))
    W(ul_close())

    # Sand King
    W(hero_header("Sand King"))
    W(ul_open())
    W(li("Base Strength decreased from 22 to 21", b(22, 21)))
    W(ul_close())
    W(ability("Caustic Finale", slug="sandking_caustic_finale", innate=True))
    W(ul_open())
    W(li("Base Damage decreased from 20/40/60/80 to 15/35/55/75", b([20, 40, 60, 80], [15, 35, 55, 75])))
    W(ul_close())

    # Shadow Demon
    W(hero_header("Shadow Demon"))
    W(facet_header("shadow_demon_promulgate"))
    W(ul_open())
    W(li("Disseminate: Current health lost decreased from 20% to 14/16/18/20%", b(20, [14, 16, 18, 20])))
    W(ul_close())

    # Shadow Shaman
    W(hero_header("Shadow Shaman"))
    W(ability("Shackles", slug="shadow_shaman_shackles"))
    W(ul_open())
    W(li("Cooldown decreased from 16/14/12/10s to 13/12/11/10s", b([16, 14, 12, 10], [13, 12, 11, 10], l=True)))
    W(ul_close())

    # Silencer
    W(hero_header("Silencer"))
    W(ul_open())
    W(li("Agility gain decreased from 2.4 to 2.2", b(2.4, 2.2)))
    W(li("Base Attack Speed increased from 100 to 110", b(100, 110)))
    W(ul_close())
    W(ability("Arcane Curse", slug="silencer_curse_of_the_silent"))
    W(ul_open())
    W(li("Movement Slow increased from 10/15/20/25% to 16/19/22/25%", b([10, 15, 20, 25], [16, 19, 22, 25])))
    W(ul_close())

    # Spectre
    W(hero_header("Spectre"))
    W(ability("Spectral Dagger", slug="spectre_spectral_dagger"))
    W(ul_open())
    W(li("Mana Cost decreased from 120/130/140/150 to 110/120/130/140", b([120, 130, 140, 150], [110, 120, 130, 140], l=True)))
    W(ul_close())

    # Sven
    W(hero_header("Sven"))
    W(ability("Warcry", slug="sven_warcry"))
    W(ul_open())
    W(li("Duration decreased from 10s to 8s", b(10, 8)))
    W(ul_close())

    # Tinker
    W(hero_header("Tinker"))
    W(ul_open())
    W(li("Base Mana Regen decreased from 0.75 to 0.5", b(0.75, 0.5)))
    W(ul_close())
    W(ability("Defense Matrix", slug="tinker_defense_matrix"))
    W(ul_open())
    W(li("Status Resistance rescaled from 10/20/30/40% to 15/20/25/30%", b([10, 20, 30, 40], [15, 20, 25, 30])))
    W(li("Cast Range decreased from 700/750/800/850 to 700", b([700, 750, 800, 850], 700)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Defense Matrix Damage Barrier decreased from +125 to +75", b(125, 75)))
    W(ul_close())

    # Windranger
    W(hero_header("Windranger"))
    W(ul_open())
    W(li("Base Agility decreased from 19 to 17", b(19, 17)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Windrun Cooldown Reduction decreased from 2.5s to 2s", b(2.5, 2)))
    W(li("Level 20 Talent Focus Fire Damage Penalty Reduction decreased from 12% to 10%", b(12, 10)))
    W(ul_close())

    # Winter Wyvern
    W(hero_header("Winter Wyvern"))
    W(facet_header("winter_wyvern_heal_mana"))
    W(ul_open())
    W(li("Healing Converted to Mana increased from 15% to 20%", b(15, 20)))
    W(ul_close())

    # Zeus
    W(hero_header("Zeus"))
    W(ability("Lightning Bolt", slug="zuus_lightning_bolt"))
    W(ul_open())
    W(li("Damage increased from 125/200/275/350 to 140/220/300/380", b([125, 200, 275, 350], [140, 220, 300, 380])))
    W(ul_close())
    W(ability("Nimbus", slug="zuus_cloud"))
    W(ul_open())
    W(li("Mana Cost decreased from 325 to 275", b(325, 275, l=True)))
    W(ul_close())

    write_footer()
    save_html('patches/7.37c.html')
