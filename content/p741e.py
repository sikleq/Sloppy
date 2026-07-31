from patch.api import *

def build():
    write_head("7.41e", "30.07.2026")

    # 7.41e — auto-generated from data/7.41e_datafeed.json (generate_patch_code_v2.py)
    # then hand-reviewed: recipe-cost rows with unchanged total moved to the
    # canonical MISC + inline-badge form, "Damage at level 1"/"Damage gain per
    # level" consequence lines promoted to their own visible rows, Spirit Bear
    # (hero_id 1961) folded into the Lone Druid section as a unit block, the
    # per-hero-level Thread Break Distance row moved to li_formula.

    # ===== GENERAL UPDATES =====
    W(section("General Updates"))

    W(plain_header("Twin Gates"))
    W(ul_open())
    W(li("Channeling the Twin Gate can now be interrupted by root", t("MISC")))
    W(ul_close())

    W(plain_header("Tormentor"))
    W(ul_open())
    W(li("Now disjoints projectiles when moving between chasms", t("NEW")))
    W(ul_close())

    # ===== ITEM UPDATES =====
    W(section("Item Updates"))
    W(item_header("Abyssal Blade"))
    W(ul_open())
    W(li("Strength bonus increased from +26 to +30", b(26, 30)))
    W(ul_close())
    W(item_header("Butterfly"))
    W(ul_open())
    W(li("Agility bonus decreased from +35 to +30", b(35, 30)))
    W(li("Damage bonus increased from +25 to +30", b(25, 30)))
    W(ul_close())
    W(item_header("Chasm Stone"))
    W(ul_open())
    W(li("Cost increased from 800 to 900", b(800, 900, l=True)))
    W(ul_close())
    W(item_header("Shiva's Guard"))
    W(ul_open())
    W(li("Recipe cost decreased from 1350 to 1250 " + b(1350, 1250, l=True), t("MISC"),
         extra=inline_note("Total cost unchanged at 4500g")))
    W(ul_close())
    W(item_header("Gleipnir"))
    W(ul_open())
    W(li("Recipe cost decreased from 400 to 300 " + b(400, 300, l=True), t("MISC"),
         extra=inline_note("Total cost unchanged at 4650g")))
    W(ul_close())
    W(item_header("Crella's Crozier"))
    W(ul_open())
    W(li("Rite of Rumusque movement speed steal duration increased from 1.5s to 2s", b(1.5, 2)))
    W(li("Rite of Rumusque Putrefaction Aura effect increased from 75% to 90%", b(75, 90)))
    W(ul_close())
    W(item_header("Divine Rapier"))
    W(ul_open())
    W(li("Spell Amplification from multiple Divine Rapiers no longer stacks", t("DEL")))
    W(ul_close())
    W(item_header("Eye of Skadi"))
    W(ul_open())
    W(li("Cold Attack attack speed slow increased from 20% to 25%", b(20, 25)))
    W(ul_close())
    W(item_header("Hand of Midas"))
    W(ul_open())
    W(li("Attack Speed bonus increased from +35 to +40", b(35, 40)))
    W(ul_close())
    W(item_header("Heaven's Halberd"))
    W(ul_open())
    W(li("Disarm cooldown decreased from 16s to 15s", b(16, 15, l=True)))
    W(ul_close())
    W(item_header("Hurricane Pike"))
    W(ul_open())
    W(li("Hurricane Thrust buff duration decreased from 6s to 5s", b(6, 5)))
    W(ul_close())
    W(item_header("Kaya"))
    W(ul_open())
    W(li("Mana Regen Amplification decreased from 30% to 20%", b(30, 20)))
    W(ul_close())
    W(item_header("Meteor Hammer"))
    W(ul_open())
    W(li("Mana Regen Amplification decreased from 35% to 25%", b(35, 25)))
    W(ul_close())
    W(item_header("Kaya and Sange"))
    W(ul_open())
    W(li("Mana Regen Amplification decreased from 40% to 30%", b(40, 30)))
    W(ul_close())
    W(item_header("Yasha and Kaya"))
    W(ul_open())
    W(li("Mana Regen Amplification decreased from 40% to 30%", b(40, 30)))
    W(ul_close())
    W(item_header("Mask of Madness"))
    W(ul_open())
    W(li("Berserk now provides 15% slow resistance for ranged heroes and 30% for melee heroes, instead of 30% for any hero", t("REWORK")))
    W(li("Berserk movement speed bonus on ranged heroes decreased from 8% to 6%", b(8, 6)))
    W(ul_close())
    W(item_header("Orb of Frost"))
    W(ul_open())
    W(li("Frost health restoration reduction increased from 13% to 15%", b(13, 15)))
    W(li("Frost no longer applies when attacking allies", t("MISC")))
    W(ul_close())
    W(item_header("Orb of Corrosion"))
    W(ul_open())
    W(li("Corrosion health restoration reduction increased from 16% to 18%", b(16, 18)))
    W(ul_close())
    W(item_header("Orb of Venom"))
    W(ul_open())
    W(li("Poison Attack damage per second increased from 10 to 12", b(10, 12)))
    W(ul_close())
    W(item_header("Refresher Shard"))
    W(ul_open())
    W(li("No longer provides +12 Health Regen, +6 Mana Regen, or +20 Damage", t("DEL")))
    W(ul_close())
    W(item_header("Satanic"))
    W(ul_open())
    W(li("Unholy Rage cooldown increased from 30s to 40s", b(30, 40, l=True)))
    W(ul_close())
    W(item_header("Smoke of Deceit"))
    W(ul_open())
    W(li("Disguise now has a fixed duration and is not affected by buff duration amplification", t("MISC")))
    W(ul_close())
    W(item_header("Urn of Shadows"))
    W(ul_open())
    W(li("Mana Regen bonus decreased from +1.25 to +1", b(1.25, 1)))
    W(li("When in Stash, no longer grants charges from nearby hero deaths", t("MISC")))
    W(ul_close())
    W(item_header("Essence Distiller"))
    W(ul_open())
    W(li("When in Stash, no longer grants charges from nearby hero deaths", t("MISC")))
    W(ul_close())
    W(item_header("Spirit Vessel"))
    W(ul_open())
    W(li("When in Stash, no longer grants charges from nearby hero deaths", t("MISC")))
    W(ul_close())
    W(item_header("Veil of Discord"))
    W(ul_open())
    W(li("Spell Weakness mana cost decreased from 50 to 25", b(50, 25, l=True)))
    W(ul_close())

    # ===== NEUTRAL ITEM UPDATES =====
    W(section("Neutral Item Updates"))

    W(plain_header("Artifacts", dynamics=False, sublabel=True))
    W(item_header("Forager's Kit"))
    W(ul_open())
    W(li("Forage time decreased from 1s to 0.75s", b(1, 0.75, l=True)))
    W(ul_close())
    W(item_header("Conjurer's Catalyst"))
    W(ul_open())
    W(li("Spellover non-hero explosion damage decreased from 30 to 20", b(30, 20), extra=inline_note("From 39 to 26 with Dormant Curio")))
    W(li("Spellover damage threshold on illusions now only considers pre-amplification damage", t("REWORK")))
    W(ul_close())
    W(item_header("Enchanter's Bauble"))
    W(ul_open())
    W(li("Enchant recraft bonus decreased from 40% to 35%", b(40, 35), extra=inline_note("From 52% to 45.5% with Dormant Curio")))
    W(ul_close())
    W(item_header("Witchbane"))
    W(ul_open())
    W(li("Cleanse cooldown decreased from 40s to 30s", b(40, 30, l=True)))
    W(ul_close())

    W(plain_header("Enchantments", dynamics=False, sublabel=True))
    W(enchant_header("Greedy"))
    W(ul_open())
    W(li("GPM Bonus decreased from +75/100 to +65/90", b([75, 100], [65, 90])))
    W(ul_close())
    W(enchant_header("Feverish"))
    W(ul_open())
    W(li("No longer increases Mana Cost/Lost by 7%. Now decreases maximum mana by 20%", t("REWORK")))
    W(ul_close())

    # ===== HERO UPDATES =====
    W(section("Hero Updates"))

    # Ancient Apparition
    W(hero_header("Ancient Apparition"))
    W(ability("Ice Blast", slug="ancient_apparition_ice_blast"))
    W(ul_open())
    W(li("Cooldown decreased from 60/50/40s to 50/45/40s", b([60, 50, 40], [50, 45, 40], l=True)))
    W(ul_close())

    # Axe
    W(hero_header("Axe"))
    W(ul_open())
    W(li("Base Agility decreased from 20 to 18", b(20, 18)))
    W(ul_close())
    W(ability("Battle Hunger", slug="axe_battle_hunger"))
    W(ul_open())
    W(li("Damage per second decreased from 12/18/24/30 to 12/16/20/24", b([12, 18, 24, 30], [12, 16, 20, 24])))
    W(ul_close())

    # Bane
    W(hero_header("Bane"))
    W(ability("Ichor of Nyctasha", slug="bane_ichor_of_nyctasha"))
    W(ul_open())
    W(li("Max Terrors per hero increased from 5 to 6", b(5, 6)))
    W(li("Status Resistance per Terror decreased from 5% to 4%", b(5, 4)))
    W(ul_close())
    W(ability("Nightmare", slug="bane_nightmare"))
    W(ul_open())
    W(li("Now completely disables the target's sight, instead of overriding the vision range value", t("REWORK")))
    W(li("Duration decreased from 3.5/4.5/5.5/6.5s to 3/4/5/6s", b([3.5, 4.5, 5.5, 6.5], [3, 4, 5, 6])))
    W(ul_close())
    W(ability("Fiend's Grip", slug="bane_fiends_grip"))
    W(ul_open())
    W(li("Aghanim's Scepter cooldown reduction decreased from 45s to 40s", b(45, 40)))
    W(ul_close())

    # Batrider
    W(hero_header("Batrider"))
    W(ability("Smoldering Resin", slug="batrider_smoldering_resin"))
    W(ul_open())
    W(li("No longer applies when attacking allies", t("MISC")))
    W(ul_close())

    # Beastmaster
    W(hero_header("Beastmaster"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Damage to Beastmaster and his summons decreased from +30 to +25", b(30, 25)))
    W(li("Level 25 Talent Primal Roar Cooldown Reduction decreased from 25s to 20s", b(25, 20)))
    W(ul_close())

    # Centaur Warrunner
    W(hero_header("Centaur Warrunner"))
    W(ability("Double Edge", slug="centaur_double_edge"))
    W(ul_open())
    W(li("Aghanim's Shard Buff duration decreased from 15s to 12s", b(15, 12)))
    W(ul_close())
    W(ability("Retaliate", slug="centaur_return"))
    W(ul_open())
    W(li("Strength Return Damage decreased from 16/24/32/40% to 14/21/28/35%", b([16, 24, 32, 40], [14, 21, 28, 35])))
    W(ul_close())

    # Chaos Knight
    W(hero_header("Chaos Knight"))
    W(ability("Chaos Bolt", slug="chaos_knight_chaos_bolt"))
    W(ul_open())
    W(li("Bolt Speed increased from 700 to 900", b(700, 900)))
    W(ul_close())

    # Clockwerk
    W(hero_header("Clockwerk"))
    W(ability("Power Cogs", slug="rattletrap_power_cogs"))
    W(ul_open())
    W(li("Mana Burn decreased from 40/80/120/160 to 40/75/110/145", b([40, 80, 120, 160], [40, 75, 110, 145])))
    W(li("Cogs Travel Distance decreased from 1000 to 850/900/950/1000", b(1000, [850, 900, 950, 1000])))
    W(li("Cogs Day/Night Vision decreased from 1600/600 to 800/400", b([1600, 600], [800, 400])))
    W(li("Cogs no longer block creep camps", t("DEL")))
    W(ul_close())

    # Death Prophet
    W(hero_header("Death Prophet"))
    W(ul_open())
    W(li("Agility gain increased from 2.0 to 2.3", b(2, 2.3)))
    W(li("Damage gain per level increased from 3.6 to 3.7", b(3.6, 3.7)))
    W(ul_close())

    # Doom
    W(hero_header("Doom"))
    W(ul_open())
    W(li("Attack Range decreased from 200 to 175", b(200, 175)))
    W(ul_close())
    W(ability("Infernal Blade", slug="doom_bringer_infernal_blade"))
    W(ul_open())
    W(li("Base Burn Damage increased from 15/30/45/60 to 18/34/50/66", b([15, 30, 45, 60], [18, 34, 50, 66])))
    W(li("Max HP As Damage rescaled from 1/2/3/4% to 0.5/1.75/3/4.25%", b([1, 2, 3, 4], [0.5, 1.75, 3, 4.25])))
    W(ul_close())

    # Dragon Knight
    W(hero_header("Dragon Knight"))
    W(ability("Wyrm's Wrath", slug="dragon_knight_wyrms_wrath"))
    W(ul_open())
    W(li("AoE Bonus increased from 25/50/75/100 to 30/60/90/120", b([25, 50, 75, 100], [30, 60, 90, 120])))
    W(ul_close())

    # Drow Ranger
    W(hero_header("Drow Ranger"))
    W(ability("Multishot", slug="drow_ranger_multishot"))
    W(ul_open())
    W(li("Arrow Range rescaled from 1.75x Drow Ranger's Attack Range to 475 + 1x Drow Ranger's Attack Range", t("REWORK"),
         extra=inline_note("At her base 625 Attack Range the arrows travel 1094 &rarr; 1100. "
                           "The two formulas break even at 633 Attack Range — with any more range the new value is lower "
                           "(with Dragon Lance's +130: 1321 &rarr; 1230)")))
    W(li("Mana Cost increased from 50/70/90/110 to 70/85/100/115", b([50, 70, 90, 110], [70, 85, 100, 115], l=True)))
    W(li("Arrow Base Damage Bonus decreased from 100/120/140/160% to 80/100/120/140%", b([100, 120, 140, 160], [80, 100, 120, 140])))
    W(ul_close())

    # Earth Spirit
    W(hero_header("Earth Spirit"))
    W(ul_open())
    W(li("Base Intelligence decreased from 18 to 17", b(18, 17)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Magnetize Damage & Duration decreased from +30% to +25%", b(30, 25)))
    W(ul_close())

    # Elder Titan
    W(hero_header("Elder Titan"))
    W(ability("Momentum", slug="elder_titan_momentum"))
    W(ul_open())
    W(li_formula("Bonus Speed to Armor increased", "5% + 0.5% per level", "7% + 0.5% per level", lambda L: 5 + 0.5*L, lambda L: 7 + 0.5*L, value_fmt="{:g}%"))
    W(ul_close())
    W(ability("Astral Spirit", slug="elder_titan_ancestral_spirit"))
    W(ul_open())
    W(li("Return Astral Spirit and Move Astral Spirit sub-abilities no longer break Elder Titan's invisibility when used", t("MISC")))
    W(ul_close())

    # Ember Spirit
    W(hero_header("Ember Spirit"))
    W(ul_open())
    W(li("Base Movement Speed decreased from 300 to 295", b(300, 295)))
    W(ul_close())

    # Grimstroke
    W(hero_header("Grimstroke"))
    W(ability("Dark Portrait", slug="grimstroke_dark_portrait"))
    W(ul_open())
    W(li("No longer has illusion vision penalty", t("DEL")))
    W(ul_close())

    # Gyrocopter
    W(hero_header("Gyrocopter"))
    W(ability("Rocket Barrage", slug="gyrocopter_rocket_barrage"))
    W(ul_open())
    W(li("Mana Cost decreased from 85 to 75", b(85, 75, l=True)))
    W(ul_close())
    W(ability("Homing Missile", slug="gyrocopter_homing_missile"))
    W(ul_open())
    W(li("Mana Cost decreased from 120/130/140/150 to 120", b([120, 130, 140, 150], 120, l=True)))
    W(li("Cooldown decreased from 30/24/18/12s to 26/21/16/11s", b([30, 24, 18, 12], [26, 21, 16, 11], l=True)))
    W(ul_close())

    # Hoodwink
    W(hero_header("Hoodwink"))
    W(ability("Mistwoods Wayfarer", slug="hoodwink_mistwoods_wayfarer"))
    W(ul_open())
    W(li_formula("Redirect Chance decreased", "14% + 1% per level", "14.25% + 0.75% per level", lambda L: 14 + 1*L, lambda L: 14.25 + 0.75*L, value_fmt="{:g}%"))
    W(ul_close())
    W(ability("Sharpshooter", slug="hoodwink_sharpshooter"))
    W(ul_open())
    W(li("Mana Cost increased from 100/150/200 to 150/200/250", b([100, 150, 200], [150, 200, 250], l=True)))
    W(ul_close())
    W(ability("Hunter's Boomerang", slug="hoodwink_hunters_boomerang"))
    W(ul_open())
    W(li("Cooldown increased from 18s to 20s", b(18, 20, l=True)))
    W(ul_close())

    # Invoker
    W(hero_header("Invoker"))
    W(ability("Ghost Walk", slug="invoker_ghost_walk"))
    W(ul_open())
    W(li("Duration decreased from 60s to 50s", b(60, 50)))
    W(li("Aghanim's Shard no longer increases radius", t("DEL")))
    W(ul_close())

    # Jakiro
    W(hero_header("Jakiro"))
    W(ul_open())
    W(li("Intelligence gain increased from 3.0 to 3.3", b(3, 3.3)))
    W(ul_close())

    # Keeper of the Light
    W(hero_header("Keeper of the Light"))
    W(ability("Chakra Magic", slug="keeper_of_the_light_chakra_magic"))
    W(ul_open())
    W(li("Cooldown increased from 19/16/13/10s to 20/17/14/11s", b([19, 16, 13, 10], [20, 17, 14, 11], l=True)))
    W(ul_close())
    W(ability("Solar Bind", slug="keeper_of_the_light_radiant_bind"))
    W(ul_open())
    W(li("Cast Range decreased from 850 to 750", b(850, 750)))
    W(ul_close())

    # Legion Commander
    W(hero_header("Legion Commander"))
    W(ul_open())
    W(li("Base Strength increased from 24 to 25", b(24, 25)))
    W(li("Damage at level 1 increased from 57-61 to 58-62", br(57, 61, 58, 62)))
    W(li("Strength gain decreased from 3.1 to 3.0", b(3.1, 3)))
    W(li("Base Attack Speed increased from 100 to 105", b(100, 105)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Duel Refreshes Cooldown On Victory replaced with Duel Advances Cooldown by 30s On Victory", t("REWORK")))
    W(ul_close())

    # Lina
    W(hero_header("Lina"))
    W(ul_open())
    W(li("Base Agility decreased from 23 to 21", b(23, 21)))
    W(ul_close())

    # Lone Druid
    W(hero_header("Lone Druid"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Savage Roar Cooldown Reduction decreased from 5s to 4s", b(5, 4)))
    W(li("Level 20 Talent Savage Roar Radius decreased from +150 to +125", b(150, 125)))
    W(ul_close())
    # Spirit Bear (Lone Druid pet — Valve lists it as hero_id 1961; rendered as a
    # unit block inside the Lone Druid section, per the 7.41c/7.41d convention).
    W(unit_header("Spirit Bear", "../icons/abilities/lone_druid_spirit_bear.png", kind="Creep-hero"))
    W(ul_open())
    W(li("Base Armor decreased by 1",
         bstat_u("npc_dota_lone_druid_bear1", "ArmorPhysical", "7.41d", -1),
         extra=note_box(unit="npc_dota_lone_druid_bear1", field="ArmorPhysical", before_patch="7.41d")))
    W(ul_close())
    W(ability("Demolish", slug="lone_druid_spirit_bear_demolish"))
    W(ul_open())
    W(li("Bonus Building Damage decreased from 30% to 20%", b(30, 20)))
    W(ul_close())

    # Magnus
    W(hero_header("Magnus"))
    W(ability("Horn Toss", slug="magnataur_horn_toss"))
    W(ul_open())
    W(li("Damage increased from 300 to 325", b(300, 325)))
    W(ul_close())

    # Mars
    W(hero_header("Mars"))
    W(ul_open())
    W(li("Intelligence gain increased from 2.2 to 2.4", b(2.2, 2.4)))
    W(ul_close())

    # Medusa
    W(hero_header("Medusa"))
    W(ability("Split Shot", slug="medusa_split_shot"))
    W(ul_open())
    W(li("Toggling on/off no longer breaks invisibility and can be done while silenced", t("MISC")))
    W(ul_close())

    # Morphling
    W(hero_header("Morphling"))
    W(ability("Morph", slug="morphling_replicate"))
    W(ul_open())
    W(li("Cooldown decreased from 140/100/60s to 125/90/55s", b([140, 100, 60], [125, 90, 55], l=True)))
    W(li("Aghanim's Scepter illusion no longer has illusion vision penalty", t("DEL")))
    W(ul_close())

    # Muerta
    W(hero_header("Muerta"))
    W(ability("Gunslinger", slug="muerta_gunslinger"))
    W(ul_open())
    W(li("Toggling on/off no longer breaks invisibility", t("MISC")))
    W(ul_close())

    # Necrophos
    W(hero_header("Necrophos"))
    W(ability("Sadist", slug="necrolyte_sadist"))
    W(ul_open())
    W(li_formula("HP/Mana Regen decreased", "3.7 + 0.3 per level", "3.8 + 0.2 per level", lambda L: 3.7 + 0.3*L, lambda L: 3.8 + 0.2*L, value_fmt="{:g}"))
    W(ul_close())
    W(ability("Death Seeker", slug="necrolyte_death_seeker"))
    W(ul_open())
    W(li("Cast Range decreased from 750 to 600", b(750, 600)))
    W(ul_close())

    # Night Stalker
    W(hero_header("Night Stalker"))
    W(ability("Crippling Fear", slug="night_stalker_crippling_fear"))
    W(ul_open())
    W(li("Radius decreased from 375 to 350", b(375, 350)))
    W(ul_close())

    # Omniknight
    W(hero_header("Omniknight"))
    W(ability("Hammer of Purity", slug="omniknight_hammer_of_purity"))
    W(ul_open())
    W(li("Heal Amount improved from 35% over 5s to 40% over 4s", t("BUFF")))
    W(ul_close())

    # Oracle
    W(hero_header("Oracle"))
    W(ability("Fate's Edict", slug="oracle_fates_edict"))
    W(ul_open())
    W(li("Fate's Edict that was cast on Oracle or his ally is now dispellable by enemies", t("NEW")))
    W(ul_close())
    W(ability("False Promise", slug="oracle_false_promise"))
    W(ul_open())
    W(li("Cast Range increased from 700/800/900 to 800/850/900", b([700, 800, 900], [800, 850, 900])))
    W(ul_close())

    # Outworld Destroyer
    W(hero_header("Outworld Destroyer"))
    W(ability("Objurgation", slug="obsidian_destroyer_objurgation"))
    W(ul_open())
    W(li("Now has an instant cast and no longer cancels movement", t("MISC"), extra=inline_note("Used to have 0.2s cast point")))
    W(li("Barrier increased from 120/180/240/300 to 150/200/250/300", b([120, 180, 240, 300], [150, 200, 250, 300])))
    W(li("Cooldown decreased from 36/34/32/30 to 36/33/30/27s", b([36, 34, 32, 30], [36, 33, 30, 27], l=True)))
    W(ul_close())

    # Phantom Assassin
    W(hero_header("Phantom Assassin"))
    W(ability("Blur", slug="phantom_assassin_blur"))
    W(ul_open())
    W(li("Now cannot be dispelled", t("NEW")))
    W(ul_close())

    # Phantom Lancer
    W(hero_header("Phantom Lancer"))
    W(ability("Juxtapose", slug="phantom_lancer_juxtapose"))
    W(ul_open())
    W(li("Aghanim's Shard cooldown increased from 15s to 18s", b(15, 18, l=True)))
    W(ul_close())

    # Puck
    W(hero_header("Puck"))
    W(ability("Illusory Orb", slug="puck_illusory_orb"))
    W(ul_open())
    W(li("Cooldown increased from 11/10/9/8s to 12/11/10/9s", b([11, 10, 9, 8], [12, 11, 10, 9], l=True)))
    W(ul_close())

    # Pugna
    W(hero_header("Pugna"))
    W(ul_open())
    W(li("Base Intelligence increased from 26 to 27", b(26, 27)))
    W(ul_close())

    # Queen of Pain
    W(hero_header("Queen of Pain"))
    W(ability("Shadow Strike", slug="queenofpain_shadow_strike"))
    W(ul_open())
    W(li("Mana Cost decreased from 100/110/120/130 to 100/105/110/115", b([100, 110, 120, 130], [100, 105, 110, 115], l=True)))
    W(ul_close())
    W(ability("Sonic Wave", slug="queenofpain_sonic_wave"))
    W(ul_open())
    W(li("Damage from two Sonic Waves cast in quick succession now stack", t("NEW")))
    W(ul_close())

    # Ringmaster
    W(hero_header("Ringmaster"))
    W(ability("Impalement Arts", slug="ringmaster_impalement"))
    W(ul_open())
    W(li("Damage per Second (Creeps) rescaled from 85/90/95/100 to 60/75/90/105", b([85, 90, 95, 100], [60, 75, 90, 105])))
    W(ul_close())

    # Shadow Fiend
    W(hero_header("Shadow Fiend"))
    W(ul_open())
    W(li("Base Intelligence decreased from 18 to 16", b(18, 16)))
    W(ul_close())
    W(ability("Shadowraze", slug="nevermore_shadowraze1"))
    W(ul_open())
    W(li("Stack duration decreased from 7s to 6s", b(7, 6)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Shadowraze Applies Attack Damage no longer applies attack modifiers or procs", t("DEL")))
    W(ul_close())

    # Snapfire
    W(hero_header("Snapfire"))
    W(ability("Scatterblast", slug="snapfire_scatterblast"))
    W(ul_open())
    W(li("Initial Blast Width is no longer increased by bonuses to AoE", t("DEL")))
    W(li("Point Blank Damage Bonus decreased from 30% to 25%", b(30, 25)))
    W(ul_close())
    W(ability("Firesnap Cookie", slug="snapfire_firesnap_cookie"))
    W(ul_open())
    W(li("Impact Damage decreased from 75/150/225/300 to 60/130/200/270", b([75, 150, 225, 300], [60, 130, 200, 270])))
    W(ul_close())
    W(ability("Mortimer Kisses", slug="snapfire_mortimer_kisses"))
    W(ul_open())
    W(li("Damage per glob decreased from 180/270/360 to 170/250/330", b([180, 270, 360], [170, 250, 330])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Mortimer Kisses Burn DPS decreased from +35 to +30", b(35, 30)))
    W(li("Level 15 Talent -3s Firesnap Cookie Cooldown replaced with +125 Cast Range", t("REWORK")))
    W(li("Level 25 Talent Mortimer Kisses Launched decreased from +8 to +6", b(8, 6)))
    W(ul_close())

    # Sniper
    W(hero_header("Sniper"))
    W(ability("Concussive Grenade", slug="sniper_concussive_grenade"))
    W(ul_open())
    W(li("Can now be cast while rooted, but will not knock Sniper back if he is under the effect of root", t("MISC")))
    W(ul_close())

    # Spectre
    W(hero_header("Spectre"))
    W(ability("Haunt", slug="spectre_haunt"))
    W(ul_open())
    W(li("Illusion Damage rescaled from 30/50/70% to 35/50/65%", b([30, 50, 70], [35, 50, 65])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent All Spectre Illusion Damage decreased from +15% to +12%", b(15, 12)))
    W(ul_close())

    # Templar Assassin
    W(hero_header("Templar Assassin"))
    W(ability("Psionic Projection", slug="templar_assassin_trap_teleport"))
    W(ul_open())
    W(li("Can now be interrupted by root", t("MISC")))
    W(ul_close())

    # Tiny
    W(hero_header("Tiny"))
    W(ul_open())
    W(li("Base Health Regen decreased by 1.0", bstat_h("Tiny", "StatusHealthRegen", "7.41d", -1), extra=note_box(hero="Tiny", field="StatusHealthRegen", before_patch="7.41d")))
    W(ul_close())

    # Treant Protector
    W(hero_header("Treant Protector"))
    W(ul_open())
    W(li("Base Attack Speed decreased from 100 to 90", b(100, 90)))
    W(ul_close())
    W(ability("Leech Seed", slug="treant_leech_seed"))
    W(ul_open())
    W(li("Root duration decreased from 0.9/1.1/1.3/1.5s to 0.75/1.0/1.25/1.5s", b([0.9, 1.1, 1.3, 1.5], [0.75, 1, 1.25, 1.5])))
    W(ul_close())
    W(ability("Living Armor", slug="treant_living_armor"))
    W(ul_open())
    W(li("Mana Cost increased from 65/70/75/80 to 80", b([65, 70, 75, 80], 80, l=True)))
    W(ul_close())

    # Troll Warlord
    W(hero_header("Troll Warlord"))
    W(ul_open())
    W(li("Base Agility increased from 23 to 24", b(23, 24)))
    W(li("Damage at level 1 increased from 50-58 to 51-59", br(50, 58, 51, 59)))
    W(ul_close())
    W(ability("Battle Stance", slug="troll_warlord_switch_stance"))
    W(ul_open())
    W(li("Toggling between stances no longer breaks invisibility", t("MISC")))
    W(ul_close())
    W(ability("Battle Trance", slug="troll_warlord_battle_trance"))
    W(ul_open())
    W(li("Now also grants 35% Slow Resistance", t("NEW")))
    W(ul_close())

    # Underlord
    W(hero_header("Underlord"))
    W(ability("Fiend's Gate", slug="abyssal_underlord_dark_portal"))
    W(ul_open())
    W(li("Gate channeling can now be interrupted by root", t("MISC")))
    W(ul_close())

    # Undying
    W(hero_header("Undying"))
    W(ul_open())
    W(li("Base Movement Speed decreased from 300 to 295", b(300, 295)))
    W(ul_close())
    W(ability("Flesh Golem", slug="undying_flesh_golem"))
    W(ul_open())
    W(li("Bonus Movement Speed increased from 20 to 25", b(20, 25)))
    W(ul_close())

    # Vengeful Spirit
    W(hero_header("Vengeful Spirit"))
    W(ability("Vengeance Aura", slug="vengefulspirit_command_aura"))
    W(ul_open())
    W(li("Aghanim's Scepter illusion no longer has illusion vision penalty", t("DEL")))
    W(ul_close())

    # Venomancer
    W(hero_header("Venomancer"))
    W(ability("Snakebite", slug="venomancer_snakebite"))
    W(ul_open())
    W(li("Initial Damage increased from 40/60/80/100 to 40/70/100/130", b([40, 60, 80, 100], [40, 70, 100, 130])))
    W(ul_close())

    # Visage
    W(hero_header("Visage"))
    W(ability("Stone Form", slug="visage_stone_form_self_cast"))
    W(ul_open())
    W(li("No longer breaks Visage's invisibility when used to order Familiars to execute", t("MISC")))
    W(ul_close())

    # Weaver
    W(hero_header("Weaver"))
    W(ability("Threads of Fate", slug="weaver_threads_of_fate"))
    W(ul_open())
    W(li_formula("Thread Break Distance increased", "900", "890 + 10 per hero level",
                 lambda L: 900, lambda L: 890 + 10*L))
    W(ul_close())

    # Witch Doctor
    W(hero_header("Witch Doctor"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Maledict bursts deal 75% damage in a 800 AoE now considers illusions as creep targets and bursts from them will not deal damage", t("REWORK")))
    W(ul_close())

    # Zeus
    W(hero_header("Zeus"))
    W(ability("Thundergod's Wrath", slug="zuus_thundergods_wrath"))
    W(ul_open())
    W(li("Damage decreased from 300/475/650 to 275/425/575", b([300, 475, 650], [275, 425, 575])))
    W(ul_close())
    W(ability("Lightning Hands", slug="zuus_lightning_hands"))
    W(ul_open())
    W(li("Bonus Attack Speed decreased from 30 to 20", b(30, 20)))
    W(li("Toggling on/off no longer breaks invisibility and can be done while silenced", t("MISC")))
    W(ul_close())

    write_footer()
    save_html('patches/7.41e.html')
