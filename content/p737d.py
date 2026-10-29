from patch.api import *

def build():
    write_head("7.37d", "01.10.2024")

    # ===== ITEM UPDATES =====
    W(section("Item Updates"))
    W(item_header("Arcane Boots"))
    W(auto_components_change("Arcane Boots", "7.37d"))
    W(properties_change(old=[("NERF", "+0.5 Mana Regen")], new=[("", "+0.25 Mana Regen", b(0.5, 0.25))]))
    W(ul_open())
    W(li("Recipe cost increased from 375 to 475. Total Cost increased from 1300 to 1400", b([375, 1300], [475, 1400], l=True, slash=True)))
    W(li("Replenish Mana mana restored decreased from 175 to 150", b(175, 150)))
    W(ul_close())
    W(item_header("Bracer"))
    W(ul_open())
    W(li("No longer doubles its bonuses at 25 minutes", t("DEL")))
    W(ul_close())
    W(item_header("Crimson Guard"))
    W(ul_open())
    W(li("Guard duration decreased from 8s to 7s", b(8, 7)))
    W(ul_close())
    W(item_header("Disperser"))
    # abilities before -> after: the game's tooltips of each patch (patch/item_ability_text.py)
    W(item_abilities_change(
        old=["Active: Suppress. Slows the target for 5 seconds if they are an enemy or grants bonus movespeed, applies Basic Dispel and makes them unslowable for 5 seconds if they are an ally. Caster is always granted the ally benefit on cast. Both movement speed reduction and increase start at 100% and gradually decrease to 0% over the course of the buff duration. Dispel Type: Basic Dispel. Cast Range: 600. Mana Cost: 75. Cooldown: 15s",
             "Passive: Manabreak. Each attack burns 40 mana from the target, and deals 1 physical damage per burned mana. Burns 8 mana per attack from melee illusions and 8 mana per attack from ranged illusions."],
        new=["Active: Suppress. Slows the target for 5 seconds if they are an enemy or applies a basic dispell and grants bonus movespeed and 40% slow resistance for 5 seconds if they are an ally. Caster is always granted the ally benefit on cast. Both movement speed reduction and increase start at 100% and gradually decrease to 0% over the course of the buff duration. Dispel Type: Basic Dispel. Cast Range: 600. Mana Cost: 75. Cooldown: 15s",
             "Passive: Manabreak. Each attack burns 40 mana from the target, and deals 1 physical damage per burned mana. Burns 8 mana per attack from melee illusions and 8 mana per attack from ranged illusions."]))
    W(ul_open())
    W(li("Suppress now provides 40% slow resistance for the duration when used on caster or ally", t("NEW")))
    W(li("Suppress no longer makes caster or ally unslowable", t("DEL")))
    W(ul_close())
    W(item_header("Gleipnir"))
    W(auto_components_change("Gleipnir", "7.37d"))
    W(properties_change(old=[("NERF", "+30 Damage"), ("NERF", "+30 Attack Speed"), ("NERF", "+300 Health")], new=[("", "+25 Damage", b(30, 25)), ("", "+25 Attack Speed", b(30, 25)), ("", "+275 Health", b(300, 275))]))
    W(ul_open())
    W(li("Recipe cost increased from 250 to 550. Total Cost increased from 5450 to 5750", b([250, 5450], [550, 5750], l=True, slash=True)))
    W(li("Chain Lightning damage decreased from 160 to 140", b(160, 140)))
    W(ul_close())
    W(item_header("Guardian Greaves"))
    W(ul_open())
    W(li("Total cost increased from 4950 to 5050 (due to Arcane Boots cost increase)", b(4950, 5050, l=True)))
    W(ul_close())
    W(item_header("Null Talisman"))
    W(ul_open())
    W(li("No longer doubles its bonuses at 25 minutes", t("DEL")))
    W(ul_close())
    W(item_header("Pavise"))
    # abilities before -> after: the game's tooltips of each patch (patch/item_ability_text.py)
    W(item_abilities_change(
        old=["Active: Protect. When cast on an ally, grants them a physical damage barrier that absorbs 300 damage. Duration: 8s. Cast Range: 1000. Mana Cost: 75. Cooldown: 16s"],
        new=["Active: Protect. When cast on an ally, grants them a physical damage barrier that absorbs 250 damage. Duration: 7s. Cast Range: 1000. Mana Cost: 100. Cooldown: 16s"]))
    W(ul_open())
    W(li("Protect physical damage barrier decreased from 300 to 250", b(300, 250)))
    W(li("Protect duration decreased from 8s to 7s", b(8, 7)))
    W(li("Protect mana cost increased from 75 to 100", b(75, 100, l=True)))
    W(ul_close())
    W(item_header("Pipe of Insight"))
    W(ul_open())
    W(li("Barrier duration decreased from 10s to 8s", b(10, 8)))
    W(ul_close())
    W(item_header("Ring of Basilius"))
    W(ul_open())
    W(li("Mana Regen bonus decreased from +0.5 to +0.25", b(0.5, 0.25)))
    W(ul_close())
    W(item_header("Solar Crest"))
    W(properties_change(old=[("NERF", "+200 Health")], new=[("", "+175 Health", b(200, 175))]))
    # abilities before -> after: the game's tooltips of each patch (patch/item_ability_text.py)
    W(item_abilities_change(
        old=["Active: Shine. When cast on an ally, grants them 5 armor, 70 attack speed, 15% movement speed and a 400 physical damage barrier. Does not grant bonus armor, movement or attack speed if used on self. Duration: 8. Cast Range: 1000. Mana Cost: 100. Cooldown: 16s"],
        new=["Active: Shine. When cast on an ally, grants them 5 armor, 60 attack speed, 15% movement speed and a 350 physical damage barrier. Does not grant bonus armor, movement or attack speed if used on self. Duration: 7. Cast Range: 1000. Mana Cost: 100. Cooldown: 16s"]))
    W(ul_open())
    W(li("Shine duration decreased from 8s to 7s", b(8, 7)))
    W(li("Shine physical damage barrier decreased from 400 to 350", b(400, 350)))
    W(li("Shine bonus attack speed decreased from 70 to 60", b(70, 60)))
    W(ul_close())
    W(item_header("Spirit Vessel"))
    # abilities before -> after: the game's tooltips of each patch (patch/item_ability_text.py)
    W(item_abilities_change(
        old=["Active: Soul Release. When used against enemies, it reduces health by 4% of current health per second, and reduces HP regeneration, healing, lifesteal and spell lifesteal by 50%. Deals 25 damage per second. When used on allies, it provides 40 health regeneration per second. Lasts 8 seconds. Gains charges every time an enemy hero dies within 1400 units. Only the closest Spirit Vessel to the dying hero will gain a charge. Cast Range: 750. Cooldown: 10s"],
        new=["Active: Soul Release. When used against enemies, it reduces health by 4% of current health per second, and reduces HP regeneration, healing, lifesteal and spell lifesteal by 60%. Deals 25 damage per second. When used on allies, it provides 40 health regeneration per second. Lasts 8 seconds. Gains charges every time an enemy hero dies within 1400 units or the user dies. Only the closest Spirit Vessel to the dying hero will gain a charge. Cast Range: 750. Cooldown: 10s"]))
    W(ul_open())
    W(li("Soul Release now always gains a charge when the owner dies", t("NEW")))
    W(li("Soul Release health restoration reduction on enemies increased from 50% to 60%", b(50, 60)))
    W(ul_close())
    W(item_header("Wraith Band"))
    W(ul_open())
    W(li("No longer doubles its bonuses at 25 minutes", t("DEL")))
    W(ul_close())

    # ===== NEUTRAL ITEM UPDATES =====
    W(section("Neutral Item Updates"))
    W(item_header("Seeds of Serenity"))
    W(ul_open())
    W(li("Verdurous Dale duration decreased from 14s to 8s", b(14, 8)))
    W(ul_close())

    # ===== HERO UPDATES =====
    W(section("Hero Updates"))

    # Anti-Mage
    W(hero_header("Anti-Mage"))
    W(facet_header("antimage_magebanes_mirror"))
    W(ul_open())
    W(li("Counterspell: Reflected Spell Amp increased from 30% to 40%", b(30, 40)))
    W(li("Counterspell: Ally: Reflected Spell Amp increased from 30% to 40%", b(30, 40)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +10% Counterspell Magic Resistance replaced with +3 Health Regen", t("SWAP")))
    W(ul_close())

    # Batrider
    W(hero_header("Batrider"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent +4.5s Firefly Duration replaced with +2s Smoldering Resin Duration", t("SWAP")))
    W(ul_close())

    # Beastmaster
    W(hero_header("Beastmaster"))
    W(ability("Primal Roar", slug="beastmaster_primal_roar"))
    W(ul_open())
    W(li("Stun Duration increased from 2.75/3.25/3.75s to 3/3.5/4s", b([2.75, 3.25, 3.75], [3, 3.5, 4])))
    W(ul_close())
    W(ability("Drums of Slom", slug="beastmaster_drums_of_slom"))
    W(ul_open())
    W(li("Heal from Heroes decreased from 25% to 20%", b(25, 20)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Inner Beast Magic Resist increased from 5% to 10%", b(5, 10)))
    W(ul_close())

    # Bloodseeker
    W(hero_header("Bloodseeker"))
    W(ability("Bloodrage", slug="bloodseeker_bloodrage"))
    W(ul_open())
    W(li("Mana Cost decreased from 25 to 0", b(25, 0, l=True)))
    W(ul_close())

    # Bounty Hunter
    W(hero_header("Bounty Hunter"))
    W(ability("Jinada", slug="bounty_hunter_jinada"))
    W(ul_open())
    W(li("Bonus Damage rescaled from 60/100/140/180 to 70/105/140/175", b([60, 100, 140, 180], [70, 105, 140, 175])))
    W(ul_close())

    # Chen
    W(hero_header("Chen"))
    W(ability("Holy Persuasion", slug="chen_holy_persuasion"))
    W(ul_open())
    W(li("Sacrificing creeps with Martyrdom (Aghanim's Scepter) now triggers On Death effects", t("NEW")))
    W(ul_close())

    # Clockwerk
    W(hero_header("Clockwerk"))
    W(facet_header("rattletrap_expanded_armature"))
    W(ul_open())
    W(li("Power Cogs: Enemy heroes caught are no longer pulled to the center of the formation. Now they are placed inside as far away from the center as possible while not touching a cog", t("REWORK")))
    W(ul_close())

    # Crystal Maiden
    W(hero_header("Crystal Maiden"))
    W(ul_open())
    W(li("Agility gain increased from 1.6 to 1.8", b(1.6, 1.8)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Crystal Nova Cooldown Reduction increased from 4s to 4.5s", b(4, 4.5)))
    W(ul_close())

    # Dawnbreaker
    W(hero_header("Dawnbreaker"))
    W(ability("Celestial Hammer", slug="dawnbreaker_celestial_hammer"))
    W(ul_open())
    W(li("Mana Cost decreased from 110/120/130/140 to 100/110/120/130", b([110, 120, 130, 140], [100, 110, 120, 130], l=True)))
    W(li("Projectile speed increased from 1500 to 1600", b(1500, 1600)))
    W(ul_close())

    # Dazzle
    W(hero_header("Dazzle"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Attack Speed increased from +80 to +90", b(80, 90)))
    W(li("Level 20 Talent Poison Touch DPS increased from +60 to +75", b(60, 75)))
    W(ul_close())

    # Death Prophet
    W(hero_header("Death Prophet"))
    W(ul_open())
    W(li("Base Damage increased by 2", bstat_h("Death Prophet", "AttackDamageMin", "7.37c", 2), extra=note_box(hero="Death Prophet", field="AttackDamageMin", before_patch="7.37c")))
    W(ul_close())
    W(ability("Exorcism", slug="death_prophet_exorcism"))
    W(ul_open())
    W(li("Spirit count increased from 8/16/24 to 10/17/24", b([8, 16, 24], [10, 17, 24])))
    W(ul_close())

    # Doom
    W(hero_header("Doom"))
    W(facet_header("doom_bringer_gluttony"))
    W(ul_open())
    W(li("Devour: Base Charge Restore Time decreased from 90s to 85s", b(90, 85, l=True)))
    W(ul_close())
    W(ability("Lvl ? Pain", slug="doom_bringer_lvl_pain"))
    W(ul_open())
    W(li("Now only applies to Doom's attacks", t("NERF")))
    W(ul_close())

    # Dragon Knight
    W(hero_header("Dragon Knight"))
    W(facet_header("dragon_knight_fire_dragon"))
    W(ul_open())
    W(li("Wyrm's Wrath: Cleave Distance decreased from 450 to 400", b(450, 400)))
    W(ul_close())

    # Drow Ranger
    W(hero_header("Drow Ranger"))
    W(ul_open())
    W(li("Base Agility increased from 20 to 22", b(20, 22)))
    W(ul_close())

    # Enchantress
    W(hero_header("Enchantress"))
    W(facet_header("enchantress_overprotective_wisps"))
    W(ul_open())
    W(li("Nature's Attendants: Damage threshold increased from 250 to 275", b(250, 275, l=True)))
    W(ul_close())
    W(ability("Enchant", slug="enchantress_enchant"))
    W(ul_open())
    W(li("Hero move slow duration decreased from 5s to 3.5/4/4.5/5s", b(5, [3.5, 4, 4.5, 5])))
    W(ul_close())
    W(ability("Sproink", slug="enchantress_bunny_hop"))
    W(ul_open())
    W(li("Cooldown increased from 8s to 10s", b(8, 10, l=True)))
    W(ul_close())

    # Grimstroke
    W(hero_header("Grimstroke"))
    W(ability("Ink Swell", slug="grimstroke_spirit_walk"))
    W(ul_open())
    W(li("Ink Tendrils DPS increased from 25/40/55/70 to 30/45/60/75", b([25, 40, 55, 70], [30, 45, 60, 75])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Stroke of Fate Damage increased from +75% to +80%", b(75, 80)))
    W(ul_close())

    # Gyrocopter
    W(hero_header("Gyrocopter"))
    W(ul_open())
    W(li("Base Damage increased by 2", bstat_h("Gyrocopter", "AttackDamageMin", "7.37c", 2), extra=note_box(hero="Gyrocopter", field="AttackDamageMin", before_patch="7.37c")))
    W(ul_close())

    # Hoodwink
    W(hero_header("Hoodwink"))
    W(ability("Hunter's Boomerang", slug="hoodwink_hunters_boomerang"))
    W(ul_open())
    W(li("Cast Range increased from 900 to 1100", b(900, 1100)))
    W(ul_close())

    # Huskar
    W(hero_header("Huskar"))
    W(facet_header("huskar_nothl_transfusion"))
    W(ul_open())
    W(li("Life Break: Heal Radius increased from 400 to 550", b(400, 550)))
    W(ul_close())

    # Invoker
    W(hero_header("Invoker"))
    W(ability("Ghost Walk", slug="invoker_ghost_walk"))
    W(ul_open())
    W(li("Health Regeneration (Quas) decreased from 10/15/20/25/30/35/40/45 to 3/6/9/12/15/18/21/24", b([10, 15, 20, 25, 30, 35, 40, 45], [3, 6, 9, 12, 15, 18, 21, 24])))
    W(li("Mana Regeneration (Wex) decreased from 2.5/5/7.5/10/12.5/15/17.5/20 to 2/4/6/8/10/12/14/16", b([2.5, 5, 7.5, 10, 12.5, 15, 17.5, 20], [2, 4, 6, 8, 10, 12, 14, 16])))
    W(ul_close())

    # Juggernaut
    W(hero_header("Juggernaut"))
    W(ability("Duelist", slug="juggernaut_duelist", innate=True))
    W(ul_open())
    W(li("Bonus damage increased from 10% to 12%", b(10, 12)))
    W(ul_close())
    W(ability("Healing Ward", slug="juggernaut_healing_ward"))
    W(ul_open())
    W(li("Mana Cost rescaled from 140/130/120/110 to 120", b([140, 130, 120, 110], 120, l=True)))
    W(ul_close())

    # Kunkka
    W(hero_header("Kunkka"))
    W(ability("Admiral's Rum", slug="kunkka_admirals_rum"))
    W(ul_open())
    W(li("Rum Duration decreased from 10s to 6s", b(10, 6), extra=inline_note("Ghostship's Rum Duration isn't affected")))
    W(ul_close())
    W(ability("Ghostship", slug="kunkka_ghostship"))
    W(ul_open())
    W(li("Damage decreased from 400/500/600 to 350/475/600", b([400, 500, 600], [350, 475, 600])))
    W(li("Cooldown increased from 80/70/60s to 90/80/70s", b([80, 70, 60], [90, 80, 70], l=True)))
    W(ul_close())

    # Lich
    W(hero_header("Lich"))
    W(ability("Frost Shield", slug="lich_frost_shield"))
    W(ul_open())
    W(li("Damage Reduction increased from 30/40/50/60% to 45/50/55/60%", b([30, 40, 50, 60], [45, 50, 55, 60])))
    W(ul_close())

    # Lifestealer
    W(hero_header("Lifestealer"))
    W(ability("Feast", slug="life_stealer_feast"))
    W(ul_open())
    W(li("Max Health Life Steal increased from 1.25/1.75/2.25/2.75% to 1.5/2/2.5/3%", b([1.25, 1.75, 2.25, 2.75], [1.5, 2, 2.5, 3])))
    W(li("Max Health Damage increased from 1.25/1.75/2.25/2.75% to 1.5/2/2.5/3%", b([1.25, 1.75, 2.25, 2.75], [1.5, 2, 2.5, 3])))
    W(ul_close())

    # Lone Druid
    W(hero_header("Lone Druid"))
    W(facet_header("lone_druid_bear_necessities"))
    W(ul_open())
    W(li("Stat Bonus decreased from 50/60/70/80% to 30/45/60/75%", b([50, 60, 70, 80], [30, 45, 60, 75])))
    W(li("Stat Bonus no longer applies to items in the Neutral slot", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Savage Roar Cooldown Reduction decreased from 7s to 5s", b(7, 5)))
    W(ul_close())

    # Luna
    W(hero_header("Luna"))
    W(facet_header("luna_moonstorm"))
    W(ul_open())
    W(li("Lucent Beam: Damage Buff per beam decreased from 5/8/11/14 to 4/7/10/13", b([5, 8, 11, 14], [4, 7, 10, 13])))
    W(li("Lucent Beam: No longer grants bonus damage when hitting illusions", t("DEL")))
    W(ul_close())
    W(ability("Lucent Beam", slug="luna_lucent_beam"))
    W(ul_open())
    W(li("Beam Damage decreased from 80/160/240/320 to 75/150/225/300", b([80, 160, 240, 320], [75, 150, 225, 300])))
    W(ul_close())

    # Marci
    W(hero_header("Marci"))
    W(facet_header("marci_sidekick"))
    W(ul_open())
    W(li("Sidekick: Bonus Base Attack Damage decreased from 12/18/24/30% to 10/15/20/25%", b([12, 18, 24, 30], [10, 15, 20, 25])))
    W(li("Sidekick: Ally bonus radius decreased from 2500 to 1750", b(2500, 1750)))
    W(ul_close())

    # Mars
    W(hero_header("Mars"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Spear of Mars Stun decreased from +0.6s to +0.4s", b(0.6, 0.4)))
    W(ul_close())

    # Medusa
    W(hero_header("Medusa"))
    W(ability("Mana Shield", slug="medusa_mana_shield"))
    W(ul_open())
    W(li("Absorbing damage with Mana Shield now disables Blink Dagger", t("NERF")))
    W(ul_close())

    # Mirana
    W(hero_header("Mirana"))
    W(facet_header("mirana_sunlight"))
    W(ul_open())
    W(li("Max Attack Speed/Damage decreased from 80/120/160 to 70/110/150", b([80, 120, 160], [70, 110, 150])))
    W(li("Duration decreased from 18s to 16s", b(18, 16)))
    W(li("No longer increases daytime vision", t("DEL")))
    W(ul_close())
    W(ability("Leap", slug="mirana_leap"))
    W(ul_open())
    W(li("Aghanim's Shard no longer allows to hit the same enemy unit by multiple secondary Starstorms in a single cast", t("DEL")))
    W(ul_close())

    # Monkey King
    W(hero_header("Monkey King"))
    W(ul_open())
    W(li("Base Strength increased from 18 to 19", b(18, 19)))
    W(ul_close())
    W(facet_header("monkey_king_wukongs_faithful"))
    W(ul_open())
    W(li("Wukong's Command: Disperse time increased from 3s to 4s", b(3, 4)))
    W(ul_close())
    W(facet_header("monkey_king_simian_stride"))
    W(ul_open())
    W(li("Tree Dance: Health threshold increased from 90% to 95%", b(90, 95)))
    W(ul_close())

    # Muerta
    W(hero_header("Muerta"))
    W(ability("Pierce the Veil", slug="muerta_pierce_the_veil"))
    W(ul_open())
    W(li("Duration increased from 6/7/8s to 8s", b([6, 7, 8], 8)))
    W(ul_close())

    # Naga Siren
    W(hero_header("Naga Siren"))
    W(facet_header("naga_siren_active_riptide"))
    W(ul_open())
    W(li("Mana Cost increased from 45/50/55/60 to 50/60/70/80", b([45, 50, 55, 60], [50, 60, 70, 80], l=True)))
    W(ul_close())
    W(ability("Song of the Siren", slug="naga_siren_song_of_the_siren"))
    W(ul_open())
    W(li("Max HP Regen per second decreased from 2/4/6% to 2/3/4%", b([2, 4, 6], [2, 3, 4])))
    W(ul_close())

    # Nature's Prophet
    W(hero_header("Nature's Prophet"))
    W(facet_header("furion_ironwood_treant"))
    W(ul_open())
    W(li("Nature's Call: Treant Damage decreased from 28-32/44-48/60-64/76-80 to 22-26/40-44/58-62/76-80", b([30, 46, 62, 78], [24, 42, 60, 78])))
    W(li("Nature's Call: Treant Movespeed decreased from 350 to 335/340/345/350", b(350, [335, 340, 345, 350])))
    W(ul_close())

    # Necrophos
    W(hero_header("Necrophos"))
    W(ability("Ghost Shroud", slug="necrolyte_ghost_shroud"))
    W(ul_open())
    W(li("Movement Slow increased from 10/15/20/25% to 16/19/22/25%", b([10, 15, 20, 25], [16, 19, 22, 25])))
    W(ul_close())
    W(ability("Reaper's Scythe", slug="necrolyte_reapers_scythe"))
    W(ul_open())
    W(li("Cooldown decreased from 110s to 100s", b(110, 100, l=True)))
    W(ul_close())

    # Omniknight
    W(hero_header("Omniknight"))
    W(ul_open())
    W(li("Base Movement Speed decreased from 315 to 310", b(315, 310)))
    W(li("Base Strength decreased from 23 to 22", b(23, 22)))
    W(ul_close())
    W(facet_header("omniknight_dmgheals"))
    W(ul_open())
    W(li("Damage as Healing decreased from 25% to 20%", b(25, 20)))
    W(ul_close())
    W(ability("Purification", slug="omniknight_purification"))
    W(ul_open())
    W(li("Mana Cost increased from 80/95/110/125 to 90/105/120/135", b([80, 95, 110, 125], [90, 105, 120, 135], l=True)))
    W(ul_close())
    W(ability("Repel", slug="omniknight_martyr"))
    W(ul_open())
    W(li("Mana Cost increased from 80/95/110/125 to 90/105/120/135", b([80, 95, 110, 125], [90, 105, 120, 135], l=True)))
    W(ul_close())

    # Pangolier
    W(hero_header("Pangolier"))
    W(facet_header("pangolier_thunderbolt"))
    W(ul_open())
    W(li("Rolling Thunder: Duration increased from 8s to 9s", b(8, 9)))
    W(ul_close())

    # Phantom Lancer
    W(hero_header("Phantom Lancer"))
    W(ability("Illusory Armaments", slug="phantom_lancer_illusory_armaments"))
    W(ul_open())
    W(li("Effects that percentually change the base damage now also affect base damage bonus provided by Illusory Armaments", t("NEW")))
    W(li("Bonus to Base Damage for illusions increased from 65% to 70%", b(65, 70)))
    W(ul_close())

    # Puck
    W(hero_header("Puck"))
    W(ability("Puckish", slug="puck_puckish"))
    W(ul_open())
    W(li("Base health restored decreased from 20 to 15", b(20, 15)))
    W(li("Base mana restored decreased from 20 to 15", b(20, 15)))
    W(ul_close())
    W(ability("Dream Coil", slug="puck_dream_coil"))
    W(ul_open())
    W(li("Duration decreased from 6s to 5/5.5/6s", b(6, [5, 5.5, 6])))
    W(ul_close())

    # Pugna
    W(hero_header("Pugna"))
    W(facet_header("pugna_siphoning_ward"))
    W(ul_open())
    W(li("Nether Ward: Damage to Mana increased from 30% to 40%", b(30, 40)))
    W(ul_close())

    # Riki
    W(hero_header("Riki"))
    W(ability("Cloak and Dagger", slug="riki_backstab"))
    W(ul_open())
    W(li("Toggling items no longer breaks invisibility", t("QoL")))
    W(ul_close())

    # Ringmaster
    W(hero_header("Ringmaster"))
    W(ul_open())
    W(li("Base Strength decreased from 23 to 21", b(23, 21)))
    W(li("Strength gain decreased from 2.4 to 2.1", b(2.4, 2.1)))
    W(ul_close())
    W(ability("Tame the Beasts", slug="ringmaster_tame_the_beasts"))
    W(ul_open())
    W(li("Cast Range decreased from 700/750/800/850 to 700", b([700, 750, 800, 850], 700)))
    W(ul_close())
    W(ability("Escape Act", slug="ringmaster_the_box"))
    W(ul_open())
    W(li("Can now be dispelled", t("NERF")))
    W(ul_close())
    W(ability("Wheel of Wonder", slug="ringmaster_wheel"))
    W(ul_open())
    W(li("Radius decreased from 600 to 500", b(600, 500)))
    W(li("Automatic explosion time decreased from 6s to 4s", b(6, 4)))
    W(ul_close())

    # Sand King
    W(hero_header("Sand King"))
    W(facet_header("sand_king_dust_devil"))
    W(ul_open())
    W(li("Sand Storm: Radius decreased from 450/500/550/600 to 350/400/450/500", b([450, 500, 550, 600], [350, 400, 450, 500])))
    W(li("Sand Storm: Duration decreased from 20/25/30/35s to 16/20/24/28s", b([20, 25, 30, 35], [16, 20, 24, 28])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Sand Storm Damage Per Second decreased from +25 to +20", b(25, 20)))
    W(ul_close())

    # Shadow Demon
    W(hero_header("Shadow Demon"))
    W(facet_header("shadow_demon_promulgate"))
    W(ul_open())
    W(li("Disseminate: Health loss decreased from 14/16/18/20% to 9/11/13/15%", b([14, 16, 18, 20], [9, 11, 13, 15])))
    W(ul_close())
    W(ability("Shadow Poison", slug="shadow_demon_shadow_poison"))
    W(ul_open())
    W(li("Vision radius decreased from 400 to 300", b(400, 300)))
    W(ul_close())

    # Shadow Shaman
    W(hero_header("Shadow Shaman"))
    W(ability("Fowl Play", slug="shadow_shaman_fowl_play"))
    W(ul_open())
    W(li("Invulnerability duration increased from 0.75s to 1s", b(0.75, 1)))
    W(ul_close())

    # Snapfire
    W(hero_header("Snapfire"))
    W(facet_header("snapfire_full_bore"))
    W(ul_open())
    W(li("Scatterblast: Cast Range decreased from 1400 to 1300", b(1400, 1300)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Mortimer Kisses Debuff DPS increased from +20 to +25", b(20, 25)))
    W(li("Level 25 Talent Mortimer Kisses Launched increased from +6 to +8", b(6, 8)))
    W(ul_close())

    # Sniper
    W(hero_header("Sniper"))
    W(facet_header("sniper_scattershot"))
    W(ul_open())
    W(li("Shrapnel: Damage decreased from 120/180/240/300 to 90/160/230/300", b([120, 180, 240, 300], [90, 160, 230, 300])))
    W(ul_close())
    W(ability("Headshot", slug="sniper_headshot"))
    W(ul_open())
    W(li("Slow Duration decreased from 0.5s to 0.2/0.3/0.4/0.5s", b(0.5, [0.2, 0.3, 0.4, 0.5])))
    W(ul_close())

    # Techies
    W(hero_header("Techies"))
    W(ability("Proximity Mines", slug="techies_land_mines"))
    W(ul_open())
    W(li("Base Charge Restore Time decreased from 19/17/15s to 15s", b([19, 17, 15], 15, l=True)))
    W(ul_close())

    # Tidehunter
    W(hero_header("Tidehunter"))
    W(ability("Blubber", slug="tidehunter_blubber", innate=True))
    W(ul_open())
    W(li("Damage threshold for dispel decreased from 500 to 450", b(500, 450, l=True)))
    W(ul_close())
    W(ability("Ravage", slug="tidehunter_ravage"))
    W(ul_open())
    W(li("Damage increased from 250/350/450 to 275/375/475", b([250, 350, 450], [275, 375, 475])))
    W(ul_close())

    # Timbersaw
    W(hero_header("Timbersaw"))
    W(ul_open())
    W(li("Base Strength decreased from 27 to 26", b(27, 26)))
    W(ul_close())

    # Treant Protector
    W(hero_header("Treant Protector"))
    W(ability("Nature's Guise", slug="treant_natures_guise"))
    W(ul_open())
    W(li("Movement Speed bonus decreased from 12% to 10%", b(12, 10)))
    W(ul_close())
    W(ability("Leech Seed", slug="treant_leech_seed"))
    W(ul_open())
    W(li("Damage/Heal per second decreased from 20/35/50/65 to 15/30/45/60", b([20, 35, 50, 65], [15, 30, 45, 60])))
    W(li("Now heals creeps for 50% effectiveness", t("NERF"),
         extra=note_box('Creeps were healed in full before: in 7.37c the seed healed all friendly units around it. '
                        '7.37d added the 50% heal reduction on creeps')))
    W(ul_close())

    # Troll Warlord
    W(hero_header("Troll Warlord"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Whirling Axes Debuff Duration increased from +2s to +2.5s", b(2, 2.5)))
    W(li("Level 20 Talent Berserker's Rage Armor increased from +8 to +9", b(8, 9)))
    W(ul_close())

    # Tusk
    W(hero_header("Tusk"))
    W(facet_header("tusk_facet_tag_team"))
    W(ul_open())
    W(li("Bonus Damage increased from 20/45/70/95 to 25/50/75/100", b([20, 45, 70, 95], [25, 50, 75, 100])))
    W(ul_close())
    W(facet_header("tusk_facet_fist_bump"))
    W(ul_open())
    W(li("Movement Bonus decreased from 25% to 10/15/20/25%", b(25, [10, 15, 20, 25])))
    W(li("Alt cast behavior now has 50% of base spell's cast range", t("NERF")))
    W(ul_close())

    # Underlord
    W(hero_header("Underlord"))
    W(facet_header("abyssal_underlord_summons"))
    W(ul_open())
    W(li("Warrior Damage rescaled from 18/32/46 to 20/30/40", b([18, 32, 46], [20, 30, 40])))
    W(li("Warrior Last Will DMG decreased from 300/400/500 to 200/300/400", b([300, 400, 500], [200, 300, 400])))
    W(ul_close())
    W(ability("Atrophy Aura", slug="abyssal_underlord_atrophy_aura"))
    W(ul_open())
    W(li("Duration decreased from 35/45/55/65s to 30/40/50/60s", b([35, 45, 55, 65], [30, 40, 50, 60])))
    W(ul_close())

    # Vengeful Spirit
    W(hero_header("Vengeful Spirit"))
    W(ability("Nether Swap", slug="vengefulspirit_nether_swap"))
    W(ul_open())
    W(li("Cooldown decreased from 50/40/30s to 46/38/30s", b([50, 40, 30], [46, 38, 30], l=True)))
    W(ul_close())

    # Venomancer
    W(hero_header("Venomancer"))
    W(ability("Noxious Plague", slug="venomancer_noxious_plague"))
    W(ul_open())
    W(li("Minimum Movement Slow increased from 0% to 15%", b(0, 15)))
    W(ul_close())

    # Visage
    W(hero_header("Visage"))
    W(facet_header("visage_gold_assumption"))
    W(ul_open())
    W(li("Soul Assumption: No longer provides extra gold if the target dies before the projectile reaches them", t("DEL")))
    W(ul_close())
    W(ability("Summon Familiars", slug="visage_summon_familiars"))
    W(ul_open())
    W(li("Recalling is now canceled if Familiars are in stone form", t("MISC")))
    W(ul_close())

    # Windranger
    W(hero_header("Windranger"))
    W(facet_header("windrunner_whirlwind"))
    W(ul_open())
    W(li("Focus Fire: Cooldown increased from 70/50/30s to 70/60/50s", b([70, 50, 30], [70, 60, 50], l=True)))
    W(li("Focus Fire: Damage Reduction increased from 30% to 35%", b(30, 35)))
    W(li("Focus Fire: Duration decreased from 9s to 8s", b(9, 8)))
    W(li("Focus Fire: Windranger can no longer shoot arrows while channeling", t("DEL")))
    W(ul_close())
    W(ability("Windrun", slug="windrunner_windrun"))
    W(ul_open())
    W(li("Aghanim's Scepter invisibility buff is now dispelled if the base Windrun buff is dispelled", t("NERF")))
    W(ul_close())

    # Winter Wyvern
    W(hero_header("Winter Wyvern"))
    W(facet_header("winter_wyvern_heal_mana"))
    W(ul_open())
    W(li("Healing Converted to Mana increased from 20% to 24%", b(20, 24)))
    W(ul_close())

    write_footer()
    save_html('patches/7.37d.html')
