from patch.api import *

def build():
    write_head("7.41", "24.03.2026")

    # ===== GENERAL UPDATES =====
    W(section("General Updates"))

    W(plain_header("Global Changes"))
    W(ul_open())
    W(li("Facets removed from the game", t("DEL")))
    W(li("Innate abilities no longer scale with other abilities' level", t("REWORK")))
    W(li("All innate abilities that used to scale with other abilities now either provide unchangeable bonuses or improve on 'per level' basis", t("REWORK"),
         extra=inline_note(
             "Abilities that improve with hero level have a <b>base value</b> and an <b>increment value</b>. Some also specify the <b>number of levels required per increment</b>."
             "<br>Abilities that improve every level provide their increment value already at level 1."
         )))
    W(li("Added UI icon that shows you which parameters increase with hero level and what is the current value. Some non-innate ability might have this per level UI as well", t("QoL"),
         extra=inline_note("Pressing ALT key will show base value and increment of the ability.")))
    W(li("Abilities that had 'per level up' scaling changed to be 'per level'", t("MISC"),
         extra=inline_note("This mostly affects heroes reworked in update 7.40 and Largo.")))
    W(li("Flagbearer Creep Experience Bounty increased from 57 to 60", b(57, 60)))
    W(li("First +1 siege creep timing decreased from 35:00 to 30:00", b(35, 30, l=True)))
    W(li("Second +1 siege creep timing now occurs at 60:00", t("NEW")))
    W(li("Adjusted the meeting point of the lane creeps toward the offlane", t("MISC"),
         extra=inline_note(
             "Now offlane creeps are slightly slowed upon leaving the base for a couple of seconds. Safe lane creeps are slightly accelerated upon leaving the base for a couple of seconds. Both of these changes are effective until the 7:30 mark."
         )))
    W(li("All sections of currents now give a max movement speed bonus of 150", t("BUFF"),
         extra=inline_note("Previously was only provided by sections on the base and near it, while other sections provided max bonus of 100.")))
    W(ul_close())
    W(plain_header("Map Objectives"))

    W(subgroup("Tormentor"))
    W(ul_open())
    W(li("Tormentor's spawn preference has switched", t("MISC"),
         extra=inline_note("Now begins in the Bottom Chasm.")))
    W(li("Unyielding Shield Base barrier increased from 2000 to 3000", b(2000, 3000)))
    W(li("Unyielding Shield Barrier upgrade per minute increased from 20 to 50", b(20, 50)))
    W(li("Unyielding Shield Base barrier regen decreased from 40 to 20", b(40, 20)))
    W(li_formula("Unyielding Shield Barrier regen upgrade increased",
                 "3.5 per minute", "5 per minute",
                 lambda M: 3.5 * M, lambda M: 5.0 * M,
                 levels=[0, 5, 10, 15, 20, 25, 30, 40, 50, 60],
                 level_prefix='M', rework_badge=False))
    W(li("Reflect Base damage reflection percentage decreased from 50% to 30%", b(50, 30)))
    W(li("Reflect radius can now be seen by holding ALT key", t("QoL")))
    W(li_formula("The Shining damage rescaled",
                 "60",
                 "20 + 2 per minute",
                 lambda M: 60,
                 lambda M: 20 + 2 * M,
                 levels=[0, 5, 10, 15, 20, 25, 30, 40, 50, 60],
                 level_fmt=lambda M: f"{M}:00",
                 rework_badge=False,
                 headline_level=30))
    W(li("Now has 25% Status Resistance", t("NEW")))
    W(li("No longer deals damage to neutral units", t("DEL")))
    W(li("Player that got Aghanim's Shard will no longer receive 175 gold", t("DEL"),
         extra=inline_note(
             f'Total team gold reward decreased from <b>875 to 700</b> {b(875, 700)}'
             f' (total networth change decreased from <b>2275 to 2100</b> {b(2275, 2100)}).'
         )))
    W(li("Reward if all players have Aghanim's Shard decreased from 455 gold to 415 gold", b(455, 415)))
    W(ul_close())

    W(subgroup("Roshan"))
    W(ul_open())
    W(li("Roshan's pit preference has switched", t("MISC"),
         extra=inline_note("Now begins in the Top Pit.")))
    W(ul_close())

    W(subgroup("Wisdom Shrines"))
    W(ul_open())
    W(li("Wisdom Shrines and Lotus Pools now reverse their countdowns if heroes from opposing teams enter the area, instead of pausing the countdown", t("REWORK")))
    W(li_formula("Wisdom Shrine Experience changed",
                 "280 per interval",
                 "200 base and 300 per subsequent shrine",
                 lambda N: 280 * N,
                 lambda N: 200 + 300 * (N - 1),
                 levels=[1, 2, 3, 4, 5, 6, 7],
                 level_fmt=lambda N: f"#{N}",
                 rework_badge=False,
                 headline_level=2))
    W(ul_close())
    W(plain_header("Terrain Changes", terrain_link="7.41"))
    W(subgroup("Trees"))
    W(ul_open())
    W(li("Removed several trees from Dire Safelane easy pull camp and Radiant Safelane hard pull camp", t("DEL")))
    W(ul_close())
    W(subgroup("Towers"))
    W(ul_open())
    W(li("The tier 1 safe lane towers have been moved slightly away from their pull camps and where the creeps meet", t("MISC")))
    W(li("Radiant offlane tier 2 tower has been adjusted slightly to the left, such that creeps do not path on both sides of the tower", t("MISC")))
    W(ul_close())
    W(subgroup("Camps"))
    W(ul_open())
    W(li("Radiant safe lane small camp has been slightly moved north away from the lane", t("MISC")))
    W(li("Radiant safe lane hard camp's spawn box has been moved towards the offlane to remove a bad ward location", t("MISC")))
    W(li("The medium flooded camp near the safe lane tier 2 towers moved closer to the middle of the stream (substantially more for Dire than for Radiant)", t("MISC")))
    W(li("The medium flooded camp near the safe lane tier 2 towers can now only evolve once into a hard camp, rather than into an Ancient Camp", t("NERF")))
    W(li("The medium flooded camp near the bounty runes can now evolve twice into an Ancient Camp", t("REWORK")))
    W(li("Ancient neutral camps near stream ends demoted to medium camps and moved slightly towards bases", t("NERF")))
    W(li("Medium neutral camp near offlane defender's gate has been demoted to a small neutral camp", t("NERF")))
    W(ul_close())
    W(subgroup("Watchers"))
    W(ul_open())
    W(li("The watcher between the safe lane tier 1 tower and the tormentor has been repositioned", t("MISC"),
         extra=inline_note(
             "Tormentor is on the low ground which has three stairs: one leading to the Lotus Pool, one leading to the lane, and one leading to even higher ground area with the Twin Gate."
             "<br>Twin Gate highground area is now smaller and has three stairs: one that leads to new Tormentor area, one that leads back to the lane, and one that goes two levels down straight to the end of the stream."
             "<br>Watcher is now between two stairs: one that goes down to the Tormentor and one that goes up to the Twin Gate."
         )))
    W(ul_close())
    W(subgroup("Twin Gate"))
    W(ul_open())
    W(li("Twin Gates slightly moved away from the stairs towards the map border", t("MISC")))
    W(ul_close())
    W(subgroup("Tormentor"))
    W(ul_open())
    W(li("Tormentor spawns have been positioned closer towards Lotus Pools", t("MISC")))
    W(li("Tormentor spawn areas have been reduced to low ground relative to the lane's level", t("MISC")))
    W(ul_close())
    W(subgroup("Other"))
    W(ul_open())
    W(li("Lotus Pools have been moved slightly closer to their respective offlane tower", t("MISC")))
    W(li("The ramp leading from the Radiant tier 1 tower to the stream has been decreased in width and moved away from the tower", t("MISC")))
    W(ul_close())
    W(plain_header("Mechanics Changes"))

    W(subgroup("Health Restoration"))
    W(ul_open())
    W(li("Health Restoration now applies to all forms of life gain", t("REWORK"), extra=inline_note("Previously, it did not apply to incoming heals")))
    W(ul_close())
    W(ul_open())
    W(li("Incoming Heal Amplification now stacks diminishingly with Health Restoration instead of additively with Outgoing Heal Amplification", t("REWORK")))
    W(li("Spells that previously had a separate value for incoming heal reduction now only modify Health Restoration " + info_tip(
            "Eye of Skadi's Cold Attack", "Spirit Vessel's Soul Release",
            "Omniknight's Guardian Angel with Aghanim's Scepter", "Pudge's Rot with Aghanim's Scepter",
            header="Affected spells:"), t("REWORK")))
    W(ul_close())
    W(ul_open())
    W(li("As a result of the changes, spells that only modified Health Restoration will now additionally affect incoming heals " + info_tip(
            "Sange", "Kaya and Sange", "Sange and Yasha", "Abyssal Blade", "Orb of Frost's Frost",
            "Orb of Corrosion's Corrosion", "Crippling Crossbow's Hobble", "Jidi Pollen Bag's Pollinate",
            "Item bonus from Crude enchantment", "Abaddon’s Withering Mist",
            "Drow Ranger’s Frost Arrows with Aghanim’s Scepter", "Slark's Saltwater Shiv",
            header="Affected spells:"), t("REWORK")))
    W(ul_close())

    W(subgroup("Lifesteal and Damage Manipulations"))
    W(ul_open())
    W(li("Physical and Magical Lifesteal will now take into account overall damage reductions/amplifications when computing how much to lifesteal " + info_tip(
            "Aeon Disk", "Bloodstone", "Consecrated Wraps", "Veil of Discord", "Prophet's Pendulum",
            "Audacious Enchantment", "Abaddon's Borrowed Time with Aghanim's Scepter", "Beastmaster's Wild Axes",
            "Bounty Hunter's Shadow Walk with talent", "Bristleback's Bristleback", "Centaur Warrunner's Stampede",
            "Grimstroke's Ink Trail", "Grimstroke's Soulbind with talent", "Hoodwink's Hunter's Boomerang",
            "Leshrac's Pulse Nova with talent", "Lich's Frost Shield", "Luna's Lunar Orbit",
            "Kunkka's Admiral's Rum", "Mars' Bulwark", "Nyx Assassin's Burrow", "Ogre Magi's Fire Shield",
            "Oracle's False Promise", "Pudge's Flesh Heap", "Shadow Demon's Menace", "Spectre's Dispersion",
            "Treant Protector's Living Armor", "Underlord's Invading Force", "Undying's Flesh Golem",
            "Ursa's Enrage", "Visage's Gravekeeper's Cloak", "Warlock's Golem with talent",
            header="This affects the following:"), t("REWORK")))
    W(ul_close())
    W(ul_open())
    W(li("Historically, Lifesteal was calculated before some damage reductions or amplifications were applied. As a result, you could gain health from attacks that dealt no damage (like attacks against a hero affected by Aeon Disk's Combo Breaker). This will not happen anymore", t("REWORK"), extra=inline_note("The only amplification that is not taken into account is increased damage against illusions")))
    W(ul_close())

    W(subgroup("Miscellaneous"))
    W(ul_open())
    W(li("Reflected damage cannot be reflected back", t("NEW")))
    W(li("Lifesteal and Spell Lifesteal don't apply to reflected damage", t("NEW")))
    W(li("Reflected damage doesn't affect Debuff Immune units", t("NEW")))
    W(li("Units with free movement now can miss their attacks when attacking uphill targets " + info_tip(
            "Batrider during Firefly", "Dragon Knight during Elder Dragon Form with Aghanim's Scepter",
            "Lina during Flame Cloak", "Terrorblade's Reflection illusions",
            header="Affected units:"), t("NEW")))
    W(li("All sources of reflection damage now have an ALT-note detailing mechanics of reflected damage " + info_tip(
            "Tormentor's Reflect ability", "Blade Mail (both active and passive)", "Chipped Vest", "Rattlecage",
            "Axe's Counter Helix", "Bristleback's Quill Spray triggered by Bristleback passive",
            "Centaur Warrunner's Retaliate", "Nyx Assassin's Spiked Carapace", "Queen of Pain's Scream of Pain",
            "Razor's Storm Surge", "Shadow Demon's Disseminate", "Spectre's Dispersion",
            "Tidehunter's Anchor Smash triggered by Kraken Shell passive", "Viper's Corrosive Skin",
            "Warlock's Fatal Bonds",
            header="The following items and abilities deal reflected damage:"), t("QoL")))
    W(ul_close())

    # ===== NEUTRAL CREEP UPDATES =====
    W(section("Neutral Creep Updates"))
    _NC_CDN = "../icons/units/npc_dota_neutral_"
    W(unit_header("Kobold Foreman", _NC_CDN + "kobold_taskmaster.png"))
    W(ul_open())
    W(li("Damage increased from 22–24 to 24–26", b(23, 25)))
    W(ul_close())
    W(unit_header("Kobold Soldier", _NC_CDN + "kobold_tunneler.png"))
    W(ul_open())
    W(li("Damage increased from 20–21 to 22–23", b(20.5, 22.5)))
    W(ul_close())
    W(unit_header("Kobold", _NC_CDN + "kobold.png"))
    W(ul_open())
    W(li("Damage increased from 13–14 to 15–16", b(13.5, 15.5)))
    W(ul_close())
    W(unit_header("Vhoul Assassin", _NC_CDN + "gnoll_assassin.png"))
    W(ul_open())
    W(li("Damage decreased from 30–32 to 25–27", b(31, 26)))
    W(ul_close())
    W(unit_header("Ghost Scepter", _NC_CDN + "ghost.png"))
    W(ul_open())
    W(li("Damage decreased from 45–50 to 38–43", b(47.5, 40.5)))
    W(ul_close())
    W(unit_header("Harpy Stormcrafter", _NC_CDN + "harpy_storm.png"))
    W(ability("Chain Lightning", icon_url="../icons/abilities/harpy_storm_chain_lightning.png"))
    W(ul_open())
    W(li("Damage rescaled from 140/180/220/260 to 120/170/220/270", b([140, 180, 220, 260], [120, 170, 220, 270])))
    W(ul_close())
    W(unit_header("Satyr Tormenter", _NC_CDN + "satyr_hellcaller.png"))
    W(ability("Shockwave", icon_url="../icons/abilities/satyr_hellcaller_shockwave.png"))
    W(ul_open())
    W(li("Damage rescaled from 160 to 140/160/180/200", b(160, [140, 160, 180, 200])))
    W(ul_close())
    W(unit_header("Warpine Raider", _NC_CDN + "warpine_raider.png"))
    W(ability("Seed Shot", icon_url="../icons/abilities/warpine_raider_seed_shot.png"))
    W(ul_open())
    W(li("Damage rescaled from 100 to 80/95/110/125", b(100, [80, 95, 110, 125])))
    W(ul_close())
    W(unit_header("Boglet", _NC_CDN + "froglet.png"))
    W(ability("Arm of the Deep", icon_url="../icons/abilities/frogmen_arm_of_the_deep.png"))
    W(ul_open())
    W(li("After neutrals cast this ability, all copies of Arm of the Deep, Tendrils of the Deep, and Congregations of the Deep on other neutral Boglets, Croakers, and Ancient Croakers within 1200 range are put on 5s cooldown", t("MISC")))
    W(ul_close())
    W(subnote("Previously affected other copies of this ability"))
    W(unit_header("Croaker", _NC_CDN + "grown_frog.png"))
    W(ability("Tendrils of the Deep", icon_url="../icons/abilities/frogmen_tendrils_of_the_deep.png"))
    W(ul_open())
    W(li("After neutrals cast this ability, all copies of Arm of the Deep, Tendrils of the Deep, and Congregations of the Deep on other neutral Boglets, Croakers, and Ancient Croakers within 1200 range are put on 5s cooldown", t("MISC")))
    W(ul_close())
    W(subnote("Previously affected other copies of this ability"))
    W(unit_header("Ancient Croaker", _NC_CDN + "ancient_frog.png"))
    W(ability("Congregations of the Deep", icon_url="../icons/abilities/frogmen_congregation_of_the_deep.png"))
    W(ul_open())
    W(li("After neutrals cast this ability, all copies of Arm of the Deep, Tendrils of the Deep, and Congregations of the Deep on other neutral Boglets, Croakers, and Ancient Croakers within 1200 range are put on 5s cooldown", t("MISC")))
    W(ul_close())
    W(subnote("Previously affected other copies of this ability"))
    W(ul_open())
    W(li("Radius is now affected by Area of Effect bonuses", t("BUFF")))
    W(ul_close())
    W(unit_header("Ancient Marshmage", _NC_CDN + "ancient_frog_mage.png"))
    W(ability("Water Bubble (Large)", icon_url="../icons/abilities/frogmen_water_bubble_large.png"))
    W(ul_open())
    W(li("Radius is now affected by Area of Effect bonuses", t("BUFF")))
    W(ul_close())

    # ===== ITEM UPDATES =====
    W(section("Item Updates"))

    W(plain_header("Shop Reshuffle", dynamics=False, sublabel=True))
    W(ul_open())
    W(li("Items in all shop categories except for Consumables have been rearranged to accommodate new items", t("QoL")))
    W(li("Consumables now includes Infused Raindrops", t("QoL")))
    W(ul_close())

    W(plain_header("Basic Items", dynamics=False, sublabel=True))
    W(item_header("Chasm Stone", new="New Miscellaneous Item"))
    W(item_cost(800))
    W(provides('+40 Area of Effect ' + info_tip("Area of Effect bonuses from multiple Chasm Stones or its upgrades do not stack")))
    W(item_header("Shawl", new="New Miscellaneous Item"))
    W(item_cost(450))
    W(provides('+10% Magic Resistance'))
    W(item_header("Splintmail", new="New Equipment Item"))
    W(item_cost(950))
    W(provides('+7 Armor'))
    W(item_header("Wizard Hat", new="New Miscellaneous Item"))
    W(item_cost(250))
    W(provides('+125 Mana'))
    W(item_header("Chainmail"))
    W(ul_open())
    W(li("Cost decreased from 550g to 500g", b(550, 500, l=True)))
    W(ul_close())
    W(item_header("Cloak"))
    W(ul_open())
    W(li("Cost increased from 800g to 900g", b(800, 900, l=True)))
    W(li("Magic Resistance bonus decreased from +20% to +18%", b(20, 18, l=True)))
    W(ul_close())
    W(item_header("Cornucopia"))
    W(ul_open())
    W(li("Item removed from the game", t("DEL")))
    W(ul_close())
    W(item_header("Orb of Frost"))
    W(ul_open())
    W(li("Now also modifies incoming healing", t("NEW"),
         extra=inline_note("As a result of Health Restoration changes")))
    W(ul_close())
    W(item_header("Refresher Shard"))
    W(ul_open())
    W(li("Reset Cooldowns no longer refreshes items", t("DEL")))
    W(ul_close())
    W(item_header("Ring of Health"))
    W(ul_open())
    W(li("Item moved back to Secret Shop from Miscellaneous Shop", t("MISC")))
    W(ul_close())
    W(item_header("Void Stone"))
    W(ul_open())
    W(li("Item moved back to Secret Shop from Miscellaneous Shop", t("MISC")))
    W(ul_close())
    W(item_header("Voodoo Mask"))
    W(ul_open())
    W(li("Spell Lifesteal bonus increased from +12% to +15%", b(12, 15)))
    W(ul_close())

    W(plain_header("Upgrades", dynamics=False, sublabel=True))
    W(item_header("Consecrated Wraps", new="New Armor Item"))
    W(components(('Vitality Booster', 1000), ('Shawl', 450), ('Crown', 450),
                 recipe=('Recipe', 700), total=2600))
    W(provides('+15% Magic Resistance, +250 Health, +6 All Attributes'))
    W(ul_open())
    W(li("Passive: Hallowed. Gain a stack every 3s, up to a maximum of 3 stacks. Whenever the wearer takes damage from a player-controlled unit or Roshan, all stacks are removed to create an all-damage barrier for 7s that absorbs 120 damage per removed stack (up to 360). If the wearer reached a max amount of stacks at least once in a game, regaining a stack provides a non-stacking buff that increases movespeed by 20% for 7s", t("NEW")))
    W(li("Has no damage threshold, but doesn't proc from Health Loss damage (like Heartstopper Aura)", t("NEW")))
    W(li("Can't gain stacks for 3s after taking damage from Roshan or player-controlled sources", t("NERF")))
    W(ul_close())
    W(item_header("Crella's Crozier", new="New Magical Item"))
    W(components(('Ghost Scepter', 1500), ('Soul Booster', 3000),
                 recipe=('Recipe', 300), total=4800))
    W(provides('+6 All Attributes, +450 Health, +450 Mana'))
    W(ul_open())
    W(li("Active: Rite of Rumusque. The wearer enters ghost form for 4 seconds, becoming immune to physical damage, but is unable to attack and 30% more vulnerable to magic damage. Steals 5% movement speed from enemy heroes in a 900 radius every second. Movement speed steal lasts 1.5s. Bonuses stack and have duration refreshed on gaining new stacks. No Mana Cost. Cooldown: 20s", t("NEW")))
    W(li("The ghost form and stolen speed can be dispelled off the wearer, but the stealing debuff that provides new stacks can't", t("NERF")))
    W(li("Passive: Putrefaction Aura. Reduces health restoration of nearby enemy heroes by 30%. While Rite of Rumusque is active, the effect is increased to 75% and all of the lost Health Restoration is redirected to the wearer every second. Radius: 900", t("BUFF")))
    W(ul_close())
    W(item_header("Essence Distiller", new="New Support Item"))
    W(components(('Urn of Shadows', 825), ('Chainmail', 500), ('Wizard Hat', 250),
                 recipe=('Recipe', 200), total=1775))
    W(provides('+1.75 Mana Regen, +3 All Attributes, +6 Armor, +150 Mana'))
    W(ul_open())
    W(li("Active: Soul Release. When cast on an ally, provides 40 health regeneration. If the ally is attacked by an enemy hero or Roshan, the effect is lost. When cast on an enemy, deals 25 damage per second, provides True Sight over them and shares their vision with the wearer's team. Both effects last 8 seconds. Can be cast on the ground to put a dormant effect that will latch to the first enemy hero that comes within 400 range from it. The effect waits for 15s and provides 400 vision until it disappears. Gains charges every time an enemy hero dies within 1500 units. Cast Range: 1000. No Mana Cost. Cooldown: 10s", t("NEW")))
    W(li("Gains one charge if the wearer dies with an empty Essence Distiller", t("NEW")))
    W(li("Gains two charges if Essence Distiller had no charges and an enemy hero dies within radius", t("NEW")))
    W(ul_close())
    W(item_header("Specialist's Array", new="Returning Armaments Item"))
    W(components(('Blade of Alacrity', 1000), ('Broadsword', 1000),
                 recipe=('Recipe', 550), total=2550))
    W(provides('+20 Damage, +12 Agility'))
    W(ul_open())
    W(li("Passive: Splitshot. Ranged Only. Ranged attacks have a 30% chance to fire additional projectiles at up to 2 nearby enemies that aren't the original attack target within 120 degree angle in front of the wearer and within attack range + 150. The additional projectiles deal 20 + 75% damage of a normal attack and do not trigger on hit effects. The primary attack deals 20 + full damage of a normal attack when the ability procs", t("NEW")))
    W(li("Doesn't work with other sources of secondary projectiles from hero abilities " + info_tip(
            "Gyrocopter's Flak Cannon", "Medusa's Split Shot", "Muerta's Gunslinger",
            header="Affected abilities:"),
         t("NEW")))
    W(ul_close())
    W(item_header("Hydra's Breath", new="New Armaments Item"))
    W(components(("Specialist's Array", 2550), ('Dragon Lance', 1900), ('Orb of Venom', 350),
                 recipe=('Recipe', 1100), total=5900))
    W(provides('+25 Damage, +30 Agility, +15 Strength, +150 Attack Range (Ranged Only)'))
    W(ul_open())
    W(li("Passive: Miasma. Attacks poison the target for 3 seconds, dealing magical damage equal to 2.5% of the target's max health every second. If the debuff is reapplied, the duration is refreshed. Can't be applied by illusions or to Roshan", t("NEW")))
    W(li("Passive: Polycephaly. Ranged attacks have a 30% chance to fire at up to 3 nearby enemies that aren't the original attack target within 120 degree angle in front of the wearer and within attack range + 150. The additional projectiles deal 20 + 75% damage of a normal attack and do not trigger on hit effects except for Miasma. The primary attack deals 20 + full damage of a normal attack when the ability procs", t("NEW")))
    W(li("Similarly to Specialist's Array, doesn't work with other sources of secondary projectiles from hero abilities", t("NEW")))
    W(ul_close())
    W(item_header("Arcane Boots", changed=True))
    W(auto_components_change("Arcane Boots", "7.41"))
    W(properties_change(
        old=[],
        new=[("NEW", "+125 Mana")]))
    W(ul_open())
    W(li("Recipe cost decreased from 475 to 325 " + b(475, 325, l=True) + ". Total cost increased from 1400g to 1500g", b(1400, 1500, l=True)))
    W(ul_close())
    W(item_header("Guardian Greaves"))
    W(ul_open())
    W(li("Recipe cost increased from 1125 to 1175 " + b(1125, 1175, l=True) + ". Total cost increased from 4300g to 4450g (due to Arcane Boots cost increase)", b(4300, 4450, l=True)))
    W(li("Mana Regen bonus decreased from +1.5 to +1", b(1.5, 1)))
    W(li("Now also provides +150 Mana", t("NEW")))
    W(ul_close())
    W(item_header("Battle Fury", changed=True))
    W(auto_components_change("Battle Fury", "7.41"))
    W(ul_open())
    W(li("Recipe cost decreased from 600 to 400 " + b(600, 400, l=True) + ". Total cost unchanged at 3900g", t("MISC")))
    W(ul_close())
    W(item_header("Black King Bar"))
    W(ul_open())
    W(li("Avatar duration changed from 9/8/7/6s to 9/8/7s", t("REWORK")))
    W(ul_close())
    W(item_header("Blade Mail", changed=True))
    W(auto_components_change("Blade Mail", "7.41"))
    W(properties_change(
        old=[("BUFF", "+6 Armor")],
        new=[("",     "+7 Armor", b(6, 7))]))
    W(ul_open())
    W(li("Recipe cost decreased from 750 to 450 " + b(750, 450, l=True) + ". Total cost increased from 2300g to 2400g", b(2300, 2400, l=True)))
    W(ul_close())
    W(item_header("Crimson Guard"))
    W(ul_open())
    W(li("Armor bonus decreased from +8 to +6", b(8, 6)))
    W(li("Guard max health damage block decreased from 2.2% to 2%", b(2.2, 2)))
    W(li("Guard base damage block rescaled from 70 for all units to 70 on melee heroes and buildings and 45 on ranged heroes", t("REWORK")))
    W(ul_close())
    W(item_header("Dagon", changed=True))
    W(auto_components_change("Dagon", "7.41"))
    W(properties_change(
        old=[("NERF", "+7/9/11/13/15 All Attributes"),
             ("DEL",  "+15/16/17/18/19% Spell Lifesteal")],
        new=[("",    "+6/7/8/9/10 All Attributes", b([7, 9, 11, 13, 15], [6, 7, 8, 9, 10])),
             ("NEW", "+200/210/220/230/240 Health"),
             ("NEW", "+350/375/400/425/450 Mana"),
             ("NEW", "+60/90/120/150/180 Cast Range " + info_tip(
                 "Cast Range Bonus does not stack with Aether Lens or multiple Dagons",
                 header="Stacking rules"))]))
    W(ul_open())
    W(li("Recipe cost unchanged at 1150. Total cost increased from 2800/3950/5100/6250/7400g to 3050/4200/5350/6500/7650g", b([2800, 3950, 5100, 6250, 7400], [3050, 4200, 5350, 6500, 7650], l=True)))
    W(li("Energy Burst cast range decreased from 700/750/800/850/900 to 640", b([700, 750, 800, 850, 900], 640)))
    W(li("Effective cast range with item's built-in Cast Range bonus decreased from 700/750/800/850/900 to 700/730/760/790/820", b([700, 750, 800, 850, 900], [700, 730, 760, 790, 820])))
    W(li("Energy Burst no longer instantly kills non-ancient creeps", t("DEL")))
    W(li("Energy Burst no longer heals for 75% of damage dealt", t("DEL")))
    W(ul_close())
    W(item_header("Dragon Lance"))
    W(ul_open())
    W(li("Ranged Attack Range bonus decreased from +140 to +130", b(140, 130)))
    W(ul_close())
    W(item_header("Hurricane Pike"))
    W(ul_open())
    W(li("Ranged Attack Range bonus decreased from +140 to +130", b(140, 130)))
    W(li("Hurricane Thrust cast range on enemies decreased from 450 to 425", b(450, 425)))
    W(li("Hurricane Thrust enemy push distance decreased from 450 to 425", b(450, 425)))
    W(ul_close())
    W(item_header("Drum of Endurance", changed=True))
    W(auto_components_change("Drum of Endurance", "7.41"))
    W(properties_change(
        old=[("BUFF", "+7 Strength"),
             ("DEL",  "+7 Intelligence")],
        new=[("",     "+8 Strength", b(7, 8))]))
    W(ul_open())
    W(li("Endurance now shares cooldown with Boots of Bearing", t("NERF")))
    W(li("Swiftness Aura now also provides +2.5 Health Regen", t("NEW")))
    W(li("Recipe cost increased from 500 to 525 " + b(500, 525, l=True) + ". Total cost unchanged at 1625g", t("MISC")))
    W(ul_close())
    W(item_header("Boots of Bearing"))
    W(ul_open())
    W(li("Endurance now shares cooldown with Drum of Endurance", t("NERF")))
    W(li("No longer provides +8 Intelligence", t("DEL")))
    W(li("Swiftness Aura now also provides +2.5 Health Regen", t("NEW")))
    W(ul_close())
    W(item_header("Eternal Shroud"))
    W(ul_open())
    W(li("Item removed from the game", t("DEL")))
    W(ul_close())
    W(item_header("Ethereal Blade"))
    W(ul_open())
    W(li("Can no longer be disassembled", t("DEL")))
    W(ul_close())
    W(item_header("Gleipnir", changed=True))
    W(auto_components_change("Gleipnir", "7.41"))
    W(ul_open())
    W(li("Recipe cost decreased from 1100 to 400 " + b(1100, 400, l=True) + ". Total cost increased from 4550g to 4650g", b(4550, 4650, l=True)))
    W(li("Area of Effect bonuses from multiple Chasm Stones or its upgrades do not stack", t("MISC")))
    W(ul_close())
    W(item_header("Glimmer Cape", changed=True))
    W(auto_components_change("Glimmer Cape", "7.41"))
    W(ul_open())
    W(li("Recipe cost increased from 450 to 800 " + b(450, 800, l=True) + ". Total cost unchanged at 2150g", t("MISC")))
    W(ul_close())
    W(item_header("Hand of Midas"))
    W(ul_open())
    W(li("Transmute no longer prevents camp-clearing Madstone Bundles from spawning if it was used on the last creep in neutral camp", t("MISC")))
    W(li("Getting guaranteed Madstone Bundle from Transmute used to prevent the camp-clearing bundle from spawning", t("MISC")))
    W(ul_close())
    W(item_header("Harpoon"))
    W(ul_open())
    W(li("Draw Forth can now target trees and will pull the caster to it, destroying all trees on the way", t("NEW")))
    W(ul_close())
    W(item_header("Heaven's Halberd", changed=True))
    W(auto_components_change("Heaven's Halberd", "7.41"))
    W(properties_change(
        old=[("DEL",  "+275 Health"),
             ("DEL",  "Damage Block (passive)"),
             ("BUFF", "+6 Health Regen")],
        new=[("NEW",  "+9 Armor"),
             ("NEW",  "+25% Evasion"),
             ("",     "+6.5 Health Regen", b(6, 6.5))]))
    W(ul_open())
    W(li("Disarm cooldown decreased from 20s to 16s", b(20, 16, l=True)))
    W(li("Disarm cast range increased from 650 to 750", b(650, 750)))
    W(li("Disarm duration increased from 3s to 3.5s", b(3, 3.5)))
    W(li("Can no longer be disassembled", t("DEL")))
    W(ul_close())
    W(item_header("Kaya"))
    W(ul_open())
    W(li("Mana Regen Amplification bonus decreased from +40% to +30%", b(40, 30)))
    W(ul_close())
    W(item_header("Kaya and Sange"))
    W(ul_open())
    W(li("Mana Regen Amplification bonus decreased from +50% to +40%", b(50, 40)))
    W(li("Now also modifies incoming healing", t("NEW"),
         extra=inline_note("As a result of Health Restoration changes")))
    W(ul_close())
    W(item_header("Meteor Hammer"))
    W(ul_open())
    W(li("Mana Regen Amplification bonus decreased from +40% to +35%", b(40, 35)))
    W(ul_close())
    W(item_header("Yasha and Kaya"))
    W(ul_open())
    W(li("Mana Regen Amplification bonus decreased from +50% to +40%", b(50, 40)))
    W(ul_close())
    W(item_header("Lotus Orb"))
    W(ul_open())
    W(li("Can no longer be disassembled", t("DEL")))
    W(ul_close())
    W(item_header("Mage Slayer", changed=True))
    W(auto_components_change("Mage Slayer", "7.41"))
    W(properties_change(
        old=[("BUFF", "+5 Health Regen"),
             ("BUFF", "+2 Mana Regen"),
             ("BUFF", "+8 Damage"),
             ("DEL",  "+30 Attack Speed")],
        new=[("",     "+6 Health Regen",  b(5, 6)),
             ("",     "+2.5 Mana Regen",  b(2, 2.5)),
             ("",     "+15 Damage",       b(8, 15))]))
    W(ul_open())
    W(li("Mage Slayer damage per second increased from 20 to 40", b(20, 40)))
    W(li("Total cost increased from 2800g to 3100g (change is bigger due to Cloak cost increase)", b(2800, 3100, l=True)))
    W(li("Mage Slayer damage type changed from magical to physical", t("REWORK")))
    W(ul_close())
    W(item_header("Mask of Madness"))
    W(ul_open())
    W(li("Berserk armor reduction decreased from 8 to 7", b(8, 7, l=True)))
    W(li("Berserk now also grants 30% Slow Resistance for the duration", t("NEW")))
    W(li("Berserk bonus Movement Speed changed from +25 for all heroes to +8%/12% for Ranged/Melee", t("REWORK")))
    W(ul_close())
    W(item_header("Mekansm"))
    W(ul_open())
    W(li("Recipe cost increased from 800 to 850", t("MISC") + b(800, 850, l=True), extra=inline_note("Total cost unchanged at 1775g (due to Chainmail cost decrease)")))
    W(ul_close())
    W(item_header("Monkey King Bar"))
    W(ul_open())
    W(li("Damage bonus increased from +40 to +50", b(40, 50)))
    W(li("Attack Speed bonus increased from +45 to +50", b(45, 50)))
    W(li("Recipe cost increased from 600 to 900 " + b(600, 900, l=True) + ". Total cost increased from 4700g to 5000g", b(4700, 5000, l=True)))
    W(li("Now also provides +50 Attack Range to melee heroes only", t("NEW")))
    W(ul_close())
    W(item_header("Nullifier", changed=True))
    W(auto_components_change("Nullifier", "7.41"))
    W(ul_open())
    W(li("No longer provides +6 Health Regen", t("DEL")))
    W(li("Total cost decreased from 4375g to 4350g", b(4375, 4350, l=True)))
    W(ul_close())
    W(item_header("Oblivion Staff"))
    W(ul_open())
    W(li("Mana Regen bonus increased from +1 to +1.25", b(1, 1.25)))
    W(ul_close())
    W(item_header("Orchid Malevolence", changed=True))
    W(auto_components_change("Orchid Malevolence", "7.41"))
    W(properties_change(
        old=[("BUFF", "+10 Damage"),
             ("NERF", "+3 Mana Regen"),
             ("BUFF", "+10 Intelligence"),
             ("DEL",  "+6 Health Regen")],
        new=[("",     "+20 Damage",       b(10, 20)),
             ("",     "+2.5 Mana Regen",  b(3, 2.5)),
             ("",     "+12 Intelligence", b(10, 12))]))
    W(ul_open())
    W(li("Recipe cost decreased from 450 to 300 " + b(450, 300, l=True) + ". Total cost unchanged at 3275g", t("MISC")))
    W(ul_close())
    W(item_header("Bloodthorn", changed=True))
    W(auto_components_change("Bloodthorn", "7.41"))
    W(properties_change(
        old=[("BUFF", "+10 Intelligence"),
             ("NERF", "+95 Attack Speed"),
             ("BUFF", "+3.25 Mana Regen"),
             ("BUFF", "+10 Damage"),
             ("DEL",  "+6.5 Health Regen")],
        new=[("",     "+25 Intelligence", b(10, 25)),
             ("",     "+70 Attack Speed", b(95, 70)),
             ("",     "+4 Mana Regen",    b(3.25, 4)),
             ("",     "+20 Damage",       b(10, 20))]))
    W(ul_open())
    W(li("Recipe cost increased from 450 to 600 " + b(450, 600, l=True) + ". Total cost decreased from 6625g to 6400g", b(6625, 6400, l=True)))
    W(li("Soul Rend Mana Cost increased from 125 to 150", b(125, 150, l=True)))
    W(ul_close())
    W(item_header("Orb of Corrosion"))
    W(ul_open())
    W(li("Now also modifies incoming healing", t("NEW"),
         extra=inline_note("As a result of Health Restoration changes")))
    W(ul_close())
    W(item_header("Eye of Skadi"))
    W(ul_open())
    W(li("Cold Attack no longer has a separate value for incoming heal reduction", t("MISC"),
         extra=inline_note("Still reduces incoming heals due to Health Restoration changes")))
    W(li("Cold Attack health restoration reduction increased from 40% to 50%", b(40, 50)))
    W(ul_close())
    W(item_header("Pavise", changed=True))
    W(auto_components_change("Pavise", "7.41"))
    W(properties_change(
        old=[("NERF", "+250 Mana")],
        new=[("",     "+175 Mana", b(250, 175))]))
    W(ul_open())
    W(li("Recipe cost increased from 175 to 675 " + b(175, 675, l=True) + ". Total cost decreased from 1400g to 1350g", b(1400, 1350, l=True)))
    W(ul_close())
    W(item_header("Solar Crest", changed=True))
    W(auto_components_change("Solar Crest", "7.41"))
    W(properties_change(
        old=[("BUFF", "+4 Armor"),
             ("NERF", "+300 Mana"),
             ("BUFF", "+175 Health"),
             ("DEL",  "+4 All Attributes")],
        new=[("",     "+7 Armor",    b(4, 7)),
             ("",     "+200 Mana",   b(300, 200)),
             ("",     "+200 Health", b(175, 200))]))
    W(ul_open())
    W(li("Recipe cost unchanged at 500. Total cost unchanged at 2575g (due to Pavise cost decrease)", t("MISC")))
    W(ul_close())
    W(item_header("Perseverance"))
    W(ul_open())
    W(li("Health Regen bonus decreased from +6.5 to +5.5", b(6.5, 5.5)))
    W(ul_close())
    W(item_header("Phase Boots"))
    W(ul_open())
    W(li("Cost decreased from 1500g to 1450g (due to Chainmail cost decrease)", b(1500, 1450, l=True)))
    W(ul_close())
    W(item_header("Phylactery"))
    W(ul_open())
    W(li("Health Regen bonus decreased from +6.5 to +5.5", b(6.5, 5.5)))
    W(ul_close())
    W(item_header("Pipe of Insight", changed=True))
    W(auto_components_change("Pipe of Insight", "7.41"))
    W(ul_open())
    W(li("Recipe Cost decreased from 800 to 675", t("MISC") + b(800, 675, l=True), extra=inline_note("Total cost unchanged at 3725g (due to Cloak cost increase)")))
    W(li("Barrier no longer affects units that have been affected by Barrier within Pipe of Insight's cooldown", t("NERF")))
    W(li("Insight Aura no longer provides 2.5 health regen", t("DEL")))
    W(ul_close())
    W(item_header("Radiance"))
    W(ul_open())
    W(li("Burn toggling no longer breaks invisibility nor stops channels", t("MISC")))
    W(ul_close())
    W(item_header("Refresher Orb"))
    W(ul_open())
    W(li("Health Regen bonus increased from +12 to +14", b(12, 14)))
    W(li("Mana Regen bonus increased from +6 to +7", b(6, 7)))
    W(li("Reset Cooldowns cooldown decreased from 180/190/200/210s to 180s", b([180, 190, 200, 210], 180, l=True),
         extra=inline_note("No longer scales with uses")))
    W(li("Reset Cooldowns mana cost decreased from 400 to 325", b(400, 325, l=True)))
    W(li("Reset Cooldowns no longer refreshes items", t("DEL")))
    W(ul_close())
    W(item_header("Revenant's Brooch"))
    W(ul_open())
    W(li("Spell Lifesteal bonus increased from +14% to +15%", b(14, 15)))
    W(ul_close())
    W(item_header("Sange"))
    W(ul_open())
    W(li("Slow Resistance bonus increased from +20% to +25%", b(20, 25)))
    W(li("Now also modifies incoming healing", t("NEW"),
         extra=inline_note("As a result of Health Restoration changes")))
    W(ul_close())
    W(item_header("Abyssal Blade"))
    W(ul_open())
    W(li("Slow Resistance bonus increased from +25% to +30%", b(25, 30)))
    W(li("Now also modifies incoming healing", t("NEW"),
         extra=inline_note("As a result of Health Restoration changes")))
    W(ul_close())
    W(item_header("Sange and Yasha"))
    W(ul_open())
    W(li("Status Resistance bonus increased from +15% to +16%", b(15, 16)))
    W(li("Slow Resistance bonus increased from +25% to +30%", b(25, 30)))
    W(li("Now also modifies incoming healing", t("NEW"),
         extra=inline_note("As a result of Health Restoration changes")))
    W(ul_close())
    W(item_header("Shiva's Guard", changed=True))
    W(auto_components_change("Shiva's Guard", "7.41"))
    W(properties_change(
        old=[("BUFF", "+15 Armor"),
             ("DEL",  "+5 Strength"),
             ("DEL",  "+5 Agility"),
             ("DEL",  "+5 Intelligence"),
             ("DEL",  "+5 Health Regen")],
        new=[("",    "+17 Armor", b(15, 17)),
             ("NEW", "+75 Area of Effect")]))
    W(ul_open())
    W(li("Recipe cost decreased from 2050 to 1350 " + b(2050, 1350, l=True) + ". Total cost decreased from 5175g to 4500g", b(5175, 4500, l=True)))
    W(li("Arctic Blast damage increased from 200 to 260", b(200, 260)))
    W(li("Freezing Aura now pierces debuff immunity", t("NEW")))
    W(li("Arctic Blast no longer increases damage taken from spells", t("DEL")))
    W(li("Freezing Aura no longer reduces Health Restoration and Incoming Heal Amplification by 25%", t("DEL")))
    W(li("Area of Effect bonuses from multiple Chasm Stones or its upgrades do not stack", t("MISC")))
    W(li("Arctic Blast radius decreased from 900 to 825", t("MISC"),
         extra=inline_note("Effective spell radius unchanged due to item's built-in Area of Effect bonus")))
    W(ul_close())
    W(item_header("Spirit Vessel"))
    W(ul_open())
    W(li("Soul Release no longer has a separate value for incoming heal reduction", t("MISC"),
         extra=inline_note("Still reduces incoming heals due to Health Restoration changes")))
    W(ul_close())
    W(item_header("Tranquil Boots"))
    W(ul_open())
    W(li("Break now also goes on cooldown when the item is disassembled. Reassembling the item will remember the time remaining", t("REWORK")))
    W(ul_close())
    W(item_header("Veil of Discord", changed=True))
    W(auto_components_change("Veil of Discord", "7.41"))
    W(properties_change(
        old=[("DEL", "+4 Armor"),
             ("DEL", "+4 All Attributes"),
             ("DEL", "+4.5 Health Regen")],
        new=[("NEW", "+10 Intelligence"),
             ("NEW", "+175 Health"),
             ("NEW", "+18% Spell Lifesteal")]))
    W(ul_open())
    W(li("Magic Weakness renamed to Spell Weakness", t("MISC")))
    W(ul_close())
    W(item_header("Bloodstone", changed=True))
    W(auto_components_change("Bloodstone", "7.41"))
    W(properties_change(
        old=[("NERF", "+25% Spell Lifesteal"),
             ("BUFF", "+450 Health"),
             ("DEL",  "+3 Mana Regen")],
        new=[("",    "+20% Spell Lifesteal", b(25, 20)),
             ("",    "+650 Health",          b(450, 650)),
             ("NEW", "+15 Intelligence")]))
    W(ul_open())
    W(li("Bloodpact no longer has a 30s self debuff preventing repeated usage of Bloodpact", t("BUFF")))
    W(li("Total cost increased from 4350g to 4700g", b(4350, 4700, l=True)))
    W(li("Bloodpact no longer multiplies spell lifesteal bonus by 3. Now increases spell lifesteal to 60% instead", b(75, 60),
         extra=inline_note("Spell Lifesteal during Bloodpact decreased from 75% to 60%")))
    W(li("Bloodpact no longer applies a basic dispel", t("DEL")))
    W(li("Now also provides passive Spell Weakness Aura", t("NEW")))
    W(li("Passive: Enemy units within 1200 radius take 12% increased damage from spells", "",
         extra=inline_note("Effect does not stack with Veil of Discord's Spell Weakness")))
    W(ul_close())
    W(item_header("Witch Blade"))
    W(ul_open())
    W(li("Recipe cost increased from 250 to 300", t("MISC") + b(250, 300, l=True), extra=inline_note("Total cost unchanged at 2775g (due to Chainmail cost decrease)")))
    W(ul_close())
    # ===== NEUTRAL ITEM UPDATES =====
    W(section("Neutral Item Updates"))
    W(plain_header("General changes", dynamics=False, sublabel=True))
    W(ul_open())
    W(li("Tier 1 availability changed from 5:00 to 0:00", t("REWORK")))
    W(li("Madstone crafting cost for Tier 1 items increased from 5 to 6", t("REWORK")))
    W(ul_close())
    W(plain_header("Artifact changes", dynamics=False, sublabel=True))
    W(ul_open())
    W(li("Number of artifact choices increased from 4 to 5 for Tiers 2-5", t("REWORK")))
    W(ul_close())
    W(item_header("Ash Legion Shield"))
    W(ul_open())
    W(li("Shield Wall damage barrier increased from 140 to 160", b(140, 160)))
    W(li("Shield Wall movement speed reduction increased from 12 to 20", b(12, 20, l=True)))
    W(ul_close())
    W(item_header("Chipped Vest"))
    W(ul_open())
    W(li("Chipper damage returned to attacking creeps decreased from 20 to 15", b(20, 15)))
    W(ul_close())
    W(item_header("Dagger of Ristul", new="Returning Tier 1 Artifact"))
    W(ul_open())
    W(li("Active: Imbrue. Increase attack damage by 25 for 8s. Health Cost: 100. Cooldown: 30s", t("NEW")))
    W(ul_close())
    W(item_header("Forager's Kit", new="New Tier 1 Artifact"))
    W(ul_open())
    # First li opens the ability-row box; subsequent lis without ability_row=True
    # are treated as continuations by the box-wrapper state machine, so all 8
    # rows land inside ONE shared bordered box.
    W(li("When this item is off cooldown, the wearer can see trees that can be foraged. Standing next to one of those trees for 1s will give the wearer one of the following items. Cooldown: 60s. Tree reveal radius: 1200", t("NEW"), ability_row=True))
    W(li("All items except for bag of gold are placed in inventory (if there are slots available) and can stack up to 5 times per slot.", t("NEW")))
    W(li("&nbsp;", t("NEW")))
    W(li("Possible items:", t("NEW")))
    W(li("Ironwood Nut: Passively provides +3 Movement Speed. Grants +1 Primary Stat when consumed (+.4 all stats for universal heroes)", t("NEW")))
    W(li("Tomo'kan Ringcap: Passively Provides +2 Intelligence. Can be consumed to instantly grant a target 50 + 5% of their maximum mana", t("NEW")))
    W(li("Vital Toadstool: Passively Provides +2 Damage. Can be consumed to grant a target +1% Max Health Regeneration for 10s. If the unit is attacked by an enemy hero or Roshan the bonus is lost", t("NEW")))
    W(li("Bag of Gold: Provides 30 gold to the wearer. Don't need to be picked up", t("NEW")))
    W(ul_close())
    W(item_header("Possessed Mask", new="Returning Tier 1 Artifact"))
    W(ul_open())
    W(li("Passive: Lifesteal. Attacks heal for 5 health", t("NEW"),
         extra=inline_note("This counts as lifesteal and is manipulated by Health Restoration")))
    W(ul_close())
    W(item_header("Stonefeather Satchel", new="New Tier 1 Artifact"))
    W(ul_open())
    W(li("Toggle: Transmogrify. Activate to switch the contents of the satchel between Feathers or Rocks. No Mana Cost. Cooldown: 6s.", t("NEW")))
    W(li("Pound of Feathers: Increases movement speed by 12 and distance of forced movement effects on yourself by 30%", t("NEW")))
    W(li("Pound of Rocks: Increases armor by 3 and decreases distance of forced movement effects by 30%", t("NEW")))
    W(ul_close())
    W(item_header("Weighted Dice"))
    W(ul_open())
    W(li("Loaded now also increases max base damage by 6", t("NEW")))
    W(ul_close())
    W(item_header("Crippling Crossbow"))
    W(ul_open())
    W(li("Hobble initial damage decreased from 75 to 25", b(75, 25)))
    W(li("Hobble Max slow decreased from 80% to 50%", b(80, 50)))
    W(li("Hobble Cast Range decreased from 800 to 650", b(800, 650)))
    W(li("Hobble now also modifies incoming healing", t("NEW"),
         extra=inline_note("As a result of Health Restoration changes")))
    W(li("Moved from Tier 4 to Tier 2", t("REWORK")))
    W(ul_close())
    W(item_header("Medallion of Courage", new="Returning Tier 2 Artifact"))
    W(ul_open())
    W(li("Active: Valor. If cast on an ally, increases their armor by 7 for 8s. If cast on an enemy, decreases their armor by 4 for 8s. Cannot be cast on self. Cast Range: 1000. Mana Cost: 30. Cooldown: 18s", t("NEW"),
         extra=inline_note("Dormant Curio increases duration from 8s to 10.4s")))
    W(ul_close())
    W(item_header("Searing Signet"))
    W(ul_open())
    W(li("Burn Through: Total Damage decreased from 90 to 80", b(90, 80)))
    W(ul_close())
    W(subnote("From 117 to 104 with Dormant Curio"))
    W(ul_open())
    W(li("Burn Through: Damage Threshold increased from 55 to 60", b(55, 60, l=True)))
    W(ul_close())
    W(item_header("Seeds of Serenity", new="Returning Tier 2 Artifact"))
    W(ul_open())
    W(li("Active: Verdurous Dale. Place a 400 unit circle on the ground for 8s that increases health regeneration of allies inside by 8 + 25% of the caster's health regeneration. Cast Range: 350. No Mana Cost. Cooldown: 35s", t("NEW"),
         extra=inline_note("Dormant Curio increases health regeneration from 8 to 10.4 and from 25% to 32.5%")))
    W(ul_close())
    W(item_header("Whisper of the Dread"))
    W(ul_open())
    W(li("Item cycled out", t("DEL")))
    W(ul_close())
    W(item_header("Cloak of Flames", new="Returning Tier 3 Artifact"))
    W(ul_open())
    W(li("Passive: Immolate. Burns enemy units in a 375 unit radius for 40 damage per second. Illusions deal 25 damage per second", t("NEW"),
         extra=inline_note("Dormant Curio increases damage from 40 to 52 and illusion damage from 25 to 32.5")))
    W(ul_close())
    W(item_header("Gunpowder Gauntlet"))
    W(ul_open())
    W(li("Beat the Crowd cooldown increased from 6s to 10s", b(6, 10, l=True)))
    W(ul_close())
    W(item_header("Jidi Pollen Bag"))
    W(ul_open())
    W(li("Pollinate health restoration loss increased from 30% to 50%", b(30, 50)))
    W(li("Pollinate now also modifies incoming healing", t("NEW"),
         extra=inline_note("As a result of Health Restoration changes")))
    W(ul_close())
    W(item_header("Partisan's Brand", new="New Tier 3 Artifact"))
    W(ul_open())
    W(li("Passive: Brand. Increases spell damage against player controlled units by 9%", t("NEW"),
         extra=inline_note("Dormant Curio increases bonus spell damage from 9% to 11.7%")))
    W(li("Player controlled units includes heroes and any creep summoned or converted by them", t("NEW")))
    W(ul_close())
    W(item_header("Serrated Shiv"))
    W(ul_open())
    W(li("Gut 'Em cooldown increased from 1s to 1.5s", b(1, 1.5, l=True)))
    W(ul_close())
    W(item_header("Spellslinger", new="New Tier 3 Artifact"))
    W(ul_open())
    W(li("Passive: Salvo. Whenever you cast a spell, 20% of the spell's mana cost is restored over 10s. Tick rate: 2s", t("NEW"),
         extra=inline_note("Dormant Curio increases mana restored from 20% to 26%")))
    W(li("Mana recovery duration cannot be modified", t("NERF")))
    W(ul_close())
    W(item_header("Stormcrafter", new="Returning Tier 3 Artifact"))
    W(ul_open())
    W(li("Passive: Bottled Lightning. Every 6s, zaps up to 2 enemies within 700 units, slowing them by 40% for 0.4s and dealing 70 magic damage", t("NEW"),
         extra=inline_note("Dormant Curio increases damage from 70 to 91")))
    W(ul_close())
    W(item_header("Conjurer's Catalyst", new="New Tier 3 Artifact"))
    W(ul_open())
    W(li("Passive: Spellover. Every 100 spell damage dealt to an enemy deals damage to their surrounding allies in a 300 unit radius. Hero targets deal 40 damage to their allies, other targets deal 15 damage", t("NEW"),
         extra=inline_note("Dormant Curio increases hero damage from 40 to 52 and non-hero damage from 15 to 19.5")))
    W(ul_close())
    W(item_header("Dandelion Amulet", new="Returning Tier 4 Artifact"))
    W(ul_open())
    W(li("Passive: Magical Damage Block. Blocks 300 magic damage from instances over 75 damage. Cooldown: 12s", t("NEW"),
         extra=inline_note("Dormant Curio increases blocked damage from 300 to 390")))
    W(ul_close())
    W(item_header("Enchanter's Bauble", new="New Tier 4 Artifact"))
    W(ul_open())
    W(li("Passive: Enchant. Increases bonuses of the item's Neutral Enchantment by 15%. Every time you craft this item again the bonus is increased by 40%", t("NEW"),
         extra=inline_note("Dormant Curio increases recraft stat bonus from 40% to 52%")))
    W(li("You can select any Enchantments during re-craft and bonus will still keep increasing as long as you keep Enchanter's Bauble", t("NEW")))
    W(ul_close())
    W(item_header("Metamorphic Mandible"))
    W(ul_open())
    W(li("Pupate duration increased from 4s to 5s", b(4, 5)))
    W(ul_close())
    W(subnote("From 5.2s to 6.5s with Dormant Curio"))
    W(ul_open())
    W(li("Pupate bonus magic resistance increased from 35% to 50%", b(35, 50)))
    W(ul_close())
    W(item_header("Prophet's Pendulum", new="New Tier 4 Artifact"))
    W(ul_open())
    W(li("Passive: Linger. 30% of damage taken is delayed over 5 seconds. Damage Ticks every 1 second and is lethal", t("NEW"),
         extra=inline_note("Dormant Curio increases damage delayed from 30% to 39%")))
    W(ul_close())
    W(item_header("Rattlecage"))
    W(ul_open())
    W(li("Reverberate damage threshold increased from 180 to 220", b(180, 220)))
    W(ul_close())
    W(item_header("Harmonizer", new="New Tier 5 Artifact"))
    W(ul_open())
    W(li("Passive: Balance. Grants 5% mana cost reduction for every hero ability off cooldown and 6% spell amplification for every spell on cooldown", t("NEW"),
         extra=inline_note("Dormant Curio increases mana cost reduction from 5% to 6.5% and spell amplification from 6% to 7.8%")))
    W(li("Item spells are affected by both effects, however item cooldowns don't affect the Harmonizer buff", t("NEW")))
    W(li("The buff counts only current abilities that have cooldown, even if it's passive", t("NEW")))
    W(li("Invoked abilities and sub-abilities don't count when they're hidden", t("NEW")))
    W(ul_close())
    W(item_header("Riftshadow Prism"))
    W(ul_open())
    W(li("Refract health cost decreased from 10% to 8%", b(10, 8, l=True)))
    W(li("Refract incoming damage decreased from 240% to 200%", b(240, 200, l=True)))
    W(ul_close())
    W(item_header("Spider Legs"))
    W(ul_open())
    W(li("Skitter: Duration increased from 10s to 14s", b(10, 14)))
    W(ul_close())
    W(item_header("Witchbane", new="Returning Tier 5 Artifact"))
    W(ul_open())
    W(li("Active: Cleanse. Apply basic dispel on all units in a 300 unit radius area. Cast Range: 500. Mana Cost: 150. Cooldown: 40s", t("NEW")))
    W(li("Passive: Subjugate. Your attacks deal bonus magical damage equal to 4% of target's Max Mana", t("NEW"),
         extra=inline_note("Dormant Curio increases damage from 4% to 5.2%")))
    W(ul_close())
    W(plain_header("Enchantment Changes", dynamics=False, sublabel=True))
    W(ul_open())
    W(li("Number of Enchantment choices increased from 4 to 5 for Tiers 2-5", b(4, 5)))
    W(li("Enchantments are no longer randomized. Now options are based on your hero's primary attribute, with some enchantments available to all heroes", t("REWORK")))
    W(ul_close())

    W(subgroup("Tier 1"))
    W(enchant_tier_box([
        ("all", ["Quickened", "Vital"]),
        ("str", ["Brawny", "Tough"]),
        ("agi", ["Alert", "Brawny"]),
        ("int", ["Mystical", "Tough"]),
        ("uni", ["Alert", "Mystical"]),
    ], tiers=1))

    W(subgroup("Tiers 2-3"))
    W(enchant_tier_box([
        ("all", ["Quickened", "Greedy"]),
        ("str", ["Brawny", "Tough", "Crude"]),
        ("agi", ["Alert", "Brawny", "Nimble"]),
        ("int", ["Mystical", "Tough", "Keen-Eyed"]),
        ("uni", ["Alert", "Mystical", "Titanic"]),
    ], tiers=[2, 3]))

    W(subgroup("Tier 4"))
    W(enchant_tier_box([
        ("all", ["Quickened", "Timeless"]),
        ("str", ["Brawny", "Tough", "Crude"]),
        ("agi", ["Alert", "Brawny", "Nimble"]),
        ("int", ["Mystical", "Tough", "Keen-Eyed"]),
        ("uni", ["Alert", "Mystical", "Titanic"]),
    ], tiers=4))

    W(subgroup("Tier 5"))
    W(enchant_tier_box([
        ("all", ["Evolved", "Fleetfooted", "Timeless", "Vampiric"]),
        ("str", ["Hulking"]),
        ("agi", ["Audacious"]),
        ("int", ["Feverish"]),
        ("uni", ["Manic"]),
    ], tiers=5))
    W(enchant_header("Boundless"))
    W(ul_open())
    W(li("Removed", t("DEL")))
    W(ul_close())
    W(enchant_header("Vast"))
    W(ul_open())
    W(li("Removed", t("DEL")))
    W(ul_close())
    W(enchant_header("Wise"))
    W(ul_open())
    W(li("Removed", t("DEL")))
    W(ul_close())
    W(enchant_header("Quickened"))
    W(ul_open())
    W(li("Now is a guaranteed Tiers 1-4 option for all heroes", t("REWORK")))
    W(ul_close())
    W(enchant_header("Vital", new="New Tier 1 Enchantment"))
    W(ul_open())
    W(li("+2 Health Regen", t("NEW")))
    W(ul_close())
    W(enchant_header("Brawny"))
    W(ul_open())
    W(li("Now is a guaranteed Tiers 1-4 option for Strength and Agility heroes", t("REWORK")))
    W(ul_close())
    W(enchant_header("Tough"))
    W(ul_open())
    W(li("Now is a guaranteed Tiers 1-4 option for Strength and Intelligence heroes", t("REWORK")))
    W(ul_close())
    W(enchant_header("Alert"))
    W(ul_open())
    W(li("Now is a guaranteed Tiers 1-4 option for Agility and Universal heroes", t("REWORK")))
    W(li("Attack Speed bonus decreased from +10/17/24/31 to +7/15/23/31", b([10, 17, 24, 31], [7, 15, 23, 31])))
    W(ul_close())
    W(enchant_header("Mystical"))
    W(ul_open())
    W(li("Now is a guaranteed Tiers 1-4 option for Intelligence and Universal heroes", t("REWORK")))
    W(li("No longer provides +100 Cast Range bonus at Tier 4", t("DEL")))
    W(li("Now provides +15% Mana Cost/Mana Loss Reduction at Tier 4", t("NEW")))
    W(ul_close())
    W(enchant_header("Greedy", "greedy"))
    W(ul_open())
    W(li("Now is a guaranteed option for all heroes on Tiers 2-3", t("REWORK")))
    W(ul_close())
    W(enchant_header("Crude", "crude"))
    W(ul_open())
    W(li("Health Restoration bonus rescaled from +30/40% to +10/15/20%", b([30, 40], [10, 15, 20])))
    W(li("Base Attack Time Reduction bonus rescaled from 12/18% to 8/12/16%", b([12, 18], [8, 12, 16])))
    W(li("Intelligence Penalty increased from 5% to 6%", b(5, 6, l=True)))
    W(li("Now also modifies incoming healing", t("NEW"),
         extra=inline_note("As a result of Health Restoration changes")))
    W(li("Now is a guaranteed option for Strength heroes only", t("REWORK")))
    W(li("Tiers changed from 4/5 to 2-4", t("REWORK")))
    W(ul_close())
    W(enchant_header("Nimble", new="New Tiers 2-4 Enchantment"))
    W(ul_open())
    W(li("+6/8/10% Movement Speed", t("NEW")))
    W(li("+10/15/20 Damage", t("NEW")))
    W(li("-1.5/2.25/3 <font color='#e03e2e'>Health Regen</font>", t("NEW")))
    W(ul_close())
    W(enchant_header("Keen-Eyed"))
    W(ul_open())
    W(li("Max Mana Penalty increased from 10% to 10/12/14%", b(10, [10, 12, 14], l=True)))
    W(li("Cast Range bonus rescaled from +125/135 to +125/135/145", t("NEW")))
    W(li("Mana Regen bonus rescaled from 1/1.5 to 1/1.5/2", t("NEW")))
    W(li("Now is a guaranteed option for Intelligence heroes only", t("REWORK")))
    W(li("Tiers changed from 2/3 to 2-4", t("REWORK")))
    W(ul_close())
    W(enchant_header("Titanic"))
    W(ul_open())
    W(li("Attack Damage bonus rescaled from +10/20% to +8/12/16%", b([10, 20], [8, 12, 16])))
    W(li("Status Resistance rescaled from 10/15% to +10/12/14%", b([10, 15], [10, 12, 14])))
    W(li("Now also provides -10/12/14% <font color='#e03e2e'>Attack Speed</font>", t("NEW")))
    W(li("Now is a guaranteed option for Universal heroes only", t("REWORK")))
    W(li("Tiers changed from 4/5 to 2-4", t("REWORK")))
    W(ul_close())
    W(enchant_header("Timeless"))
    W(ul_open())
    W(li("Now is a guaranteed Tiers 4-5 option for all heroes", t("REWORK")))
    W(ul_close())
    W(enchant_header("Evolved"))
    W(ul_open())
    W(li("Now is a guaranteed Tier 5 option for all heroes", t("REWORK")))
    W(ul_close())
    W(enchant_header("Fleetfooted"))
    W(ul_open())
    W(li("Now is a guaranteed Tier 5 option for all heroes", t("REWORK")))
    W(ul_close())
    W(enchant_header("Vampiric"))
    W(ul_open())
    W(li("Now is a guaranteed option for all heroes", t("REWORK")))
    W(li("Tiers changed from 2-4 to 5", t("REWORK")))
    W(li("Lifesteal bonus increased from +12/14/16% to +30%", b([12, 14, 16], 30)))
    W(li("Spell Lifesteal increased from +6/8/10% to +20%", b([6, 8, 10], 20)))
    W(li("Bonus Night Vision increased from +0/0/200 to +300", b([0, 0, 200], 300)))
    W(ul_close())
    W(enchant_header("Hulking", new="New Tier 5 Enchantment"))
    W(ul_open())
    W(li("+5% Max Health", t("NEW")))
    W(li("+1.5% Max Health Regen", t("NEW")))
    W(li("-30% <font color='#e03e2e'>Attack Speed</font>", t("NEW")))
    W(ul_close())
    W(enchant_header("Audacious"))
    W(ul_open())
    W(li("Now is a guaranteed Tier 5 option for Agility heroes only", t("REWORK")))
    W(ul_close())
    W(enchant_header("Feverish"))
    W(ul_open())
    W(li("Now is a guaranteed Tier 5 option for Intelligence heroes only", t("REWORK")))
    W(ul_close())
    W(enchant_header("Manic", new="New Tier 5 Enchantment"))
    W(ul_open())
    W(li("-18% Base Attack Time", t("NEW")))
    W(li("+20% Cast Speed", t("NEW")))
    W(li("-20% <font color='#e03e2e'>Vision</font>", t("NEW")))
    W(ul_close())

    # ===== HERO UPDATES =====
    W(section("Hero Updates"))


    # Abaddon
    W(hero_header("Abaddon"))
    W(ability("Withering Mist"))
    W(ul_open())
    W(li_formula("Health Restoration Reduction changed",
                 "35%", "24.5% + 0.5% per level",
                 lambda L: 35.0, lambda L: 24.5 + 0.5 * L))
    W(li("Now also modifies incoming healing", t("NEW"),
         extra=inline_note("As a result of Health Restoration changes")))
    W(ul_close())
    W(ability("Mist Coil", slug="abaddon_death_coil"))
    W(ul_open())
    W(li("Damage/Heal increased from 95/160/225/290 to 95/170/245/320", b([95, 160, 225, 290], [95, 170, 245, 320])))
    W(ul_close())
    W(ability("Borrowed Time"))
    W(ul_open())
    W(li("Cooldown decreased from 90/85/80s to 85/75/65s", b([90, 85, 80], [85, 75, 65], l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +10% Withering Mist Health Restoration Reduction replaced with +25 Curse of Avernus DPS", t("REWORK")))
    W(li("Level 15 Talent +40 Curse of Avernus DPS replaced with -10s Borrowed Time Cooldown", t("REWORK")))
    W(ul_close())

    # Alchemist
    W(hero_header("Alchemist"))
    W(ability("Greevil's Greed", slug="alchemist_goblins_greed"))
    W(ul_open())
    W(li("Aghanim's Scepter now also increases Base Bonus Gold and Max Bonus Gold per kill by 6 per melted Aghanim's Scepter", t("NEW")))
    W(ul_close())
    W(ability("Corrosive Weaponry"))
    W(ul_open())
    W(li("Movement Slow per stack increased from 2/2.5/3/3.5% to 2.5/3/3.5/4%", b([2, 2.5, 3, 3.5], [2.5, 3, 3.5, 4])))
    W(li("Base Attack Damage Reduction per stack increased from 2/2.5/3/3.5% to 2.5/3/3.5/4%", b([2, 2.5, 3, 3.5], [2.5, 3, 3.5, 4])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Unstable Concoction Radius increased from +125 to +150", b(125, 150)))
    W(li("Level 15 Talent Damage per Greevil's Greed stack increased from +2.5 to +3", b(2.5, 3)))
    W(li("Level 15 Talent Acid Spray grants armor to allies replaced with +1% Corrosive Weaponry Slow/Damage Reduction Per Stack", t("REWORK")))
    W(ul_close())

    # Ancient Apparition
    W(hero_header("Ancient Apparition"))
    _bc_pill, _bc_table = scale_pill(
        "0.1 + 0.1 per 3 levels",
        lambda L: 0.1 + 0.1 * (L // 3),
        value_fmt="{:.2f}",
    )
    W(ability_change(
        old=dict(
            name="Death Rime",
            innate=True,
            desc=[
                "Passive.",
                "Ancient Apparition's abilities apply frost stacks that deal <b>10 damage per second</b> and <b>1.5% movement slow</b> for each stack on the enemy.",
            ],
        ),
        new=dict(
            name="Bone Chill",
            slug="ancient_apparition_bone_chill",
            innate=True,
            desc=[
                "Passive.",
                "When Ancient Apparition deals magic damage with his abilities, affected enemies are chilled for 4s, reducing their movement speed by 2% per stack. Each instance stacks and has independent duration.",
                "If the target is an enemy hero, the debuff also reduces their Strength by "
                + _bc_pill
                + ".",
                aghs_line("Increases Base Strength Reduction by 0.3."),
            ],
            tables=[_bc_table],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Cold Feet"))
    W(ul_open())
    W(li("Now deals 20/40/60/80 damage per second", t("NEW")))
    W(ul_close())
    W(ability("Ice Vortex"))
    W(ul_open())
    W(li("Now deals 10/20/30/40 damage per second", t("NEW")))
    W(li("Now slows movement by 8%", t("NEW")))
    W(ul_close())
    W(ability("Chilling Touch"))
    W(ul_open())
    W(li("Mana Cost decreased from 45/50/55/60 to 35", b([45, 50, 55, 60], 35, l=True)))
    W(li("Aghanim's Scepter no longer reduces mana cost", t("DEL")))
    W(ul_close())
    W(ability("Ice Blast"))
    W(ul_open())
    W(li("Now deals 12/24/36 damage per second", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +2 Cold Feet Death Rime Stacks replaced with +30 Cold Feet Damage Per Second", t("REWORK")))
    W(li("Level 15 Talent Cold Feet Break Distance decreased from +300 to +250", b(300, 250)))
    W(li("Level 25 Talent +50% Death Rime Slow/Damage replaced with 450 AoE Cold Feet", t("REWORK")))
    W(ul_close())

    # Anti-Mage
    W(hero_header("Anti-Mage"))
    W(ul_open())
    W(li("Base Armor increased by 1", bstat_h("Anti-Mage", "ArmorPhysical", "7.40c", 1), extra=note_box(hero="Anti-Mage", field="ArmorPhysical", before_patch="7.40c")))
    W(ul_close())
    W(ability("Persecutor", slug="antimage_persectur"))
    W(ul_open())
    W(li("No longer levels with Mana Void", t("REWORK")))
    W(li_formula("Min Movement Slow rescaled",
                 "12.5/15/17.5/20%", "12% + 0.5% per level",
                 lambda L: 20.0, lambda L: 12.0 + 0.5 * L))
    W(li_formula("Max Movement Slow rescaled",
                 "25/30/35/40%", "24% + 1% per level",
                 lambda L: 40.0, lambda L: 24.0 + 1.0 * L))
    W(ul_close())
    W(ability("Mana Break"))
    W(ul_open())
    W(li("Effectiveness when applied by illusions decreased from 50% to 25%", b(50, 25)))
    W(li("Aghanim's Scepter: Increases Max Mana Burned per hit by an additional 1.5%", t("NEW")))
    W(ul_close())
    W(ability("Blink"))
    W(ul_open())
    W(li("Cast Range rescaled from 750/900/1050/1200 to 875/950/1025/1100", b([750, 900, 1050, 1200], [875, 950, 1025, 1100])))
    W(li("Cooldown decreased from 12/10/8/6s to 10.5/9/7.5/6s", b([12, 10, 8, 6], [10.5, 9, 7.5, 6], l=True)))
    W(li("Mana Cost increased from 50 to 65/60/55/50", b(50, [65, 60, 55, 50], l=True)))
    W(li("Aghanim's Scepter no longer decreases cooldown by 1s", t("DEL")))
    W(ul_close())
    W(ability("Counterspell"))
    W(ul_open())
    W(li("Magic Resistance decreased from 16/24/32/40% to 14/21/28/35%", b([16, 24, 32, 40], [14, 21, 28, 35])))
    W(li("Duration increased from 1.2s to 1.3s", b(1.2, 1.3)))
    W(ul_close())
    W(ability("Mana Void"))
    W(ul_open())
    W(li("Cooldown increased from 70s to 100/85/70s", b(70, [100, 85, 70], l=True)))
    W(li("Radius decreased from 500 to 400/450/500", b(500, [400, 450, 500])))
    W(li("Damage per 1 Mana Missing rescaled from 0.8/0.95/1.1 to 1", b([0.8, 0.95, 1.1], 1)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +1% Max Mana Mana Burn replaced with +0.2 Mana Void Damage Multiplier", t("REWORK")))
    W(li("Level 20 Talent +0.2 Mana Void Damage Multiplier replaced with +150 Blink Cast Range", t("REWORK")))
    W(li("Level 25 Talent +200 Blink Cast Range replaced with -1s Blink Cooldown", t("REWORK")))
    W(ul_close())

    # Arc Warden
    W(hero_header("Arc Warden"))
    W(ul_open())
    W(li("Strength gain decreased from 2.4 to 2.2", b(2.4, 2.2)))
    W(li("Agility gain decreased from 3.0 to 2.7", b(3.0, 2.7)))
    W(li("Damage gain per level decreased from 3.6 to 3.4 as a result", b(3.6, 3.4)))
    W(li("Base Movement Speed increased from 285 to 300", b(285, 300)))
    W(ul_close())
    W(ability_change(
        old=dict(
            name="Runic Infusion",
            slug="arc_warden_runic_infusion",
            innate=True,
            desc=[
                "Passive.",
                "Upon activating any rune, Arc Warden gains the Regeneration Rune buff for 4s. Duration is reduced by 34% for activating Bounty or Water Runes.",
                "Activating a Wisdom Rune provides a full 4s buff. Activating a Regeneration Rune creates a stackable second effect.",
            ],
        ),
        new=dict(
            name="Runic Infusion",
            slug="arc_warden_runic_infusion",
            innate=True,
            desc=[
                "Passive.",
                "Whenever Arc Warden or the Tempest Double activates a Power Rune, Arc Warden permanently gains +1.5 all attributes.",
            ],
        ),
        summary="Innate reworked.",
        tag="rework",
    ))
    W(ability("Magnetic Field"))
    W(ul_open())
    W(li("The field now also pulls runes, and automatically activates ones that are inside. Rune Pull Force: 100. Rune Pull Radius: 800/1200/1600/2000", t("NEW")))
    W(ul_close())
    W(ability("Spark Wraith"))
    W(ul_open())
    W(li("Slow Duration increased from 0.5/0.6/0.7/0.8s to 0.7/0.8/0.9/1s", b([0.5, 0.6, 0.7, 0.8], [0.7, 0.8, 0.9, 1])))
    W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
    W(ul_close())
    W(ability("Tempest Double"))
    W(ul_open())
    W(li_formula("Gold and XP Bounty rescaled",
                 "180/240/300", "70 + 10 per level",
                 lambda L: 300.0, lambda L: 70.0 + 10.0 * L))
    W(li("Aghanim's Shard: The Tempest Double is infused with the bonuses of Arcane, Invisibility, and Haste Runes for 12s. These bonuses don't provide Runic Infusion stacks", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent +50% Spark Wraith Damage replaced with +200 Spark Wraith Damage", t("REWORK")))
    W(li("Level 25 Talent -1.1s Spark Wraith Activation Delay replaced with +30s Spark Wraith Duration", t("REWORK")))
    W(li("Level 25 Talent Tempest Double Has No Penalties replaced with +1.5 Runic Infusion All Attributes Bonus (applies retroactively)", t("REWORK")))
    W(ul_close())

    # Axe
    W(hero_header("Axe"))
    W(ability_change(
        old=dict(
            name="Coat of Blood",
            innate=True,
            desc=[
                "Passive.",
                "Whenever Axe kills an enemy, he gains <b>+1 permanent armor</b>. Kills with Culling Blade give <b>2×</b> that amount.",
            ],
        ),
        new=dict(
            name="One Man Army",        innate=True,
            desc=[
                "Passive.",
                "Increases Axe's Strength by 50% of his armor, as long as there are no allied heroes within a 700 unit radius of him.",
                "The effect fades over 3s after an ally walks within range. Bonus Strength can be broken.",
            ],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Culling Blade"))
    W(ul_open())
    W(li("Now each hero kill made with Culling Blade provides a permanent stack, which provides 1/1.5/2 armor depending on the current level of Culling Blade", t("NEW")))
    W(ul_close())

    # Bane
    W(hero_header("Bane"))
    W(ul_open())
    W(li("Strength gain decreased from 2.7 to 2.5", b(2.7, 2.5)))
    W(li("Agility gain decreased from 2.7 to 2.5", b(2.7, 2.5)))
    W(li("Intelligence gain decreased from 2.7 to 2.5", b(2.7, 2.5)))
    W(li("Damage gain per level decreased from 3.6 to 3.4 as a result", b(3.6, 3.4),
         extra=inline_note("Bane is Universal — all three attribute decreases contribute")))
    W(li("Attack Range increased from 400 to 425", b(400, 425)))
    W(ul_close())
    W(ability_change(
        old=dict(
            name="Ichor of Nyctasha",
            slug="bane_ichor_of_nyctasha",
            innate=True,
            desc=[
                "Passive.",
                "Bane's attribute gains are always evenly distributed across all three attributes.",
                "Example: Belt of Strength that provides +6 Strength will instead increase all three attributes by 2.",
            ],
        ),
        new=dict(
            name="Ichor of Nyctasha",
            slug="bane_ichor_of_nyctasha",
            innate=True,
            desc=[
                "Passive.",
                "Every time Bane kills an enemy hero or they die under the effect of any debuff applied by Bane, they receive a Terror for the rest of the game.",
                "Each Terror stack decreases the enemy's status resistance to all Bane's debuffs by 5%. Max Terror stacks per hero: 5.",
            ],
        ),
        summary="Innate reworked.",
        tag="rework",
    ))
    W(ability("Nightmare"))
    W(ul_open())
    W(li("Now a Unit Vector Target Spell", t("REWORK")))
    W(li("Sleeping units walk in Bane's chosen direction at a speed of 110", t("MISC"),
         extra=inline_note("Can be put on alt-cast to disable sleepwalking behavior")))
    W(ul_close())

    # Batrider
    W(hero_header("Batrider"))
    W(ability("Firefly"))
    W(ul_open())
    W(li("Now also provides an increasing movement speed bonus that reaches its maximum of 12/18/24/30% at the end of Firefly's duration", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +50 Flamebreak Knockback Distance replaced with +1s Smoldering Resin Duration", t("REWORK")))
    W(li("Level 10 Talent +50 Sticky Napalm Radius replaced with +5% Firefly Max Movement Speed Bonus", t("REWORK")))
    W(li("Level 15 Talent -8s Flaming Lasso Cooldown replaced with +0.5% Sticky Napalm Movement Slow", t("REWORK")))
    W(li("Level 15 Talent +20 Movement Speed replaced with +30 Firefly Damage Per Second", t("REWORK")))
    W(li("Level 20 Talent +4s Smoldering Resin Duration replaced with Attacks apply 1 Stack of Sticky Napalm", t("REWORK")))
    W(li("Level 25 Talent +10 Sticky Napalm Damage replaced with +0.75s Flaming Lasso Duration", t("REWORK")))
    W(ul_close())

    # Beastmaster
    W(hero_header("Beastmaster"))
    _ib_pill, _ib_table = scale_pill(
        "7 + 3 per level",
        lambda L: 7.0 + 3.0 * L,
    )
    W(ability_change(
        old=dict(
            name="Rugged",
            innate=True,
            desc=[
                "Passive.",
                "Beastmaster's chance to <b>block damage from non-hero unit attacks</b> is increased to <b>100%</b> (from the melee hero base of 50%).",
            ],
        ),
        new=dict(
            name="Inner Beast",
            slug="beastmaster_inner_beast",
            innate=True,
            desc=[
                "Passive.",
                "Provides bonus Attack Speed to Beastmaster and units under his control: " + _ib_pill + ".",
            ],
            tables=[_ib_table],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Wild Axes"))
    W(ul_open())
    W(li("Damage per axe increased from 30/65/100/135 to 40/80/120/160", b([30, 65, 100, 135], [40, 80, 120, 160])))
    W(li("Damage Amp per stack decreased from 6/9/11/13% to 5/6/7/8%", b([6, 9, 11, 13], [5, 6, 7, 8])))
    W(li("Aghanim's Shard: Beastmaster's attacks on enemy heroes also apply the Wild Axes debuff of its corresponding level. Illusions of Beastmaster don't apply Wild Axes stacks", t("NEW")))
    W(ul_close())
    W(ability("Summon Razorback"))
    W(ul_open())
    W(li("Call of the Wild Boar renamed to Summon Razorback", t("MISC")))
    W(li("Boar's armor increased by 1",
         bstat_u("npc_dota_beastmaster_boar", "ArmorPhysical", "7.40c", 1),
         extra=note_box(unit="npc_dota_beastmaster_boar", field="ArmorPhysical", before_patch="7.40c")))
    W(li("Boar Attack Damage increased from 25/40/55/70 to 30/45/60/75", b([25, 40, 55, 70], [30, 45, 60, 75])))
    W(ul_close())
    W(ability_change(
        old=dict(
            name="Call of the Wild Hawk",
            slug="beastmaster_call_of_the_wild_hawk",
            desc=[
                "Active.",
                "Beastmaster summons a Hawk that circles around him and dives onto an enemy within 500 range, dealing 50/80/110/140 damage and rooting them for 0.25/0.5/0.75/1s.",
                "Hawk cannot be controlled, prioritizes heroes, and is killed upon Beastmaster's death. Hawk has an attack interval of 4s, but it scales with attack speed.",
                "Hawk Duration: 25s. Mana Cost: 50. Cooldown: 45/40/35/30s.",
                aghs_shard_line("Summons an additional Hawk."),
            ],
        ),
        new=dict(
            name="Summon Raptors",
            slug="beastmaster_summon_raptor",
            desc=[
                "Active. Now a separately leveled ability, occupying Inner Beast's old slot (Inner Beast moved to innate).",
                "Summons 2 hawks (with 0.75s delay between them) that circle around Beastmaster and dive onto an enemy within 500 range, dealing 60/95/130/165 damage and rooting them for 0.4/0.6/0.8/1s.",
                "Hawks now prioritize Beastmaster's current attack target when selecting their Dive target.",
                "Hawks are invisible whenever Beastmaster is invisible or affected by Smoke of Deceit. They do not attack while invisible.",
                "Mana Cost: 50. Cooldown: 30s.",
            ],
        ),
        summary="New ability.",
        tag="new",
    ))
    W(ul_open())
    W(li("Cooldown decreased from 45/40/35/30s to 30s", b([45, 40, 35, 30], 30, l=True)))
    W(li("Dive Damage increased from 50/80/110/140 to 60/95/130/165", b([50, 80, 110, 140], [60, 95, 130, 165])))
    W(li("Root Duration increased from 0.25/0.5/0.75/1s to 0.4/0.6/0.8/1s", b([0.25, 0.5, 0.75, 1], [0.4, 0.6, 0.8, 1])))
    W(li("Hawk armor increased by 1",
         bstat_u("npc_dota_beastmaster_hawk", "ArmorPhysical", "7.40c", 1),
         extra=note_box(unit="npc_dota_beastmaster_hawk", field="ArmorPhysical", before_patch="7.40c")))
    W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent -5s Call of the Wild Cooldown replaced with +5 Armor", t("REWORK")))
    W(li("Level 15 Talent +15 Inner Beast Attack Speed replaced with +200 Primal Roar Cast Range", t("REWORK")))
    W(ul_close())

    # Bloodseeker
    W(hero_header("Bloodseeker"))
    W(ability("Sanguivore"))
    W(ul_open())
    W(li_formula("Max Health Heal changed",
                 "1.5% + 1.5% per level up", "1.5% per level",
                 lambda L: 1.5 * L, lambda L: 1.5 * L))
    W(ul_close())
    W(subnote("Effective values are not changed"))
    W(ability("Bloodrage"))
    W(ul_open())
    W(li("Now a no target ability that affects only Bloodseeker", t("REWORK")))
    W(li("Pure damage based on target's max health with Aghanim's Shard now pierces Debuff Immunity", t("BUFF")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Blood Rite Silence Duration increased from +2.5s to +3s", b(2.5, 3)))
    W(ul_close())

    # Bounty Hunter
    W(hero_header("Bounty Hunter"))
    W(ability_change(
        old=dict(
            name="Big Game Hunter",
            innate=True,
            desc=[
                "Passive.",
                "When getting a kill or assist on an enemy with a kill streak, Bounty Hunter gains <b>10% extra gold</b>.",
            ],
        ),
        new=dict(
            name="Big Game Hunter",
            innate=True,
            desc=[
                "Passive.",
                "Bounty Hunter receives <b>15% more kill and assist gold</b> if the dying enemy hero is <b>Big Game</b>. An enemy hero is considered Big Game if they are one of the <b>top 3 net worth heroes</b> on the enemy team."
                + inline_note(
                    "Bounty Hunter has a list of heroes currently considered Big Game, accessible by pressing a special button over the innate."
                    "<br>These heroes also have a debuff pointing out that they're among the three Big Game targets — visible only to Bounty Hunter and his allies."
                ),
            ],
        ),
        summary="Innate reworked.",
        tag="rework",
    ))
    W(ability("Jinada"))
    W(ul_open())
    W(li("Gold Steal increased from 12/20/28/36 to 15/22/29/36", b([12, 20, 28, 36], [15, 22, 29, 36])))
    W(ul_close())
    W(ability("Shadow Walk", slug="bounty_hunter_wind_walk"))
    W(ul_open())
    W(li("Now grants 8/12/16/20% bonus movement speed when active", t("BUFF"),
         extra=inline_note("Also applies to Friendly Shadow")))
    W(ul_close())
    W(ability("Track"))
    W(ul_open())
    W(li("No longer grants 12/16/20% bonus movement speed to Bounty Hunter", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Damage increased from +25 to +30", b(25, 30)))
    W(ul_close())

    # Brewmaster
    W(hero_header("Brewmaster"))
    W(ability("Liquid Courage"))
    W(ul_open())
    W(li_formula("Max Status Resist changed",
                 "10.5% + 0.5% per level up", "10% + 0.5% per level",
                 lambda L: 10.0 + 0.5 * L, lambda L: 10.0 + 0.5 * L))
    W(ul_close())
    W(subnote("Effective values are not changed"))
    W(ability("Primal Split"))
    W(ul_open())
    W(li("Earth Brewling's Hurl Boulder Stun Duration decreased from 1.6/1.6/1.6/2s to 1.6/1.6/1.6/1.8s", b([1.6, 1.6, 1.6, 2], [1.6, 1.6, 1.6, 1.8])))
    W(li("Storm Brewling's Cyclone Duration decreased from 3/4/5/6s to 3/3.75/4.5/5.25s", b([3, 4, 5, 6], [3, 3.75, 4.5, 5.25])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +1s Drunken Brawler Brewed Up / Extend Duration replaced with +2/1s Drunken Brawler Brewed Up / Extend Duration", t("REWORK")))
    W(ul_close())

    # Bristleback
    W(hero_header("Bristleback"))
    W(ability("Prickly"))
    W(ul_open())
    W(li_formula("Damage and debuff duration amplification changed",
                 "10%", "4.5% + 0.5% per level",
                 lambda L: 10.0, lambda L: 4.5 + 0.5 * L))
    W(ul_close())
    W(ability("Viscous Nasal Goo"))
    W(ul_open())
    W(li("Stack Limit increased from 4 to 6", b(4, 6)))
    W(li("Now has the same duration on all units", t("NERF"),
         extra=inline_note("Used to have double duration on creeps")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent +12% Spell Lifesteal replaced with -25 Bristleback Damage Threshold", t("REWORK")))
    W(ul_close())

    # Broodmother
    W(hero_header("Broodmother"))
    W(ability("Spider's Milk"))
    W(ul_open())
    W(li_formula("Hero Health as Heal changed",
                 "2%", "1.9% + 0.1% per level",
                 lambda L: 2.0, lambda L: 1.9 + 0.1 * L))
    W(ul_close())
    W(ability("Insatiable Hunger"))
    W(ul_open())
    W(li("Now also applies lifesteal to Spiderlings within 800 range of Broodmother", t("NEW")))
    W(ul_close())
    W(ability("Spin Web"))
    W(ul_open())
    W(li("Movespeed Bonus decreased from 10/22/34/46% to 10/20/30/40%", b([10, 22, 34, 46], [10, 20, 30, 40])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Spiderlings Health increased from +150 to +175", b(150, 175)))
    W(li("Level 15 Talent Incapacitating Bite Attack Bonus decreased from +6 to +5", b(6, 5)))
    W(li("Level 25 Talent -0.15s BAT during Insatiable Hunger now also affects Spiderlings within 800 range", t("NEW")))
    W(ul_close())

    # Centaur Warrunner
    W(hero_header("Centaur Warrunner"))
    W(ul_open())
    W(li("Strength gain increased from 4.0 to 4.2", b(4.0, 4.2)))
    W(ul_close())
    W(ability_change(
        old=dict(
            name="Rawhide",
            innate=True,
            desc=[
                "Passive.",
                "Centaur Warrunner permanently gains <b>+40 max health</b> every <b>120s</b>.",
            ],
        ),
        new=dict(
            name="Horsepower",
            innate=True,
            desc=[
                "Passive.",
                "Centaur Warrunner gains <b>30% of his Strength as bonus movement speed</b>."
                + inline_note("This movement speed bonus does not stack with bonuses from boots."),
            ],
        ),
        summary="New innate ability.",
        tag="new",
    ))

    # Chaos Knight
    W(hero_header("Chaos Knight"))
    W(ability_change(
        old=dict(
            name="Reins of Chaos",
            innate=True,
            desc=[
                "Passive.",
                "Whenever illusions of Chaos Knight are created, there is a 50% chance that an additional 1 illusion will spawn.",
            ],
        ),
        new=dict(
            name="Fundamental Forging",
            innate=True,
            desc=[
                "Passive.",
                "When Chaos Knight crafts a neutral item, it gets an <b>additional random enchantment</b> that doesn't provide negative stats."
                + inline_note(
                    "The random enchantment is selected from all available enchantments in that tier, including ones that are normally not available for Strength heroes."
                    "<br>Due to negative stats, Chaos Knight can't randomly get Crude, Nimble, Keen-Eyed, Titanic, Greedy, Hulking, Audacious, Feverish, and Manic enchantments."
                    "<br>The random enchantment is different from the one used in crafting."
                ),
            ],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Reality Rift"))
    W(ul_open())
    W(li("Cooldown decreased from 18/14/10/6s to 15/12/9/6s", b([18, 14, 10, 6], [15, 12, 9, 6], l=True)))
    W(ul_close())
    W(ability("Chaos Strike"))
    W(ul_open())
    W(li("Critical Lifesteal increased from 24/36/48/60% to 30/40/50/60%", b([24, 36, 48, 60], [30, 40, 50, 60])))
    W(ul_close())
    W(ability("Phantasm"))
    W(ul_open())
    W(li("Aghanim's Scepter now provides a passive component to this ability", t("NEW"),
         extra=inline_note("Whenever an illusion of Chaos Knight is created, there is a 50% chance to create an additional illusion under Chaos Knight's control. Bonus illusion will be under Chaos Knight's control even if other illusions were made by an enemy.")))
    W(li("Aghanim's Scepter no longer guarantees to create an additional illusion on cast", t("DEL")))
    W(ul_close())

    # Chen
    W(hero_header("Chen"))
    W(ability_change(
        old=dict(
            name="Summon Convert",
            innate=True,
            desc=[
                "Active, levels with Holy Persuasion.",
                "Chen summons a convert to fight for him. The convert gains bonuses from Holy Persuasion, including its abilities. Health is set to 200 + 80 × Chen's Level. The convert is considered a creep-hero.",
                "Only one convert can be summoned at a time, and it dies if Chen dies. Mana Cost: 50. Cooldown: 30s. Cooldown starts once the convert dies and automatically refreshes on Chen's respawn.",
                "Which creature is summoned depends on the chosen Facet. Summoned convert counts toward Holy Persuasion's Max Units limit.",
            ],
        ),
        new=dict(
            name="Zealot",
            slug="chen_zealot",
            innate=True,
            desc=[
                "Passive and active components. Improves with game's time.",
                "When Chen respawns, he is joined in battle by a Zealot — a melee creep warrior with the Martyrdom ability. Zealot has the same stats as the current melee creeps on his team (including super or mega form), but has 125 attack range, base damage increased by 2 per Chen's level, base health regen increased from 0.5 to 2.5, and doesn't have Runty attack type. Zealot respawns after 60s dead.",
                "<b>Martyrdom:</b> 500-range unit-targeted ability on the Zealot creep, targeting either an enemy or ally. When cast, the Zealot sacrifices itself, firing a projectile at 1000 speed dealing damage to enemies or healing allies. Damage = 25 + 20% of the Zealot's current health; healing = 50% of these values.",
                "Can also be cast on a controlled unit to teleport it to Chen after a 6s delay. Self-targeting teleports all controlled units. <b>Mana Cost:</b> 50. <b>Cooldown:</b> 10s."
                + inline_note("Mechanics moved from Divine Favor without any changes."),
            ],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Holy Persuasion"))
    W(ul_open())
    W(li("Zealots receive the benefits from Holy Persuasion", t("NEW")))
    W(li("Now may be cast on existing persuaded creeps that have not been damaged in the last 3 seconds to unsummon them", t("NEW"),
         extra=inline_note("Unsummoning a unit has a global cast range, costs no mana and sets ability to a 3s cooldown")))
    W(li("Now increases all of creature's outgoing damage by 0/6/12/18% instead of only increasing attack damage by 4/8/12/16", t("REWORK")))
    W(ul_close())
    W(ability("Divine Favor"))
    W(ul_open())
    W(li("Self-casting no longer teleports Chen's creeps to him", t("DEL"),
         extra=inline_note("Still applies the Divine Favor buff to all of them")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +150 Convert Attack Speed replaced with +25% Zealot Health/Damage", t("REWORK")))
    W(li("Level 15 Talent +14 Holy Persuasion Damage replaced with +12% Holy Persuasion Damage", t("REWORK")))
    W(ul_close())

    # Clinkz
    W(hero_header("Clinkz"))
    W(ul_open())
    W(li("Base Movement Speed decreased from 290 to 285", b(290, 285)))
    W(ul_close())
    W(ability("Strafe"))
    W(ul_open())
    W(li("Skeleton attack speed multiplier decreased from 50% to 40%", b(50, 40)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Death Pact Health increased from +350 to +400", b(350, 400)))
    W(ul_close())

    # Clockwerk
    W(hero_header("Clockwerk"))
    W(ability_change(
        old=dict(
            name="Armor Power",
            innate=True,
            desc=[
                "Passive.",
                "Clockwerk's outgoing damage is increased by 0.25% per point of armor.",
            ],
        ),
        new=dict(
            name="Armor Power",
            innate=True,
            desc=[
                "Passive.",
                "Clockwerk's outgoing damage is increased by 0.25% per point of armor.",
                "Clockwerk can self-cast a Chainmail item to consume it, gaining +4 Armor per Chainmail consumed. Number of stacks is unlimited.",
            ],
        ),
        summary="Innate reworked.",
        tag="rework",
    ))
    W(ability("Battery Assault"))
    W(ul_open())
    W(li("Mana Cost decreased from 90 to 75/80/85/90", b(90, [75, 80, 85, 90], l=True)))
    W(ul_close())
    W(ability("Power Cogs"))
    W(ul_open())
    W(li("Clockwerk can now move freely through the cogs, sinking them down while walking over them. Other units can also walk over sunken Power Cogs", t("NEW")))
    W(li("Mana Cost rescaled from 70 to 60/65/70/75", b(70, [60, 65, 70, 75], l=True)))
    W(li("Mana Burn increased from 35/70/105/140 to 35/75/115/155", b([35, 70, 105, 140], [35, 75, 115, 155])))
    W(ul_close())
    W(ability_change(
        old=dict(
            name="Overclocking",
            slug="rattletrap_overclocking",
            desc=[
                "Active (Aghanim's Scepter upgrade). All of Clockwerk's abilities are supercharged for the duration:",
                "&nbsp;&nbsp;• Battery Assault damages and stuns all enemies within its radius.",
                "&nbsp;&nbsp;• Power Cogs increase Clockwerk's Attack Speed by 250 while he is inside.",
                "&nbsp;&nbsp;• Rocket Flare cooldown decreased to 3.5s and fires 2 additional flares to either side of the target.",
                "&nbsp;&nbsp;• Hookshot stun radius and duration increased by 50%.",
                "&nbsp;&nbsp;• Jetpack movement speed bonus increased from 20% to 40%.",
                "When duration expires, Clockwerk's movement and attack speed are slowed by 100% briefly.",
                "Duration: 13s. Mana: 90. Cooldown: 50s.",
            ],
        ),
        new=dict(
            name="Overclocking",
            slug="rattletrap_overclocking",
            desc=[
                "Active (Aghanim's Scepter upgrade). All of Clockwerk's abilities are supercharged for the duration:",
                "&nbsp;&nbsp;• Battery Assault damages and stuns all enemies within its radius — radius increased to 330.",
                "&nbsp;&nbsp;• Power Cogs radius increased to 330 and Clockwerk gets +25% bonus armor while near cogs.",
                "&nbsp;&nbsp;• Rocket Flare damage, vision and slow duration increased by 35%.",
                "&nbsp;&nbsp;• Hookshot stun radius and duration increased by 50%.",
                "&nbsp;&nbsp;• Jetpack movement speed bonus increased from 20% to 40%.",
                "Duration: 18s. Mana: 90. Cooldown: 50s.",
            ],
        ),
        summary="Ability reworked.",
        tag="rework",
    ))
    W(ul_open())
    W(li("Duration increased from 13s to 18s", b(13, 18)))
    W(li("Now also increases Battery Assault radius to 330", t("NEW")))
    W(li("Now also increases Power Cogs radius to 330 and provides 25% bonus armor to Clockwerk while he is near cogs", t("NEW")))
    W(li("Now increases Rocket Flare damage, vision and slow duration by 35%", t("NEW")))
    W(li("No longer increases Clockwerk's attack speed while inside Power Cogs", t("DEL")))
    W(li("No longer decreases Rocket Flare cooldown to 3.5s", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +0.4s Rocket Flare Slow Duration replaced with +1.5 Mana Regen", t("REWORK")))
    W(li("Level 15 Talent +2 Power Cogs Hits To Kill replaced with -10s Hookshot Cooldown", t("REWORK")))
    W(li("Level 25 Talent Debuff Immunity Inside Power Cogs replaced with 3 Rocket Flare Charges", t("REWORK")))
    W(ul_close())

    # Crystal Maiden
    W(hero_header("Crystal Maiden"))
    _cm_pill, _cm_table = scale_pill(
        "30% + 2% per level",
        lambda L: 30.0 + 2.0 * L,
    )
    W(ability_change(
        old=dict(
            name="Blueheart Floe",
            innate=True,
            desc=[
                "Passive.",
                "Crystal Maiden has <b>50% Mana Regen Amplification</b>.",
            ],
        ),
        new=dict(
            name="Glacial Guard",
            slug="crystal_maiden_glacial_guard",
            innate=True,
            desc=[
                "Passive.",
                "A portion of the mana Crystal Maiden spends on her abilities is converted into a physical barrier for 8s. Barriers stack, but each instance has independent duration.",
                "Mana Spent to Barrier: " + _cm_pill + ".",
            ],
            tables=[_cm_table],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Arcane Aura", slug="crystal_maiden_brilliance_aura"))
    W(ul_open())
    W(li("Now also passively provides Crystal Maiden with 20/40/60/80% mana regen amplification", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent +225 Attack Speed replaced with +20% Glacial Guard Mana Spent To Barrier", t("REWORK")))
    W(ul_close())

    # Dark Seer
    W(hero_header("Dark Seer"))
    W(ability_change(
        old=dict(
            name="Aggrandize",
            innate=True,
            desc=[
                "Passive.",
                "When Dark Seer levels up, he restores a percentage of his max Health and Mana. Restore percentage = <b>10% + 2% per hero level</b>. Disabled by Break.",
                "Also passively grants <b>1 Attack Speed per point of Intelligence</b>.",
            ],
        ),
        new=dict(
            name="Quick Wit",
            slug="dark_seer_aggrandize",
            innate=True,
            desc=[
                "Passive.",
                "Whenever Dark Seer casts an ability, he restores 8.5% of Max Health and 8.5% of Max Mana, plus 1.5% per Dark Seer level.",
                "Also provides Dark Seer with +1 attack speed for each point of Intelligence.",
            ],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ul_open())
    W(li("Max Health and Mana Restore base value decreased from 10% to 8.5%", b(10, 8.5)))
    W(li("Now also provides Dark Seer +1 attack speed from each point of Intelligence", t("NEW")))
    W(li("Aggrandize renamed to Quick Wit", t("MISC")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Ion Shell Provides +250 Max Health replaced with -1.5s Surge Cooldown", t("REWORK")))
    W(ul_close())

    # Dark Willow
    W(hero_header("Dark Willow"))
    W(ability_change(
        old=dict(
            name="Pixie Dust",
            innate=True,
            desc=[
                "Passive.",
                "Whenever a hero ability makes Dark Willow untargetable or hidden, she gains <b>+100% Health Regen</b> and <b>+100% Mana Regen</b> while in that state.",
            ],
        ),
        new=dict(
            name="Pixie Dust",
            innate=True,
            desc=[
                "Passive.",
                "Dark Willow's Health Regen and Mana Regen always have 20% Amplification.",
                "Amplification increases to 100% whenever she becomes untargetable or invulnerable.",
            ],
        ),
        summary="Innate reworked.",
        tag="rework",
    ))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Intelligence increased from +10 to +12", b(10, 12)))
    W(li("Level 15 Talent Terrorize Cooldown Reduction increased from 15s to 20s", b(15, 20, l=True)))
    W(ul_close())

    # Dawnbreaker
    W(hero_header("Dawnbreaker"))
    W(ul_open())
    W(li("Base damage increased by 6", bstat_h("Dawnbreaker", "AttackDamageMin", "7.40c", 6), extra=note_box(hero="Dawnbreaker", field="AttackDamageMin", before_patch="7.40c")))
    W(li("Damage at level 1 increased from 50–54 to 56–60", br(50, 54, 56, 60)))
    W(ul_close())
    W(ability("Break of Dawn"))
    W(ul_open())
    W(li_formula("Max Damage Increase changed",
                 "25%", "10% + 1% per level",
                 lambda L: 25.0, lambda L: 10.0 + 1.0 * L))
    W(li("Bonuses granted are now at their maximum for any daytime caused by Dawnbreaker's abilities for the entirety of that daytime", t("NEW")))
    W(li("Aghanim's Scepter: Amplifies heals Dawnbreaker provides by Break of Dawn's current damage increase value", t("NEW")))
    W(ul_close())
    W(ability("Solar Guardian"))
    W(ul_open())
    W(li("Cooldown decreased from 120/105/90s to 110/100/90s", b([120, 105, 90], [110, 100, 90], l=True)))
    W(li("Now causes a 6 second temporary daytime when the cast starts", t("NEW")))
    W(li("Aghanim's Scepter no longer increases heal per pulse", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +15% Celestial Hammer Slow replaced with Celestial Hammer Trail Grants Movement Speed to Allies", t("REWORK")))
    W(li("Level 10 Talent +15% Break of Dawn Max Damage replaced with +25% Luminosity Critical Strike Damage", t("REWORK")))
    W(li("Level 15 Talent Solar Guardian Cooldown Reduction increased from 15s to 20s", b(15, 20)))
    W(li("Level 15 Talent +40% Luminosity Critical Strike Damage replaced with +40% Celestial Hammer Trail/Hammer Damage", t("REWORK")))
    W(ul_close())

    # Dazzle
    W(hero_header("Dazzle"))
    W(ability("Weave", slug="dazzle_innate_weave"))
    W(ul_open())
    W(li("No longer levels with Nothl Projection", t("REWORK")))
    W(li("Armor Change per stack rescaled from 0.5/0.75/1/1.25 to 1", b([0.5, 0.75, 1, 1.25], 1)))
    W(li_formula("Duration changed", "8s", "6.9s + 0.1s per level",
                 lambda L: 8.0, lambda L: 6.9 + 0.1*L, value_fmt="{:.1f}s"))
    W(li("Aghanim's Shard: Applying a stack of Weave on an ally heals them for 60 per stack of Weave, including the stack that was just applied", t("NEW")))
    W(ul_close())
    W(ability("Nothl Projection"))
    W(ul_open())
    W(li("No longer does a hard dispel on Dazzle when projection ends", t("DEL")))
    W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
    W(ul_close())

    # Death Prophet
    W(hero_header("Death Prophet"))
    W(ul_open())
    W(li("Base Armor increased by 1", bstat_h("Death Prophet", "ArmorPhysical", "7.40c", 1), extra=note_box(hero="Death Prophet", field="ArmorPhysical", before_patch="7.40c")))
    W(ul_close())
    W(ability("Witchcraft"))
    W(ul_open())
    W(li_formula("Movement speed bonus changed",
                 "0.75% + 0.75% per level up", "0.5% + 0.75% per level",
                 lambda L: 0.5 + 0.75 * L, lambda L: 0.5 + 0.75 * L))
    W(li_formula("Cooldown Reduction changed",
                 "0.75% + 0.75% per level up", "0.75% per level",
                 lambda L: 0.75 * L, lambda L: 0.75 * L))
    W(ul_close())
    W(subnote("Effective values are not changed"))
    W(ability("Silence"))
    W(ul_open())
    W(li("Projectile speed increased from 1400 to 1750", b(1400, 1750)))
    W(ul_close())
    W(ability("Exorcism"))
    W(ul_open())
    W(li("Ghost spawn rate improved from 0.35s to 0.25s", b(0.35, 0.25)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +12% Magic Resistance replaced with +200 Health", t("REWORK")))
    W(li("Level 10 Talent +30 Attack Speed replaced with +75 Silence AoE", t("REWORK")))
    W(li("Level 15 Talent +100 Silence AoE replaced with +50 Attack Speed", t("REWORK")))
    W(li("Level 20 Talent +400 Health replaced with +6 Exorcism Spirits", t("REWORK")))
    W(li("Level 25 Talent +8 Exorcism Spirits replaced with Deaths During Exorcism Extend Duration by +8s (both allied and enemy heroes count)", t("REWORK")))
    W(ul_close())

    # Disruptor
    W(hero_header("Disruptor"))
    W(ability("Electromagnetic Repulsion"))
    W(ul_open())
    W(li("Now deals damage equal to 1.5x of Disruptor's Intelligence", t("NEW")))
    W(ul_close())
    W(ability("Thunder Strike"))
    W(ul_open())
    W(li("Strike Damage increased from 25/55/85/115 to 30/60/90/120", b([25, 55, 85, 115], [30, 60, 90, 120])))
    W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
    W(ul_close())
    W(ability("Kinetic Fence"))
    W(ul_open())
    W(li("Cast Range increased from 1050 to 1200", b(1050, 1200)))
    W(li("Cooldown decreased from 20/18/16/14s to 14s", b([20, 18, 16, 14], 14, l=True)))
    W(li("Duration increased from 2.6/3.2/3.8/4.4s to 4.4s", b([2.6, 3.2, 3.8, 4.4], 4.4),
         extra=inline_note("Can be increased with Kinetic Field Duration talent")))
    W(li("Formation Delay increased from 0.4s to 1s", b(0.4, 1)))
    W(li("Aghanim's Shard: Now grants the Kinetic Field ability. Has only one level instead of sharing levels with Kinetic Fence", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +10%/300 Glimpse Distance To Damage/Max increased to +15%/300", t("BUFF")))
    W(li("Level 20 Talent +150 Electromagnetic Repulsion Radius/Knockback replaced with +75 Static Storm Radius", t("REWORK")))
    W(li("Level 25 Talent +150 Static Storm Radius replaced with +6 Thunder Strike Strikes (also decreases Strike Interval by 50%)", t("REWORK"),
         extra=inline_note("As a result, increases overall duration from 6s to 9s — " + b(6, 9))))
    W(li("Level 25 Talent -12s Glimpse Cooldown replaced with 2 Glimpse Charges", t("REWORK")))
    W(ul_close())

    # Doom
    W(hero_header("Doom"))
    W(ability_change(
        old=dict(
            name="Lvl ? Pain",
            slug="doom_bringer_lvl_pain",
            innate=True,
            desc=[
                "Passive.",
                "Doom's attacks deal <b>25% more damage</b> to enemies whose level is lower than his."
                + inline_note("Also works at level 30. Only Doom's own attacks count, not damage from allied sources."),
            ],
        ),
        new=dict(
            name="Lvl ? Pain",
            slug="doom_bringer_lvl_pain",
            innate=True,
            desc=[
                "Passive.",
                "When Doom attacks enemy heroes, he applies a curse upon them. After 2.5s, the cursed hero bursts with a pillar of fire, damaging itself and all enemy units in a 66 AoE for 15% of the damage taken from Doom (the hero) over this duration, including damage from the attack that applied the curse.",
                "If the cursed hero's level is a multiple of 6, the curse damage and radius will be increased by 66%.",
            ],
        ),
        summary="Innate reworked.",
        tag="rework",
    ))
    W(ability("Devour"))
    W(ul_open())
    W(li("Cooldown decreased from 70s to 66s", b(70, 66, l=True)))
    W(li("Aghanim's Shard: Replaces cooldown with 2 charges with 66s restore time. Allows to devour Ancient Neutral Creeps. Gained spells also have 20% bonus AoE and 40% Spell Amplification", t("NEW")))
    W(li("Now the default cast gained on learning Devour is the one that grants abilities of devoured creeps, and alt-cast state keeps the ones that Doom currently has", t("MISC")))
    W(ul_close())
    W(ability("Scorched Earth"))
    W(ul_open())
    W(li("Radius increased from 600 to 666", b(600, 666)))
    W(li("Now also provides Doom with 7/8/9/10 bonus health regen", t("NEW")))
    W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
    W(ul_close())
    W(ability("Infernal Blade"))
    W(ul_open())
    W(li("Stun Duration increased from 0.6s to 0.66s", b(0.6, 0.66)))
    W(ul_close())
    W(ability("Doom"))
    W(ul_open())
    W(li("Damage per second increased from 25/45/65 to 25/45/66", b([25, 45, 65], [25, 45, 66])))
    W(li("Aghanim's Scepter now also applies Break to affected enemies", t("NEW")))
    W(li("Aghanim's Scepter no longer increases damage per second by 15", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Devour Can Target Ancients replaced with +66 Damage", t("REWORK")))
    W(li("Level 15 Talent Scorched Earth Movement Speed increased from +5% to +7%", b(5, 7)))
    W(li("Level 20 Talent -10s Scorched Earth Cooldown replaced with -10s Doom Cooldown", t("REWORK")))
    W(li("Level 25 Talent Doom applies Break replaced with Permanent Scorched Earth (ability becomes toggleable with no mana cost and a 2.5s cooldown between toggles)", t("REWORK")))
    W(ul_close())

    # Dragon Knight
    W(hero_header("Dragon Knight"))
    W(ul_open())
    W(li("Strength gain decreased from 3.6 to 3.2", b(3.6, 3.2)))
    W(li("Base Movement Speed decreased from 315 to 310", b(315, 310)))
    W(ul_close())
    W(ability("Breathe Fire"))
    W(ul_open())
    W(li("Damage Reduction rescaled from 30% to 20/24/28/32%", b(30, [20, 24, 28, 32])))
    W(li("Cast range increased from 600 to 1000", b(600, 1000)))
    W(li("Fixed the cast indicator not matching the actual damage range of the ability, and also to properly reflect cast range bonuses", t("QoL")))
    W(ul_close())
    W(ability("Dragon Tail"))
    W(ul_open())
    W(li("Now has 25 radius AoE by default", t("NEW")))
    W(li("No longer has an Elder Dragon specific cast range", t("DEL")))
    W(ul_close())
    W(ability("Wyrm's Wrath"))
    W(ul_open())
    W(li("Now always grants the 10/20/30/40 bonus magic damage on attack, and 25/50/75/100 Area of Effect bonus", t("NEW")))
    W(ul_close())
    W(ability_change(
        old=dict(
            name="Elder Dragon Form",
            slug="dragon_knight_elder_dragon_form",
            desc=[
                "Ultimate. No target, transforms Dragon Knight into a ranged dragon for the duration. Levels of the ability determine which dragon form is used.",
                "Level 1: Bonus attack range, +20 bonus move speed, and bonus attack damage. Splash damage 50% within 250 AoE.",
                "Level 2: Adds a Frost debuff on attacks that slows the target's attack and movement speed.",
                "Level 3: Adds a Corrosive poison on attacks that deals magical damage over time and affects buildings.",
                aghs_line("Upgrades to Level 4 Black Dragon (combined effects, magic resistance, free pathing). Also improves Wyrm's Wrath effectiveness while in Dragon Form."),
            ],
        ),
        new=dict(
            name="Elder Dragon Form",
            slug="dragon_knight_elder_dragon_form",
            desc=[
                "Ultimate. No target, transforms Dragon Knight into a ranged dragon for the duration. Now <b>evolves per level — bonuses are cumulative</b>:",
                "<b>Level 1 — Green Dragon:</b> Attacks apply a Corrosive poison that deals 25 magical damage per second for 3s. Affects buildings.",
                "<b>Level 2 — Red Dragon:</b> Attacks gain splash damage dealing 75% of attack damage to all enemies within 275 AoE. Splash also applies Corrosive poison; other attack modifiers only affect the primary target.",
                "<b>Level 3 — Blue Dragon:</b> Attacks also apply a Frost debuff (pierces Debuff Immunity) — 50 attack slow and 30% move slow. Splash attacks now apply both Corrosive poison and Frost to all affected units; other attack modifiers only affect the primary target.",
                "Bonus Move Speed: 25/30/35 (was flat 20). No longer provides bonus attack damage. Now also increases cast range of all abilities by 350 (doesn't affect items).",
                aghs_line("Upgrades to Level 4 Black Dragon: 40 Bonus Move Speed, 35 Corrosive Damage, 100% Splash Damage, 350 Splash Radius, 65 Attack Slow, 45% Movement Slow, +20% Magic Resistance, and free pathing. No longer improves Wyrm's Wrath effectiveness while in Dragon Form. Black Dragon stats slightly rescaled."),
            ],
        ),
        summary="Ability reworked.",
        tag="rework",
    ))
    W(ul_open())
    W(li("Bonus Move Speed increased from 20 to 25/30/35", b(20, [25, 30, 35])))
    W(li("Now also increases cast range of all abilities by 350", t("NEW"),
         extra=inline_note("Doesn't affect items")))
    W(li("Aghanim's Scepter Black Dragon stats slightly rescaled", t("REWORK")))
    W(li("No longer provides bonus attack damage", t("DEL")))
    W(li("Aghanim's Scepter no longer improves Wyrm's Wrath effectiveness while in Dragon Form", t("DEL")))
    W(ul_close())
    W(ability("Fireball"))
    W(ul_open())
    W(li("No longer has an Elder Dragon specific cast range", t("DEL")))
    W(li("Damage per second increased from 75 to 85", b(75, 85)))
    W(li("Duration decreased from 8s to 6s", b(8, 6)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent +60% Breathe Fire Damage/Cast Range replaced with +200 Breathe Fire Damage", t("REWORK")))
    W(li("Level 25 Talent +50% Wyrm's Wrath effect during Elder Dragon Form replaced with +50% Wyrm's Wrath Bonuses", t("REWORK")))
    W(ul_close())

    # Drow Ranger
    W(hero_header("Drow Ranger"))
    W(ul_open())
    W(li("Base Damage decreased by 2", bstat_h("Drow Ranger", "AttackDamageMin", "7.40c", -2), extra=note_box(hero="Drow Ranger", field="AttackDamageMin", before_patch="7.40c")))
    W(li("Damage at level 1 decreased from 51–58 to 49–56", br(51, 58, 49, 56)))
    W(ul_close())
    W(ability("Precision Aura", slug="drow_ranger_trueshot"))
    W(ul_open())
    W(li("No longer levels with Marksmanship", t("REWORK")))
    W(li("Agility Base Bonus rescaled from 4/8/12/16% to 10%", b([4, 8, 12, 16], 10)))
    W(ul_close())
    W(ability("Frost Arrows"))
    W(ul_open())
    W(li("Now also modifies incoming healing with Aghanim's Scepter", t("NEW"),
         extra=inline_note("As a result of Health Restoration changes")))
    W(ul_close())
    W(ability("Gust", slug="drow_ranger_wave_of_silence"))
    W(ul_open())
    W(li("Knockback duration now scales inversely with distance from the target, similar to knockback distance. Minimum knockback duration is 0.4 seconds", t("REWORK")))
    W(ul_close())
    W(ability("Multishot"))
    W(ul_open())
    W(li("Now allows Drow Ranger to move with a 35% penalty and use items while casting Multishot", t("NEW")))
    W(ul_close())
    W(ability("Glacier"))
    W(ul_open())
    W(li("Now Drow Ranger deals 25% more damage when attacking from high ground while on the Glacier", t("NEW")))
    W(li("No longer increases the number of Multishot arrows", t("DEL")))
    W(li("No longer grants True Strike on the hill", t("DEL")))
    W(ul_close())

    # Earth Spirit
    W(hero_header("Earth Spirit"))
    W(ability("Stone Remnant", slug="earth_spirit_stone_caller"))
    W(ul_open())
    W(li_formula("Max Charges changed",
                 "7 + 1 per 4 level ups", "7 + 1 per 4 levels",
                 lambda L: 7 + (L - 1) // 4, lambda L: 7 + L // 4,
                 levels=[1, 4, 8, 12, 16, 20, 24, 28, 30],
                 value_fmt="{:.0f}"))
    W(ul_close())
    W(subnote("Bonus charges are gained 1 level earlier (on levels 4/8/12... instead of 5/9/13...)"))
    W(ability("Boulder Smash"))
    W(ul_open())
    W(li("Slow Duration increased from 1.25/2.5/3.25/4s to 1.75/2.5/3.25/4s", b([1.25, 2.5, 3.25, 4], [1.75, 2.5, 3.25, 4])))
    W(ul_close())
    W(ability("Geomagnetic Grip"))
    W(ul_open())
    W(li("Silence Duration increased from 2/2.5/3/3.5s to 2.3/2.7/3.1/3.5s", b([2, 2.5, 3, 3.5], [2.3, 2.7, 3.1, 3.5])))
    W(ul_close())
    W(ability("Magnetize"))
    W(ul_open())
    W(li("Damage per second increased from 45/85/125 to 45/90/135", b([45, 85, 125], [45, 90, 135])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Geomagnetic Grip Remnant Damage increased from +175 to +250", b(175, 250)))
    W(ul_close())

    # Earthshaker
    W(hero_header("Earthshaker"))
    W(ability("Slugger"))
    W(ul_open())
    W(li("No longer levels with Echo Slam", t("REWORK")))
    W(li_formula("Damage (Creep Death) changed",
                 "30/45/60/75", "27 + 3 per level",
                 lambda L: 75.0, lambda L: 27.0 + 3.0 * L))
    W(li_formula("Damage (Hero Death) changed",
                 "150/250/350/450", "135 + 15 per level",
                 lambda L: 450.0, lambda L: 135.0 + 15.0 * L))
    W(ul_close())
    W(ability("Fissure"))
    W(ul_open())
    W(li("Stun Duration increased from 0.8/1.0/1.2/1.4s to 1.0/1.2/1.4/1.6s", b([0.8, 1.0, 1.2, 1.4], [1.0, 1.2, 1.4, 1.6])))
    W(ul_close())
    W(ability("Aftershock"))
    W(ul_open())
    W(li("Radius increased from 300 to 350", b(300, 350)))
    W(ul_close())
    W(ability("Echo Slam"))
    W(ul_open())
    W(li("Shockwave projectile speed increased from 550 to 650", b(550, 650)))
    W(ul_close())

    # Elder Titan
    W(hero_header("Elder Titan"))
    _et_pill, _et_table = scale_pill(
        "3.6% + 0.4% per level",
        lambda L: 3.6 + 0.4 * L,
        value_fmt="{:.1f}",
    )
    W(ability_change(
        old=dict(
            name="Tip The Scales",
            innate=True,
            desc=[
                "Passive.",
                "(7.37 introduction did not include a mechanic line in the patchnote — needs canonical in-game text.)",
            ],
        ),
        new=dict(
            name="Momentum",        innate=True,
            desc=[
                "Passive.",
                "Elder Titan's armor increases by " + _et_pill + " of his bonus movement speed."
                '<div class="inline-note">Only counts movement speed he has above his base (305) value. '
                'Cannot reduce armor when he is slowed below base movement speed.</div>',
            ],
            tables=[_et_table],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Astral Spirit", slug="elder_titan_ancestral_spirit"))
    W(ul_open())
    W(li("No longer provides armor on return", t("DEL"),
         extra=inline_note("Still grants movement speed, which is then used by the innate ability to provide armor")))
    W(ul_close())
    W(ability("Earth Splitter"))
    W(ul_open())
    W(li("Cooldown decreased from 100s to 100/95/90s", b(100, [100, 95, 90], l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +25 Attack Speed replaced with +150 Echo Stomp Wake Damage", t("REWORK")))
    W(li("Level 15 Talent +25 Astral Spirit Hero Attack replaced with 20% of Bonus Movement Speed as Attack Speed", t("REWORK")))
    W(li("Level 20 Talent +350 Echo Stomp Wake Damage replaced with +30 Astral Spirit Bonus Damage per Hero", t("REWORK")))
    W(ul_close())

    # Ember Spirit
    W(hero_header("Ember Spirit"))
    W(ul_open())
    W(li("Strength gain increased from 2.3 to 2.5", b(2.3, 2.5)))
    W(ul_close())
    W(ability("Immolation"))
    W(ul_open())
    W(li("No longer levels with Fire Remnant", t("REWORK")))
    W(li_formula("Damage per second changed",
                 "10/18/26/34", "10 + 1 per level",
                 lambda L: 34.0, lambda L: 10.0 + 1.0 * L))
    W(li("Radius increased from 175 to 200", b(175, 200)))
    W(li("Aghanim's Shard bonus radius decreased from 175 to 150", b(175, 150)))
    W(ul_close())
    W(subnote("Total Shard radius unchanged with base radius increase"))
    W(ability("Searing Chains"))
    W(ul_open())
    W(li("Mana Cost decreased from 95/105/115/125 to 80/90/100/110", b([95, 105, 115, 125], [80, 90, 100, 110], l=True)))
    W(ul_close())
    W(ability("Sleight of Fist"))
    W(ul_open())
    W(li("Bonus Hero Damage increased from 25/70/115/160 to 50/90/130/170", b([25, 70, 115, 160], [50, 90, 130, 170])))
    W(ul_close())

    # Enchantress
    W(hero_header("Enchantress"))
    W(ability("Rabble-Rouser", slug="enchantress_rabblerouser"))
    W(ul_open())
    W(li_formula("Damage Increase changed",
                 "4% + 4% per level up", "4% per level",
                 lambda L: 4.0 * L, lambda L: 4.0 * L))
    W(ul_close())
    W(subnote("Effective values are not changed"))
    W(ability("Enchant"))
    W(ul_open())
    W(li("Cast Range increased from 500/550/600/650 to 500/600/700/800", b([500, 550, 600, 650], [500, 600, 700, 800])))
    W(li("Now enchanting enemy heroes increases attack range against them by 50/100/150/200 for Enchantress and units under her control", t("NEW")))
    W(ul_close())
    W(ability("Nature's Attendants"))
    W(ul_open())
    W(li("Added a tooltip to display the total max possible heal", t("QoL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Untouchable Attack Slow increased from +70 to +80", b(70, 80)))
    W(ul_close())

    # Enigma
    W(hero_header("Enigma"))
    _en_pill, _en_table = scale_pill(
        "4% + 1% per level",
        lambda L: 4 + 1 * L,
    )
    W(ability_change(
        old=dict(
            name="Gravity Well",
            innate=True,
            desc=[
                "Passive, scales with Black Hole.",
                "Allies in a 500 unit radius around Enigma have an Incoming Damage Reduction buff that gradually increases with proximity: 0% at 500 distance, up to 9/11/13/15% at 200 distance.",
                "Doesn't affect Enigma itself.",
            ],
        ),
        new=dict(
            name="Event Horizon",        innate=True,
            desc=[
                "Passive.",
                "Units in a 600 radius moving away from Enigma have a movespeed penalty equal to " + _en_pill + ".",
            ],
            tables=[_en_table],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +60 Malefice Instance Damage replaced with +100 Event Horizon Radius", t("REWORK")))
    W(ul_close())

    # Faceless Void
    W(hero_header("Faceless Void"))
    W(ability_change(
        old=dict(
            name="Distortion Field",
            innate=True,
            desc=[
                "Passive, levels up with Chronosphere.",
                "Enemy attack projectiles are slowed when they fly near Faceless Void. Affects projectiles even if Faceless Void isn't the target.",
                "<b>Projectile Slow:</b> 25/30/35/40%. <b>Radius:</b> 500.",
            ],
        ),
        new=dict(
            name="Distortion Field",
            innate=True,
            desc=[
                "Passive, no longer levels with Chronosphere.",
                "Now only applies to projectiles targeting Faceless Void or an allied hero within a 1200 radius of him.",
                "Slows enemy attack projectile speed by a flat 40% within a 500 radius around the targeted hero.",
            ],
        ),
        summary="Innate reworked.",
        tag="rework",
    ))
    W(ul_open())
    W(li("Enemy attack projectile speed slow rescaled from 35/40/45/50% to 40%", b([35, 40, 45, 50], 40)))
    W(li("Max slow distance rescaled from 600 around Faceless Void to 500 around the targeted hero", t("REWORK")))
    W(li("Now only applies to projectiles targeting Faceless Void or an allied hero within a 1200 radius of him", t("REWORK")))
    W(li("No longer levels with Chronosphere", t("REWORK")))
    W(ul_close())
    W(ability("Time Walk"))
    W(ul_open())
    W(li("Aghanim's Scepter now also provides Reverse Time Walk sub-ability", t("NEW")))
    W(li("Aghanim's Scepter Time Lock attacks will no longer miss if Reverse Time Walk is used too quickly after Time Walk", t("MISC")))
    W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
    W(ul_close())
    W(ability("Time Dilation"))
    W(ul_open())
    W(li("Duration no longer counts down while under effect of Chronosphere", t("BUFF")))
    W(li("Aghanim's Shard: Increases Attack/Movement Slow per cooldown by 5/5%. Provides Faceless Void with bonus movement and attack speed by the same values per each enemy cooldown extended. The bonus degrades over the duration of the buff. 9/10/11/12 Attack Speed + the same value per affected cooldown, 9/10/11/12% Movement Speed + the same value per affected cooldown",
         t("NEW"),
         extra=inline_note("This buff also doesn't count down under effect of Chronosphere")))
    W(ul_close())
    W(ability("Chronosphere"))
    W(ul_open())
    W(li("Now the default ultimate ability", t("REWORK")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +8% Time Dilation Slow per Cooldown replaced with +125 Time Walk Range", t("REWORK")))
    W(ul_close())

    # Grimstroke
    W(hero_header("Grimstroke"))
    W(ability("Ink Trail"))
    W(ul_open())
    W(li("Now also applied when an enemy hero is affected by any of Grimstroke's abilities", t("NEW")))
    W(li("Now also applied by attacks from Grimstroke's illusions (including Dark Portrait)", t("NEW")))
    _gs_pill, _gs_table = scale_pill(
        "5% + 0.5% per level",
        lambda L: 5.0 + 0.5 * L,
        value_fmt="{:.1f}%",
    )
    W(li("Grimstroke now takes " + _gs_pill + " less damage from enemies affected by Ink Trail",
         t("NEW"), extra=_gs_table))
    W(ul_close())
    W(ability("Stroke of Fate", slug="grimstroke_dark_artistry"))
    W(ul_open())
    W(li("Can now be put on alt-cast to send the stroke straight", t("MISC")))
    W(ul_close())

    # Gyrocopter
    W(hero_header("Gyrocopter"))
    W(ul_open())
    W(li("Base Movement Speed decreased from 320 to 315", b(320, 315)))
    W(ul_close())
    _gy_pill, _gy_table = scale_pill(
        "3.9s + 0.1s per level",
        lambda L: 3.9 + 0.1 * L,
        value_fmt="{:.1f}",
    )
    W(ability_change(
        old=dict(
            name="Chop Shop",
            innate=True,
            desc=[
                "Passive.",
                "Gyrocopter can disassemble most items at all times and sells any Recipe he has for a full cost.",
                "Cannot disassemble Divine Rapier or Hand of Midas.",
            ],
        ),
        new=dict(
            name="Afterburner",
            slug="gyrocopter_afterburner",
            innate=True,
            desc=[
                "Passive.",
                "Whenever Gyrocopter damages an enemy with attacks or abilities, he gains +1 movement speed per hero damaged and +0.5 per creep. Effects stack independently.",
                "Buff duration: " + _gy_pill + ".",
            ],
            tables=[_gy_table],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Flak Cannon"))
    W(ul_open())
    W(li("Aghanim's Scepter upgrade moved into a separate ability", t("MISC")))
    W(ul_close())
    W(ability("Side Gunner", slug="gyrocopter_side_gunner_spawn_ability"))
    W(ul_open())
    W(li("Aghanim's Scepter: Side Gunner is now a separate ability granted by Scepter (effect is unchanged)", t("NEW")))
    W(ul_close())

    # Hoodwink
    W(hero_header("Hoodwink"))
    W(ability("Mistwoods Wayfarer"))
    W(ul_open())
    W(li("No longer levels with Sharpshooter", t("REWORK")))
    W(li_formula("Redirect Chance changed",
                 "14/21/28/35%", "14% + 1% per level",
                 lambda L: 35.0, lambda L: 14.0 + 1.0 * L))
    W(ul_close())
    W(ability("Acorn Shot"))
    W(ul_open())
    W(li("Cast Range rescaled from (Hoodwink's attack range + 100) to 675/700/725/750", t("REWORK"),
         extra=inline_note("As a result, Cast Range increased from 675 to 675/700/725/750 — " + b(675, [675, 700, 725, 750]))))
    W(ul_close())
    W(ability("Bushwhack"))
    W(ul_open())
    W(li("Cast Range increased from 1000 to 1100", b(1000, 1100)))
    W(ul_close())
    W(ability("Scurry"))
    W(ul_open())
    W(li("No longer doubles all sources of evasion for the duration", t("DEL")))
    W(li("Now doubles redirect chance of Mistwoods Wayfarer for the duration", t("NEW")))
    W(ul_close())
    W(ability("Sharpshooter"))
    W(ul_open())
    W(li("Now treats creep heroes as creeps", t("MISC"),
         extra=inline_note("The projectile flies through creeps, dealing them damage for half value, but still applying Slow and Break at full force and duration."
                           "<br>Since Spirit Bear is considered a true hero, the projectile will stop on impact with it.")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Health increased from +150 to +175", b(150, 175)))
    W(li("Level 15 Talent +1 Acorn Shot Bounce replaced with +10 Agility", t("REWORK")))
    W(li("Level 20 Talent -3 Armor Corruption replaced with +2 Acorn Shot Bounces", t("REWORK")))
    W(ul_close())

    # Huskar
    W(hero_header("Huskar"))
    W(ul_open())
    W(li("Intelligence gain decreased from 1.5 to 0", t("MISC"),
         extra=inline_note("Cosmetic for Huskar — his abilities use Health costs, not mana; Intelligence has no functional impact on him.")))
    W(li("Base Movement Speed decreased from 295 to 290", b(295, 290)))
    W(ul_close())
    W(ability("Inner Fire"))
    W(ul_open())
    W(li("Damage increased from 105/170/235/300 to 110/180/250/320", b([105, 170, 235, 300], [110, 180, 250, 320])))
    W(li("Knockback Duration now scales based on Knockback Distance to a minimum of 0.4s", t("REWORK"),
         extra=inline_note("Enemies which are 375 units or farther now receive a flat knockback of 25 units")))
    W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
    W(ul_close())
    W(ability("Burning Spear"))
    W(ul_open())
    W(li("Health Cost changed from 4% of current health to 2% of max health", t("REWORK")))
    W(li("Now also burns enemies for 0.5% of their max health", t("NEW")))
    W(ul_close())
    W(subnote("Huskar can use this ability even if he has less health than the health cost requires"))
    W(ul_open())
    W(li("Now also burns enemies for 0.5% of their max health", t("REWORK")))
    W(ul_close())
    W(ability("Berserker's Blood"))
    W(ul_open())
    W(li("Aghanim's Shard: Can be activated for a health cost. Applies basic dispel to Huskar, then after a delay, heals for the amount of health consumed plus an additional bonus per debuff dispelled. Current HP Cost: 30%. Cooldown: 20s. Cauterize Delay: 3s. Max HP Heal per debuff: 3%", t("NEW")))
    W(ul_close())

    # Invoker
    W(hero_header("Invoker"))
    W(ability("Quas"))
    W(ul_open())
    W(li("Max Level increased from 7 to 8", b(7, 8)))
    W(ul_close())
    W(ability("Wex"))
    W(ul_open())
    W(li("Max Level increased from 7 to 8", b(7, 8)))
    W(ul_close())
    W(ability("Exort"))
    W(ul_open())
    W(li("Max Level increased from 7 to 8", b(7, 8)))
    W(ul_close())
    W(ability("Tornado"))
    W(ul_open())
    W(li_formula("Aghanim's Scepter twister damage decreased",
                 "40 + 10 × Wex Level", "30 + 10 × Wex Level",
                 lambda W: 40 + 10 * W, lambda W: 30 + 10 * W,
                 levels=list(range(2, 12)), level_prefix='W',
                 value_fmt="{:g}"))
    W(ul_close())
    W(ability("Invoke"))
    W(ul_open())
    W(li("Now whenever Invoker gets Aghanim's Scepter or Aghanim's Shard, these items are inert in the inventory until Invoker activates them manually. Upon activation, he will be presented with three upgrades to choose from. Upgrades themselves for both Aghanim's Scepter and Aghanim's Shard are unchanged", t("REWORK")))
    W(li("You can't change selected upgrades. Selling Aghanim's Scepter and buying it again will provide the same upgrade you chose the first time", t("NERF")))
    W(li("Aghanim's Scepter no longer provides +1 level to all three orbs. Now it provides +1 level only to a single orb you choose", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +1 Facet Orb Level replaced with +25 Alacrity Speed/Damage", t("REWORK")))
    W(li("Level 20 Talent +50 Alacrity Speed/Damage replaced with +1 Orb Levels", t("REWORK")))
    W(ul_close())

    # Io
    W(hero_header("Io"))
    _io_pill, _io_table = scale_pill(
        "5% + 0.5% per level",
        lambda L: 5 + 0.5 * L,
        value_fmt="{:.1f}",
    )
    W(ability_change(
        old=dict(
            name="Wellspring",
            innate=True,
            desc=[
                "Passive.",
                "Consumable items and item abilities that restore Health and Mana over time affect Io <b>twice as fast</b>. Total amount of restored Health or Mana remains the same.",
                "Applies to: Healing Salve, Tango, Clarity, Bottle, Urn of Shadows, Spirit Vessel, Pollywog Charm, Mana Draught.",
                "Example: Clarity normally restores 150 mana over 25s; for Io, 150 mana over 12.5s.",
            ],
        ),
        new=dict(
            name="Equilibrium",
            slug="wisp_equilibrium",
            innate=True,
            desc=[
                "Passive.",
                "Io always has bonus Outgoing Damage Amp that linearly scales with its health, reaching maximum " + _io_pill + " at 100% Health.",
                "At the same time, Io has Health Restoration and Healing Amplifications that also linearly scale with its health, reaching the same maximum at 0% Health.",
            ],
            tables=[_io_table],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Overcharge"))
    W(ul_open())
    W(li("Now also provides 35/60/85/110 Attack Speed and 8/10/12/14% Spell Amplification to Io and any tethered Allies", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Strength increased from +7 to +8", b(7, 8)))
    W(li("Level 25 Talent Relocate Cast Delay Reduction increased from 1.5s to 2s", b(1.5, 2)))
    W(ul_close())

    # Jakiro
    W(hero_header("Jakiro"))
    W(ability("Double Trouble"))
    W(ul_open())
    W(li_formula("Attack Damage Reduction changed",
                 "50%", "51% - 1% per level",
                 lambda L: 50.0, lambda L: 51.0 - 1.0 * L, l=True))
    W(ul_close())
    W(ability("Liquid Fire"))
    W(ul_open())
    W(li("Now has a 20 mana cost", t("NERF")))
    W(li("Aghanim's Shard now also reduces mana cost to 0", t("NEW")))
    W(ul_close())
    W(ability("Liquid Frost", slug="jakiro_liquid_ice"))
    W(ul_open())
    W(li("Now has a 20 mana cost", t("NERF")))
    W(li("Aghanim's Shard now also reduces mana cost to 0", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Ice Path Damage increased +60 to +75", t("BUFF")))
    W(li("Level 15 Talent Dual Breath Cooldown Reduction increased from 3s to 3.5s", b(3, 3.5, l=True)))
    W(ul_close())

    # Juggernaut
    W(hero_header("Juggernaut"))
    _jg_pill, _jg_table = scale_pill(
        "2.5% + 0.05% per level",
        lambda L: 2.5 + 0.05 * L,
        value_fmt="{:.2f}",
    )
    W(ability_change(
        old=dict(
            name="Duelist",
            innate=True,
            desc=[
                "Passive.",
                "Juggernaut deals <b>10% more damage</b> to targets that are facing him. Damage bonus is always applied during Omnislash.",
            ],
        ),
        new=dict(
            name="Bladeform",        innate=True,
            desc=[
                "Passive.",
                "Juggernaut receives a stack of Bladeform every 2s he does not take damage. Maximum 10 stacks. Stacks fade after 2s upon taking any damage.",
                "Each stack grants " + _jg_pill + " base Agility bonus and 1% movement bonus.",
            ],
            tables=[_jg_table],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Blade Fury"))
    W(ul_open())
    W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
    W(ul_close())
    W(ability("Healing Ward"))
    W(ul_open())
    W(li("Aghanim's Shard: Increases healing by 1.5% and hits to destroy by 1", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +4% Duelist Damage replaced with -1s Bladeform Stack Gain Interval", t("REWORK")))
    W(li("Level 15 Talent +1% Healing Ward Heal replaced with -15s Omnislash Cooldown", t("REWORK")))
    W(li("Level 15 Talent Movement Speed During Blade Fury increased from +40 to +45", b(40, 45)))
    W(li("Level 20 Talent Blade Fury DPS increased from +90 to +100", b(90, 100)))
    W(li("Level 20 Talent +1 Healing Ward Hits to Destroy replaced with +15% Blade Dance Crit Damage", t("REWORK")))
    W(ul_close())

    # Keeper of the Light
    W(hero_header("Keeper of the Light"))
    W(ul_open())
    W(li("Base Movement Speed decreased from 320 to 315", b(320, 315)))
    W(ul_close())
    W(ability_change(
        old=dict(
            name="Special Reserve",
            innate=True,
            desc=[
                "Passive.",
                "Keeper of the Light's mana <b>cannot go below 75</b>.",
            ],
        ),
        new=dict(
            name="Bright Speed",
            slug="keeper_of_the_light_bright_speed",
            innate=True,
            desc=[
                "Passive.",
                "Keeper of the Light gains +1 movement speed for every 2.5 Intelligence.",
                "Whenever Keeper of the Light moves 300 distance, he leaves behind light that allows him to see in 400 range for 3 seconds.",
            ],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Chakra Magic"))
    W(ul_open())
    W(li("Cooldown rescaled from 18/16/14/12s to 19/16/13/10s", b([18, 16, 14, 12], [19, 16, 13, 10], l=True)))
    W(li("Mana Restore increased from 90/160/230/300 to 105/170/235/300", b([90, 160, 230, 300], [105, 170, 235, 300])))
    W(ul_close())
    W(ability("Blinding Light"))
    W(ul_open())
    W(li("Cast Range increased from 400/500/600/700 to 500/575/650/725", b([400, 500, 600, 700], [500, 575, 650, 725])))
    W(li("Knockback distance changed from 400 to knocking back to the edges of the effect radius, but a minimum knockback distance is 175", t("MISC")))
    W(ul_close())
    W(subnote("Min distance is used for enemies near the edge of AoE"))
    W(ability("Spirit Form"))
    W(ul_open())
    W(li("No longer grants bonus movement speed percentage", t("DEL")))
    W(li("Now increases movement speed bonus of Bright Speed by 50% while active", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent -5s Blinding Light Cooldown replaced with +90 Blinding Light Damage", t("REWORK")))
    W(li("Level 15 Talent -2s Chakra Magic Cooldown replaced with +30% Spirit Form Bright Speed Bonus", t("REWORK")))
    W(li("Level 20 Talent +200 Chakra Magic Mana replaced with +10% Solar Bind Magic Resistance Reduction", t("REWORK")))
    W(li("Level 20 Talent +10% Spirit Form Movement Speed Bonus replaced with +15s Spirit Form Duration", t("REWORK")))
    W(ul_close())

    # Kez
    W(hero_header("Kez"))
    W(ul_open())
    W(li("Base Movement Speed decreased from 315 to 310", b(315, 310)))
    W(li("Base Attack Speed decreased from 110 to 100", b(110, 100)))
    W(ul_close())
    W(ability("Switch Discipline", slug="kez_switch_weapons"))
    W(ul_open())
    W(li_formula("Cooldown changed",
                 "7.75s - 0.25s per level up", "8s - 0.25s per level",
                 lambda L: 8.0 - 0.25 * L, lambda L: 8.0 - 0.25 * L, l=True))
    W(ul_close())
    W(subnote("Effective values are not changed"))
    W(ul_open())
    W(li("Now the first katana hit or ability will deal 12% bonus damage after switching to Katana, and after switching to Sai Kez gains +12% movement speed for 2 seconds", t("NEW")))
    W(li("Aghanim's Scepter no longer restarts the alternate ability cooldown if it was already on cooldown", t("MISC")))
    W(ul_close())
    W(ability("Grappling Claw"))
    W(ul_open())
    W(li("When targeting a tree, now always destroys the targeted tree and ends in the tree's position", t("MISC")))
    W(ul_close())
    W(ability("Talon Toss"))
    W(ul_open())
    W(li("Cast Range decreased from 1200 to 650/750/850/950", b(1200, [650, 750, 850, 950])))
    W(ul_close())
    W(subnote("Now matches Grappling Claw"))
    W(ul_open())
    W(li("Shodo Sai: The proc effect now triggers a critical strike only instead of creating a Mark", t("REWORK")))
    W(li("18% Chance to Mark replaced with 20% Critical Strike Chance", t("REWORK"),
         extra=inline_note("As a result, marks are applied only by parrying and casting Raven's Veil")))
    W(li("No longer restricts Kez from proccing passive Bash spells of Skull Basher and Abyssal Blade", t("BUFF")))
    W(li("Mark Stun Duration increased from 0.4s to 0.5/0.6/0.7/0.8s", b(0.4, [0.5, 0.6, 0.7, 0.8])))
    W(li("No longer has a parry bonus by default", t("DEL")))
    W(li("Aghanim's Shard: Parrying creates a stronger mark that will stun the target for an additional 0.2s and an a crit bonus of 50%", t("NEW")))
    W(ul_close())
    W(ability("Raptor Dance"))
    W(ul_open())
    W(li("No longer provides magic damage immunity", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent +100% Shodo Sai Mark Critical Strike replaced with +80% Shodo Sai Critical Strike", t("REWORK")))
    W(ul_close())

    # Kunkka
    W(hero_header("Kunkka"))
    W(ability("Admiral's Rum"))
    W(ul_open())
    W(li("Can no longer be applied by multiple sources, and will no longer trigger passively if Ghostship already applied the buff", t("MISC"),
         extra=inline_note("Previously, overlapping Rum buffs from different sources could overwrite one another — the strongest buff sometimes ended early when a weaker source re-applied it.")))
    W(li_formula("Cooldown changed",
                 "60s", "60.5s - 0.5s per level",
                 lambda L: 60.0, lambda L: 60.5 - 0.5 * L, l=True))
    W(li_formula("Bonus Movement Speed rescaled",
                 "10%", "7.75% + 0.25% per level",
                 lambda L: 10.0, lambda L: 7.75 + 0.25 * L))
    W(li("Duration decreased from 6s to 5s", b(6, 5)))
    W(li("Delayed Damage decreased from 20% to 18%", b(20, 18)))
    W(ul_close())
    W(ability("Ghostship"))
    W(ul_open())
    W(li("Now applies Admiral's Rum at a 2x factor", t("NEW"),
         extra=inline_note("Multiplication applies to duration, delayed damage and movement speed bonus")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent -15s Admiral's Rum Cooldown replaced with +1s Admiral's Rum Buff Duration", t("REWORK")))
    W(li("Level 15 Talent Tidebringer Damage increased from +70 to +75", b(70, 75)))
    W(li("Level 20 Talent +15% Admiral's Rum Damage Delayed replaced with +80% Tidebringer Cleave", t("REWORK")))
    W(li("Level 25 Talent +130% Tidebringer Cleave replaced with Tidebringer Ignores 25% Armor", t("REWORK")))
    W(ul_close())

    # Largo
    W(hero_header("Largo"))
    W(ability("Encore"))
    W(ul_open())
    W(li_formula("Bonus Duration changed",
                 "10% + 1% per level up", "9% + 1% per level",
                 # Both lambdas resolve to the same in-game values — Valve
                 # re-parametrized the formula with a 1-level shift so the old
                 # "10% + 1%·L" and the new "9% + 1%·L" produce identical
                 # numbers at the hero levels the player actually plays at
                 # (hence the "Effective values are not changed" subnote).
                 lambda L: 9.0 + 1.0 * L, lambda L: 9.0 + 1.0 * L))
    W(ul_close())
    W(subnote("Effective values are not changed"))
    W(ability("Catchy Lick"))
    W(ul_open())
    W(li("Now can lick runes to pull them. Rune-licking refunds spent mana", t("NEW")))
    W(li("Health Regen Duration decreased from 10s to 8s", b(10, 8)))
    W(li("Bonus health regen is now also provided if the target is killed by Catchy Lick", t("NEW")))
    W(ul_close())
    W(ability("Amphibian Rhapsody"))
    W(ul_open())
    W(li("Aghanim's Scepter no longer adds damage to double-strumming", t("DEL")))
    W(ul_close())
    W(ability("Bullbelly Blitz", slug="largo_song_fight_song"))
    W(ul_open())
    W(li("Now also deals 20/30/40 magical damage by default", t("NEW")))
    W(li("Aghanim's Scepter: Increases magic damage by 6/12/18 per Groovin' stack when this song is used in double-strumming", t("NEW")))
    W(ul_close())
    W(ability("Hotfeet Hustle", slug="largo_song_double_time"))
    W(ul_open())
    W(li("Move Speed decreased from 16/22/28% to 16/20/24%", b([16, 22, 28], [16, 20, 24])))
    W(li("Slow Resistance decreased from 70/80/90% to 70/75/80%", b([70, 80, 90], [70, 75, 80])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Croak of Genius Max Health DPS decreased from 1.5% to 1%", b(1.5, 1)))
    W(li("Level 25 Talent Amphibian Rhapsody Song Effects decreased from +35% to +30%", b(35, 30)))
    W(ul_close())

    # Legion Commander
    W(hero_header("Legion Commander"))
    W(ul_open())
    W(li("Base armor decreased by 1", bstat_h("Legion Commander", "ArmorPhysical", "7.40c", -1), extra=note_box(hero="Legion Commander", field="ArmorPhysical", before_patch="7.40c")))
    W(ul_close())
    _lc_pill, _lc_table = scale_pill(
        "1 + 0.1 per level",
        lambda L: 1.0 + 0.1 * L,
        value_fmt="{:.1f}",
    )
    W(ability_change(
        old=dict(
            name="Outfight Them!",
            slug="legion_commander_outfight_them",
            innate=True,
            desc=[
                "Passive, levels up with Duel.",
                "When attacking an enemy hero of <b>equal or higher level</b> than Legion Commander, she gains <b>+30/40/50/60% Health Restoration</b> for <b>4s</b>. Always applies when attacking a max-level enemy hero.",
            ],
        ),
        new=dict(
            name="Outfight Them!",
            slug="legion_commander_outfight_them",
            innate=True,
            desc=[
                "Passive.",
                "Passively grants Legion Commander " + _lc_pill + " bonus armor at all times.",
                "Whenever Legion Commander <b>casts an ability</b>, she gains the same amount again as a <b>stacking 6s buff</b> (stacks independently per cast).",
                "Whenever <b>allies within 1200 range</b> cast an ability, they also gain a 6s buff for <b>50% of the value</b>. Ally buffs stack independently.",
            ],
            tables=[_lc_table],
        ),
        summary="Innate reworked.",
        tag="rework",
    ))
    W(ability("Overwhelming Odds"))
    W(ul_open())
    W(li("Now also applies 100% movement slow upon dealing damage for 0.3s", t("NEW")))
    W(li("Aghanim's Shard reworked: Increases radius by 100. Grants an all damage barrier equal to 50% of the damage dealt with Overwhelming Odds for 6s", t("REWORK")))
    W(ul_close())
    W(ability("Press The Attack"))
    W(ul_open())
    W(li("Multiple instances can now stack independently", t("NEW")))
    W(li("Aghanim's Scepter: Increases bonus movement speed by 12%. Ability becomes cast-point, affecting all allies within the targeted 500 radius area. Legion Commander is always affected, even when outside of the cast area", t("NEW")))
    W(ul_close())
    W(ability("Moment of Courage"))
    W(ul_open())
    W(li("No longer has a 25% proc chance", t("DEL")))
    W(li("Now automatically triggers after taking 7/6/5/4 attacks", t("REWORK"),
         extra=inline_note("Will not activate unless Legion Commander is both attacking and being attacked. Until this requirement is met, the 'prepared' state is kept indefinitely")))
    W(li("Cooldown decreased from 1.7/1.4/1.1/0.8 to 0.3s", b([1.7, 1.4, 1.1, 0.8], 0.3, l=True)))
    W(ul_close())
    W(ability("Duel"))
    W(ul_open())
    W(li("Legion Commander can now use any abilities during Duel", t("NEW"),
         extra=inline_note("Legion Commander will stop attacking as normal during cast animations."
                           "<br>Items can't be used.")))
    W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
    W(li("Aghanim's Scepter reworked: When Legion Commander wins a duel, Press the Attack is automatically triggered around her", t("REWORK")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +12% Press the Attack Movement Speed replaced with +1 Outfight Them! Armor", t("REWORK")))
    W(li("Level 20 Talent +8% Moment of Courage Proc Chance replaced with -1 Moment of Courage Attacks To Trigger", t("REWORK")))
    W(li("Level 20 Talent 300 AoE Press The Attack replaced with +1s Duel Duration", t("REWORK")))
    W(li("Level 25 Talent Press the Attack grants 1.5s Debuff Immunity replaced with Duel Refreshes Cooldown on Victory", t("REWORK")))
    W(ul_close())

    # Leshrac
    W(hero_header("Leshrac"))
    W(ability("Diabolic Edict"))
    W(ul_open())
    W(li("Duration improved from 10s to 8s", b(10, 8)))
    W(ul_close())
    W(subnote("Number of explosions (hence, total damage) is unchanged, explosion interval decreased from 0.25s to 0.225s"))

    # Lich
    W(hero_header("Lich"))
    W(ul_open())
    W(li("Base Mana Regen decreased from 0.75 to -1", b(0.75, -1)))
    W(li("Intelligence gain decreased from 3.8 to 3.4", b(3.8, 3.4)))
    W(ul_close())
    _lich_mana_pill, _lich_mana_table = scale_pill(
        "42% + 3% per level",
        lambda L: 42.0 + 3.0 * L,
        value_fmt="{:.0f}%",
    )
    _lich_xp_pill, _lich_xp_table = scale_pill(
        "69% + 6% per level",
        lambda L: 69.0 + 6.0 * L,
        value_fmt="{:.0f}%",
    )
    W(ability_change(
        old=dict(
            name="Death Charge",
            slug="lich_death_charge",
            innate=True,
            desc=[
                "Passive.",
                "Lich's max mana regeneration is <b>0</b>. Whenever any unit dies nearby, Lich restores a portion of his Max Mana. Dying heroes restore a bigger portion.",
                "<b>Radius:</b> 1200. <b>Max Mana Restored:</b> 2.5% (Creep), 15% (Hero).",
                "Lich can regenerate mana only under effect of a Fountain.",
            ],
        ),
        new=dict(
            name="Sacrifice",
            slug="lich_death_charge",
            innate=True,
            desc=[
                "Active, targets an allied creep within 700 range and instantly kills it.",
                "Lich gains mana equal to " + _lich_mana_pill + " of the creep's <b>current</b> health and experience bounty equal to " + _lich_xp_pill + " of the creep's value.",
                "<b>No Mana Cost. Cooldown: 120s.</b> Starts on extended cooldown with no charges — the first cast is only possible at the 2:00 mark.",
                "Sacrificed creeps count as denies, providing experience to enemy heroes (Lich's experience gain is independent from what enemies receive).",
            ],
            tables=[_lich_mana_table, _lich_xp_table],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent +4s Frost Shield Duration replaced with 2 Frost Shield Charges", t("REWORK")))
    W(li("Level 25 Talent +100 Chain Frost Incremental Damage replaced with Chain Frost Unlimited Bounces", t("REWORK")))
    W(ul_close())

    # Lifestealer
    W(hero_header("Lifestealer"))
    W(ul_open())
    W(li("Base Damage increased by 10",
         bstat_h("Lifestealer", "AttackDamageMin", "7.40c", 10),
         extra=note_box(hero="Lifestealer", field="AttackDamageMin", before_patch="7.40c")))
    W(li("Base Attack Speed increased from 100 to 120", b(100, 120)))
    W(li("Base Movement Speed increased from 315 to 320", b(315, 320)))
    W(li("Damage at level 1 increased from 39–45 to 49–55", br(39, 45, 49, 55)))
    W(ul_close())
    _lsf_pill, _lsf_table = scale_pill(
        "5 per level",
        lambda L: 5.0 * L,
        value_fmt="{:.0f}",
    )
    W(ability_change(
        old=dict(
            name="Feast",
            slug="life_stealer_feast",
            innate=True,
            desc=[
                "Passive, levels up with Infest.",
                "Lifestealer's attacks deal bonus magic damage equal to <b>1.25/1.75/2.25/2.75%</b> of target's max health and lifesteal back <b>1.25/1.75/2.25/2.75%</b> of target's max health.",
                "Also allows hitting allied creeps below <b>75%</b> health (default deny threshold is 50%).",
            ],
        ),
        new=dict(
            name="Ghoul Frenzy",
            slug="life_stealer_ghoul_frenzy",
            innate=True,
            desc=[
                "Passive, occupies the slot vacated by Feast (Feast moved back to a regular ability).",
                "Provides Lifestealer with " + _lsf_pill + " bonus Attack Speed at all times.",
            ],
            tables=[_lsf_table],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Rage"))
    W(ul_open())
    W(li("Now also provides 9/12/15/18% bonus movement speed while active", t("NEW")))
    W(ul_close())
    W(ability("Open Wounds"))
    W(ul_open())
    W(li("Mana Cost decreased from 100 to 90", b(100, 90, l=True)))
    W(li("Max Slow increased from 35/40/45/50% to 50%", b([35, 40, 45, 50], 50, l=True)))
    W(ul_close())
    W(ability("Feast"))
    W(ul_open())
    W(li("Now is a basic ability", t("REWORK")))
    W(li("Heal From Target's Max Health rescaled from 2/2.25/2.5/2.75% to 1.45/2.05/2.65/3.25%", b([2, 2.25, 2.5, 2.75], [1.45, 2.05, 2.65, 3.25])))
    W(li("Max Health Damage rescaled from 2/2.25/2.5/2.75% to 1.45/2.05/2.65/3.25%", b([2, 2.25, 2.5, 2.75], [1.45, 2.05, 2.65, 3.25])))
    W(li("Max Health per Hero Kill increased from 10 to 10/15/20/25", b(10, [10, 15, 20, 25])))
    W(ul_close())
    W(subnote("Is not retroactive"))
    W(ul_open())
    W(li("No longer increases deny health threshold to 75%", t("DEL")))
    W(ul_close())
    W(ability("Infest"))
    W(ul_open())
    W(li("Now can be used on Ancient creeps by default", t("NEW")))
    W(li("Aghanim's Shard reworked: When consuming a creep, enemies also take damage over time equal to 30% of the creep's remaining health. Damage duration: 3s. Has no effect when bursting out of enemy heroes", t("REWORK")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +3% Ghoul Frenzy Movement Speed replaced with +20 Movement Speed", t("REWORK")))
    W(li("Level 15 Talent +15% Open Wounds Slow replaced with 50 Attack Speed on Open Wounds Target", t("REWORK")))
    W(li("Level 15 Talent +50 Ghoul Frenzy Attack Speed replaced with +175 Infest Damage", t("REWORK")))
    W(li("Level 20 Talent Infest Target Movespeed/Health decreased from +15% to +12%", b(15, 12)))
    W(ul_close())

    # Lina
    W(hero_header("Lina"))
    W(ability_change(
        old=dict(
            name="Combustion",
            slug="lina_combustion",
            innate=True,
            desc=[
                "Passive, levels up with Laguna Blade.",
                "Lina's fire damage stacks <b>Overheat</b> on enemies. When the target reaches the <b>175 damage threshold</b>, they combust and take additional Overheat damage.",
                "<b>Overheat Damage:</b> 15/35/55/75 (post-7.39).",
            ],
        ),
        new=dict(
            name="Slow Burn",
            innate=True,
            desc=[
                "Passive.",
                "Lina's abilities deal an <b>additional 64%</b> damage as <b>undispellable burn damage over 4s</b>.",
                "Applies on top of the spell's base damage and stacks duration on re-application.",
            ],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Dragon Slave"))
    W(ul_open())
    W(li("Damage decreased from 85/165/245/325 to 65/125/185/245", b([85, 165, 245, 325], [65, 125, 185, 245])))
    W(ul_close())
    W(ability("Light Strike Array"))
    W(ul_open())
    W(li("Damage decreased from 110/160/210/260 to 80/120/160/200", b([110, 160, 210, 260], [80, 120, 160, 200])))
    W(ul_close())
    W(ability("Laguna Blade"))
    W(ul_open())
    W(li("Damage decreased from 500/750/1000 to 380/565/750", b([500, 750, 1000], [380, 565, 750])))
    W(li("Aghanim's Shard reworked: Casting Laguna Blade temporarily supercharges Lina, granting her 12 stacks of Fiery Soul. Supercharge duration: 5s", t("REWORK")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Light Strike Array Damage decreased from +150 to +110", b(150, 110)))
    W(li("Level 25 Talent +150% Crit On Targets Affected By Spells replaced with 150% Attack Crit on Targets Affected by Slow Burn", t("REWORK")))
    W(li("Level 25 Talent +60% Combustion Overheat Damage replaced with +1s Slow Burn Duration", t("REWORK"),
         extra=inline_note("This increases additional damage from 64% to 80% — " + b(64, 80))))
    W(ul_close())

    # Lion
    W(hero_header("Lion"))
    W(ability_change(
        old=dict(
            name="To Hell and Back",
            innate=True,
            desc=[
                "Passive.",
                "Lion gains <b>20% debuff duration</b> and <b>20% spell amplification</b> for <b>90s</b> after respawning.",
                "Refreshes every time he dies and respawns.",
            ],
        ),
        new=dict(
            name="To Hell and Back",
            innate=True,
            desc=[
                "Passive. Reworked into a two-trigger buff:",
                "<b>Kill / assist trigger:</b> killing or assisting in a Hero kill grants Lion <b>20% debuff duration</b> against that hero <b>while it is dead</b>.",
                "<b>Respawn trigger:</b> whenever Lion respawns or resurrects, he gains <b>20% spell amplification</b> for <b>90s</b>, or until he gets a kill or an assist (whichever comes first).",
            ],
        ),
        summary="Innate reworked.",
        tag="rework",
    ))
    W(ability("Finger of Death"))
    W(ul_open())
    W(li("Cooldown decreased from 120/80/40s to 110/70/30s", b([120, 80, 40], [110, 70, 30], l=True)))
    W(li("Damage per kill decreased from 40 to 30", b(40, 30)))
    W(li("Now has empowered melee attacks after the cast by default", t("NEW")))
    W(li("After using Finger of Death, Lion's hand becomes empowered, turning him into a melee hero with 250 attack range and 30 bonus movement speed. These melee attacks have 25% cleave and deal 20/30/40 bonus damage which increases with each Finger of Death kill. Enemy heroes that die within 3s after getting hit with these melee attacks (or from them) also provide bonus per kill damage. Melee form duration: 20s",
         t("REWORK"),
         extra=inline_note("Ability can be toggled with right-click to disable the melee form."
                           "<br>Cleave area is a cone with 150 width that increases up to 350 at 650 distance.")))
    W(li("Aghanim's Scepter now also increases melee cleave from 25% to 50% and duration from 20s to 30s", t("NEW")))
    W(li("Aghanim's Scepter no longer decreases cooldown", t("DEL")))
    W(ul_close())

    # Lone Druid
    W(hero_header("Lone Druid"))
    W(ul_open())
    W(li("Attack projectile speed increased from 900 to 1125", b(900, 1125)))
    W(ul_close())

    # Luna
    W(hero_header("Luna"))
    W(ability("Lunar Blessing"))
    W(ul_open())
    W(li("Damage for Allies/Self changed from 1/2 + 1/2 per level up to 1/2 per level", t("MISC")))
    W(li_formula("Bonus Night Vision changed",
                 "250 + 25 per level up", "225 + 25 per level",
                 lambda L: 250.0 + 25.0 * L, lambda L: 225.0 + 25.0 * L,
                 effective_unchanged=True))
    W(ul_close())
    W(subnote("Effective values are not changed (formulas re-parametrized with a 1-level shift)"))
    W(ability("Lunar Orbit"))
    W(ul_open())
    W(li("Now applies 8/12/16/20% damage reduction while active", t("NEW")))
    W(li("Aghanim's Shard reworked: Increases damage reduction by 10% and provides Luna with 20% bonus movement speed for the duration", t("REWORK")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent -2s Lucent Beam Cooldown replaced with 1.5x Lunar Orbit Damage / Speed", t("REWORK")))
    W(li("Level 25 Talent Lunar Blessing Allied/Self Damage decreased from +30/60 to +25/50", b([30, 60], [25, 50])))
    W(ul_close())

    # Lycan
    W(hero_header("Lycan"))
    W(ability("Apex Predator"))
    W(ul_open())
    W(li_formula("Damage to neutrals changed",
                 "2% per level", "18% + 2% per level",
                 lambda L: 2.0 * L, lambda L: 18.0 + 2.0 * L))
    W(ul_close())
    W(ability("Summon Wolves"))
    W(ul_open())
    W(li("Aghanim's Shard reworked: Increases the number of wolves by 1 and grants them Hightail ability. Activate it to give them 100% evasion, 20 bonus attack speed, and hasted movement for 6s", t("REWORK")))
    W(ul_close())
    W(ability("Shapeshift"))
    W(ul_open())
    W(li("Now grants controlled units movement speed and critical strike bonuses", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent +2 Wolves Summoned replaced with -25% Summon Wolves BAT", t("REWORK"),
         extra=inline_note("Improves wolves' BAT from 1.2/1.1/1/0.9s to 0.9/0.825/0.75/0.675s — "
                           + b([1.2, 1.1, 1, 0.9], [0.9, 0.825, 0.75, 0.675], l=True))))
    W(ul_close())

    # Magnus
    W(hero_header("Magnus"))
    W(ul_open())
    W(li("Base Agility increased from 12 to 14", b(12, 14)))
    W(li("Damage at level 1 increased from 55–63 to 56–64", br(55, 63, 56, 64)))
    W(ul_close())
    W(ability("Solid Core"))
    W(ul_open())
    W(li("No longer levels with Reverse Polarity", t("REWORK")))
    W(li_formula("Slow Resistance rescaled",
                 "20/30/40/50%", "24% + 1% per level",
                 lambda L: 50.0, lambda L: 24.0 + 1.0 * L))
    W(ul_close())
    W(ability("Empower"))
    W(ul_open())
    W(li("Now always affects Magnus with 30% increased values and can't be cast on himself", t("NEW")))
    W(ul_close())
    W(ability("Skewer"))
    W(ul_open())
    W(li("Aghanim's Shard bonus distance increased from +275 to +300", b(275, 300)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent +10% Empower Damage/Cleave replaced with Shockwave Returns to Magnus", t("REWORK")))
    W(ul_close())

    # Marci
    W(hero_header("Marci"))
    _marci_cd_pill, _marci_cd_table = scale_pill(
        "245s − 5s per level",
        lambda L: 245.0 - 5.0 * L,
        value_fmt="{:.0f}s",
    )
    W(ability_change(
        old=dict(
            name="Special Delivery",
            slug="marci_special_delivery",
            innate=True,
            desc=[
                "Passive + Active.",
                "<b>Passive:</b> permanently increases the level of all allied couriers by <b>3</b> and hero attacks to kill the courier by <b>1</b> (so Marci's team starts with flying couriers).",
                "<b>Active:</b> Marci whistles and instantly teleports her courier to her location. <b>Cast Point:</b> 1s. <b>Cooldown:</b> 240s (flat).",
            ],
        ),
        new=dict(
            name="Special Delivery",
            slug="marci_special_delivery",
            innate=True,
            desc=[
                "Passive + Active.",
                "<b>Passive:</b> permanently increases the level of all allied couriers by <b>3</b> and hero attacks to kill the courier by <b>1</b> (so Marci's team starts with flying couriers).",
                "<b>Active:</b> Marci whistles and instantly teleports her courier to her location. Reworked delivery logic:",
                "If the courier is <b>in the fountain</b> when Special Delivery is cast, it <b>takes all items from the stash</b> before teleporting.",
                "The courier then <b>automatically attempts to transfer items</b> upon arrival, then heads back to the fountain.",
                "If the courier still has any extra items after the transfer attempt — or didn't transfer anything — it <b>stays next to Marci</b> instead of returning.",
                "<b>Cast Point:</b> 1s. <b>Cooldown:</b> " + _marci_cd_pill + " (was a flat 240s).",
            ],
            tables=[_marci_cd_table],
        ),
        summary="Innate reworked.",
        tag="rework",
    ))
    W(ability_change(
        old=dict(
            name="Bodyguard",
            slug="marci_bodyguard",
            desc=[
                "Active. Target an allied hero to become their bodyguard for <b>6s</b>.",
                "<b>Passive:</b> Marci gains <b>12/18/24/30% Lifesteal</b> and <b>+12/18/24/30% bonus base attack damage</b>. Health gained from lifesteal also heals the bodyguarded ally.",
                "<b>Active:</b> the bodyguarded ally receives <b>75%</b> of these bonuses. Whenever the ally attacks or is attacked by an enemy within Marci's attack range + <b>125</b>, Marci attacks that enemy.",
            ],
        ),
        new=dict(
            name="Bodyguard",
            slug="marci_bodyguard",
            desc=[
                "Now has both <b>passive</b> and <b>active</b> components.",
                "<b>Passive:</b> grants Marci <b>12/18/24/30%</b> lifesteal and <b>12/18/24/30%</b> bonus base attack damage.",
                "<b>Active:</b> cast on an ally — they receive <b>75%</b> of the passive bonuses and a <b>shared all-damage barrier</b> that blocks 90/160/230/300 damage. Damaging the barrier on either Marci or the target reduces it for both. As Marci attacks heroes, 30% of the damage dealt restores the barrier. <b>Duration: 7s.</b>",
                "<b>Cast Range:</b> 500. <b>Mana Cost:</b> 60/65/70/75. <b>Cooldown:</b> 20s. <b>Cast Point:</b> 0.2s.",
                "The effect is dispellable. Dispelling Marci removes the barrier; dispelling the target removes both the barrier and passive bonuses (lifesteal + base attack damage).",
            ],
        ),
        summary="Ability reworked.",
        tag="rework",
    ))
    W(ability("Rebound", slug="marci_companion_run"))
    W(ul_open())
    W(li("Ability can be set to alt-cast to bring the target ally to the destination. Does not work on rooted or leashed allies", t("MISC")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +10% Rebound Movement Speed Bonus replaced with +12% Bodyguard Damage", t("REWORK")))
    W(li("Level 20 Talent Unleash Movement Speed increased from +10% to +15%", b(10, 15)))
    W(li("Level 25 Talent +20% Bodyguard Damage replaced with Bodyguard Strong Dispels (Dispels both Marci and the target)", t("REWORK")))
    W(ul_close())

    # Mars
    W(hero_header("Mars"))
    W(ability("Dauntless"))
    W(ul_open())
    W(li("No longer considers Mars's allies when determining if Mars is outnumbered", t("DEL")))
    W(li("HP Regen per extra enemy decreased from 70% to 40%", b(70, 40)))
    W(ul_close())
    W(ability("Bulwark"))
    W(ul_open())
    W(li("Now a point targeted ability. Mars will face towards the targeted direction when toggled on", t("MISC")))
    W(li("No longer upgraded with Aghanim's Scepter", t("DEL")))
    W(ul_close())
    W(ability("Arena Of Blood"))
    W(ul_open())
    W(li("Aghanim's Scepter: Lowers cooldown by 10s and increases duration from 5.5s to 6.5s. If an enemy is killed in the Arena, Mars and all of his allies inside the Arena restore 35% of their max health and mana and get a 35% attack damage buff for 20s. This effect stacks", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +20% Dauntless Regen Per Enemy replaced with +1.5 Mana Regen", t("REWORK")))
    W(li("Level 20 Talent -16s Arena Of Blood Cooldown replaced with +70 Arena of Blood Spear Damage", t("REWORK")))
    W(ul_close())

    # Medusa
    W(hero_header("Medusa"))
    W(ability("Gorgon's Grasp", slug="medusa_gorgon_grasp"))
    W(ul_open())
    W(li("Cooldown decreased from 30/27/24/21s to 30/26/22/18s", b([30, 27, 24, 21], [30, 26, 22, 18], l=True)))
    W(li("Now always centers the cast cursor around the second grouping, even if the number of volleys is increased", t("MISC")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Stone Gaze Bonus Physical Damage increased from +10% to +12%", b(10, 12)))
    W(li("Level 15 Talent Mystic Snake Cooldown Reduction increased from 3s to 4s", b(3, 4, l=True)))
    W(li("Level 15 Talent +8% Split Shot Outgoing Damage replaced with +1 Gorgon's Grasp Volley", t("REWORK")))
    W(li("Level 20 Talent +1 Gorgon's Grasp Volley replaced with +12% Split Shot Outgoing Damage", t("REWORK")))
    W(li("Level 20 Talent +3 Mystic Snake Bounces replaced with +40% Mystic Snake Damage / Mana Gain", t("REWORK")))
    W(li("Level 25 Talent Stone Gaze Duration increased from +2s to +2.5s", b(2, 2.5)))
    W(ul_close())

    # Meepo
    W(hero_header("Meepo"))
    W(ul_open())
    W(li("Base Movement Speed decreased from 320 to 315", b(320, 315)))
    W(ul_close())
    W(ability_change(
        old=dict(
            name="Sticky Fingers",
            innate=True,
            desc=[
                "Passive.",
                "Meepo receives an additional choice when activating <b>neutral item tokens</b>.",
            ],
        ),
        new=dict(
            name="Geomancy",
            innate=True,
            desc=[
                "Passive.",
                "Each Meepo (main + clones) grants stacking bonuses to <b>all</b> Meepos based on the terrain it stands on:",
                "<b>Tree within 250 range</b> → +1 Health Regen.",
                "<b>On solid ground</b> → +2% bonus movement speed.",
                "<b>In water</b> → attacks slow the target by 2% for 2s.",
                '<div class="inline-note">Each Meepo can provide only one tree bonus regardless of how many trees are in range. '
                "If there's a tree in the water, that Meepo provides both the water and tree bonuses.</div>",
            ],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Ransack"))
    W(ul_open())
    W(li("Now pierces Debuff Immunity", t("NEW")))
    W(li("No longer has separate creep values. Follows global lifesteal rules instead", t("NERF"),
         extra=inline_note("Has a 40% penalty against creeps — " + b(100, 60))))
    W(ul_close())
    W(ability_change(
        old=dict(
            name="Divided We Stand",
            slug="meepo_divided_we_stand",
            desc=[
                "Ultimate. Passive — at the ult's level-up points, Meepo gains an additional clone.",
                "<b>Max Level:</b> 3 (levels at 4 / 11 / 18).",
                "Passively grants Meepo and all clones bonus <b>Magic Resistance</b>.",
                "Each clone is a separate hero unit but does not copy items.",
            ],
        ),
        new=dict(
            name="Divided We Stand",
            slug="meepo_divided_we_stand",
            desc=[
                "Ultimate. Reworked — adds a 4th level and item sharing:",
                "<b>Max Level:</b> 4 (levels at <b>3 / 10 / 17 / 24</b>).",
                "Each duplicate now <b>copies all of Meepo's items</b>, but they <b>share their cooldowns</b>.",
                "Damage, attack speed, health / mana regeneration, mana burn, and proc-chance bonuses from items are <b>distributed equally</b> across all Meepos — a 50% / 66.6% / 75% / 80% penalty per Meepo at each level.",
                "Clones can't use consumable shared items on the main Meepo.",
                "<b>No longer</b> passively grants Magic Resistance.",
            ],
        ),
        summary="Ability reworked.",
        tag="rework",
    ))
    W(ul_open())
    W(li("Max Level increased from 3 to 4", t("REWORK")))
    W(li("Level requirement rescaled from 4/11/18 to 3/10/17/24", t("REWORK")))
    W(li("Meepo gains 100% of the experience from Hero Kills or Assists as long as at least one Meepo is in range", t("REWORK"),
         extra=inline_note("Multiple Meepos within experience range does not increase the amount gained")))
    W(li("All other experience gained by any Meepo is divided by the number of Meepos", t("REWORK"),
         extra=inline_note("Each Meepo gains experience independently")))
    W(li("No longer has a penalty for Strength, Agility, or Intelligence gained from items", t("BUFF")))
    W(li("Clones can't use consumable shared items on the main Meepo", t("NERF")))
    W(li("Clones no longer gain 30% experience independently", t("DEL")))
    W(li("No longer passively grants Magic Resistance", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Health increased from +350 to +400", b(350, 400)))
    W(ul_close())

    # Mirana
    W(hero_header("Mirana"))
    _mira_pill, _mira_table = scale_pill(
        "3 per level",
        lambda L: 3.0 * L,
        value_fmt="{:.0f}",
    )
    W(ability_change(
        old=dict(
            name="Selemene's Faithful",
            innate=True,
            desc=[
                "Passive.",
                "Healing Lotuses are <b>20% more effective</b> on Mirana and her allies — both Lotus pickups and the AoE pulse hand out a larger heal when Mirana is involved.",
            ],
        ),
        new=dict(
            name="Celestial Quiver",
            slug="mirana_celestial_quiver",
            innate=True,
            desc=[
                "Auto-cast attack modifier.",
                "Mirana consumes a charge to empower her next attack with bonus magic damage equal to " + _mira_pill + ".",
                "Starts with <b>2 max charges</b> and gains <b>+1 max charge every 7 levels</b>. <b>Base Charge Restore Time:</b> 6s.",
                aghs_shard_line("Casting Leap provides 3 temporary charges for the duration of the buff. These temporary charges ignore the max-charges cap and stack from each Leap cast."),
            ],
            tables=[_mira_table],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ul_open())
    W(li("Upgraded with Aghanim's Shard", t("NEW")))
    W(ul_close())
    W(ability("Leap"))
    W(ul_open())
    W(li("Aghanim's Shard no longer provides crits during the buff", t("DEL")))
    W(ul_close())
    W(subnote("Still increases max charges by 1"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent +35 Base Damage replaced with +35 Celestial Quiver Damage", t("REWORK")))
    W(ul_close())

    # Monkey King
    W(hero_header("Monkey King"))
    W(ability("Mischief"))
    W(ul_open())
    W(li("No longer levels with Wukong's Command", t("REWORK")))
    W(li_formula("Cooldown changed",
                 "24/20/16/12s", "24.5s - 0.5s per level",
                 lambda L: 12.0, lambda L: 24.5 - 0.5 * L, l=True))
    W(ul_close())
    W(ability("Tree Dance"))
    W(ul_open())
    W(li("Cast point increased from 0.1s to 0.2s", b(0.1, 0.2, l=True)))
    W(li("Cast Range / Perched Tree Cast Range increased from 800 to 900", b(800, 900)))
    W(li("Cooldown decreased from 1.4/1.2/1.0/0.8s to 0.9/0.6/0.3/0s", b([1.4, 1.2, 1.0, 0.8], [0.9, 0.6, 0.3, 0], l=True)))
    W(li("Leap speed decreased from 700 to 600", b(700, 600)))
    W(li("Leaping between trees can now be interrupted by Roots and Leashes", t("MISC"),
         extra=inline_note("Previously it was only interrupted by Stunned, Hidden, or Hexed statuses")))
    W(ul_close())
    W(ability("Wukong's Command"))
    W(ul_open())
    W(li("Now has Changing of the Guard sub-ability by default", t("NEW"),
         extra=inline_note("While Wukong's Command is active, Monkey King gains a Changing of the Guard ability which allows him to transform into any one of his soldiers. Upon cast, Monkey King takes the place of the soldier closest to the target location for 1.5s, and leaves another one in his stead. While Transfigured, Monkey King is indistinguishable from other soldiers and invulnerable, but can't issue commands. Cast Point: 0.3s. No Mana Cost. Cooldown: 3s")))
    W(ul_close())
    W(ability("Changing of the Guard", slug="monkey_king_transfiguration"))
    W(ul_open())
    W(li("Ability appears in place of Wukong's Command and starts on a 1s cooldown after casting Wukong's Command. Can't be cast while rooted and can't target soldiers created by Aghanim's Scepter effect. Monkey King disjoints projectiles upon transformation.", t("MISC"),
         extra=inline_note("The possessed soldier has a small ring around it which is visible only to Monkey King and his allies. When the effect is over, Monkey King becomes his usual self leaving the overtaken soldier's position empty.")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +90 Primal Spring Max Damage replaced with +350 Tree Dance Cast Range", t("REWORK")))
    W(li("Level 15 Talent +450 Tree Dance Cast Range replaced with 0 Cooldown Primal Spring", t("REWORK")))
    W(li("Level 20 Talent 0 Cooldown Primal Spring replaced with Jingu Mastery Undispellable", t("REWORK")))
    W(ul_close())

    # Morphling
    W(hero_header("Morphling"))
    W(ul_open())
    W(li("Hero model size now scales on his Agility/Strength ratio", t("MISC")))
    W(ul_close())
    W(ability_change(
        old=dict(
            name="Accumulation",
            innate=True,
            desc=[
                "Passive.",
                "Morphling receives <b>50% of Attribute gain bonuses every half level</b> instead of full bonuses at level up.",
                "Also increases <b>All Attributes bonus gained for skill points in the Talent Tree from +2 to +4</b>.",
            ],
        ),
        new=dict(
            name="Ebb and Flow",
            slug="morphling_ebb_and_flow",
            innate=True,
            desc=[
                "Passive.",
                "Strength and Agility now provide Morphling with additional bonuses (also active while replicating, except the extra attack range, which only applies when replicating a ranged unit):",
                "<b>Strength to Cast Range:</b> 20%. <b>Strength to Slow Resistance:</b> 20%.",
                "<b>Agility to Movement Speed:</b> 15%. <b>Agility to Ranged Attack Range:</b> 20%.",
            ],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Waveform"))
    W(ul_open())
    W(li("Cast Range decreased from 700/800/900/1000 to 700/775/850/925", b([700, 800, 900, 1000], [700, 775, 850, 925])))
    W(ul_close())
    W(ability("Adaptive Strike", slug="morphling_adaptive_strike_agi"))
    W(ul_open())
    W(li("Base Damage increased from 25/50/75/100 to 50/70/90/110", b([25, 50, 75, 100], [50, 70, 90, 110])))
    W(ul_close())

    # Muerta
    W(hero_header("Muerta"))
    W(ability_change(
        old=dict(
            name="Supernatural",
            slug="muerta_supernatural",
            innate=True,
            desc=[
                "Passive.",
                "Muerta is permanently endowed with <b>passive ethereal bonuses</b>: she can always attack ethereal targets and can be attacked while ethereal herself.",
                "While either she or her target is ethereal, her attack damage converts to magical and her physical lifesteal is treated as spell lifesteal.",
            ],
        ),
        new=dict(
            name="Supernatural",
            slug="muerta_supernatural",
            innate=True,
            desc=[
                "Passive. Reworked into a hero-kill-driven stacking buff:",
                "Whenever an <b>enemy hero dies within 925 units</b> of Muerta, she gains a stack of <b>1% spell amplification</b>. Max stacks equal her current hero level.",
                "When Muerta dies she <b>loses half the stacks</b>, rounded down.",
                "Passive ethereal bonuses moved to <b>Pierce the Veil</b>.",
            ],
        ),
        summary="Innate reworked.",
        tag="rework",
    ))
    W(ability_change(
        old=dict(
            name="Pierce the Veil",
            slug="muerta_pierce_the_veil",
            desc=[
                "Active ultimate. <b>Duration:</b> 8s.",
                "Muerta's attacks deal <b>magical damage</b> instead of physical and gain <b>+70/100/130 bonus attack damage</b>.",
                "Grants <b>30% Spell Lifesteal</b> for the duration.",
                aghs_shard_line("Muerta permanently gains <b>+2% Spell Amplification</b> whenever she kills an enemy hero during Pierce the Veil, or any enemy hero dies within 925 units of her. Applies retroactively."),
            ],
        ),
        new=dict(
            name="Pierce the Veil",
            slug="muerta_pierce_the_veil",
            desc=[
                "Now has both <b>passive</b> and <b>active</b> components.",
                "<b>Passive:</b> Muerta can always attack ethereal targets and can attack while ethereal herself. When either she or her target is ethereal, her attack damage is dealt as <b>magical</b>, and her physical lifesteal is treated as <b>spell lifesteal</b>. "
                + inline_note("Lifesteal conversion happens only for attacks — it does not affect her spells."),
                "<b>Active:</b> grants <b>+75% base damage</b> and <b>30% Spell Lifesteal</b>. <b>Duration:</b> 8s.",
            ],
        ),
        summary="Ability reworked.",
        tag="rework",
    ))
    W(ul_open())
    W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
    W(ul_close())
    W(ability("Spectral Slug"))
    W(ul_open())
    W(li("Aghanim's Shard: New ability — Muerta shoots a spectral bullet at an enemy, dealing damage, knocking them back, and turning them ethereal for 3s, rendering them immune to physical damage and unable to attack. The target is slowed and becomes 20% more vulnerable to magic damage",
         t("NEW"),
         extra=inline_note("Range: 500. Mana Cost: 75. Cooldown: 12s. Damage: 225. Slow: 30%. Knockback Distance: 250")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +55 Gunslinger Damage replaced with +15 Intelligence", t("REWORK")))
    W(ul_close())

    # Naga Siren
    W(hero_header("Naga Siren"))
    W(ability("Eelskin"))
    W(ul_open())
    W(li("Now provides evasion for Naga Siren on her own", t("NEW")))
    W(li_formula("Evasion per Naga changed",
                 "8%", "4.9% + 0.1% per level",
                 lambda L: 8.0, lambda L: 4.9 + 0.1 * L))
    W(ul_close())
    W(ability("Rip Tide"))
    W(ul_open())
    W(li("Now always a basic ability for Naga Siren", t("REWORK")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Reel In Pull Speed increased from +100 to +125", b(100, 125)))
    W(li("Level 15 Talent Mirror Image Illusion Damage Taken Reduction increased from 50% to 75%", b(50, 75)))
    W(li("Level 20 Talent Song of the Siren Cooldown Reduction increased from 20s to 25s", b(20, 25, l=True)))
    W(ul_close())

    # Nature's Prophet
    W(hero_header("Nature's Prophet"))
    W(ul_open())
    W(li("Minimum Base damage increased by 4", bstat_h("Nature's Prophet", "AttackDamageMin", "7.40c", 4), extra=note_box(hero="Nature's Prophet", field="AttackDamageMin", before_patch="7.40c")))
    W(li("Damage spread decreased from 10 to 6", b(10, 6)))
    W(li("Damage at level 1 increased from 40–50 to 44–50", br(40, 50, 44, 50)))
    W(ul_close())
    W(ability("Spirit of the Forest"))
    W(ul_open())
    W(li("No longer levels with Wrath of Nature", t("REWORK")))
    W(li_formula("Tree Radius rescaled",
                 "300/400/500/600", "300 + 10 per level",
                 lambda L: 600.0, lambda L: 300.0 + 10.0 * L))
    W(li("Multiplier per treant increased from 1x to 2x", b(1, 2)))
    W(li("Treants also have Spirit of the Forest and gain bonus damage for each nearby tree and treant", t("NEW")))
    W(ul_close())
    W(ability("Sprout"))
    W(ul_open())
    W(li("Vision increased from 250 to 400", b(250, 400)))
    W(ul_close())
    W(ability("Nature's Call", slug="furion_force_of_nature"))
    W(ul_open())
    W(li("Treant Movespeed rescaled from 305/310/315/320 to 300/315/330/345", b([305, 310, 315, 320], [300, 315, 330, 345])))
    W(li("Treant Health decreased from 550 to 450", b(550, 450)))
    W(li("Treants now have 25% Magic Resistance", t("NEW")))
    W(li("Treants now deal 4/8/12/16 bonus damage to enemy Heroes", t("NEW"),
         extra=inline_note("This bonus is also affected by the Treant Damage multiplying talent")))
    W(li("Treants now have free pathing through trees", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent changed from facet specific to +100 Teleportation Barrier", t("MISC")))
    W(li("Level 25 Talent 3x Treant HP/Damage no longer affects Spirit of the Forest Multiplier", t("NERF")))
    W(ul_close())

    # Necrophos
    W(hero_header("Necrophos"))
    W(ability("Sadist"))
    W(ul_open())
    W(li("No longer levels with Reaper's Scythe", t("REWORK")))
    W(li_formula("Health and Mana regen rescaled",
                 "3.5/5/6.5/8", "3.7 + 0.3 per level",
                 lambda L: 8.0, lambda L: 3.7 + 0.3 * L))
    W(ul_close())
    W(ability("Ghost Shroud"))
    W(ul_open())
    W(li("Restoration Amplification increased from 55/60/65/70% to 55/65/75/85%", b([55, 60, 65, 70], [55, 65, 75, 85])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent +15% Ghost Shroud Self Restoration Amp replaced with +75 Spell AoE", t("REWORK")))
    W(li("Level 25 Talent +0.5% Heartstopper Aura Damage replaced with +0.3 Reaper's Scythe Damage Per Missing HP", t("REWORK")))
    W(ul_close())

    # Night Stalker
    W(hero_header("Night Stalker"))
    _ns_ms_pill, _ns_ms_table = scale_pill(
        "24% + 2% per 3 levels",
        lambda L: 24.0 + 2.0 * (L // 3),
        value_fmt="{:.0f}%",
    )
    _ns_as_pill, _ns_as_table = scale_pill(
        "38 + 2 per level",
        lambda L: 38.0 + 2.0 * L,
        value_fmt="{:.0f}",
    )
    W(ability_change(
        old=dict(
            name="Heart of Darkness",
            innate=True,
            desc=[
                "Passive.",
                "At night, Night Stalker's Health Regen is <b>increased by 40%</b>, but during the day it is <b>decreased by 20%</b>.",
            ],
        ),
        new=dict(
            name="Hunter in the Night",
            slug="night_stalker_hunter_in_the_night",
            innate=True,
            desc=[
                "Passive. Activates only at night.",
                "<b>Bonus Move Speed:</b> " + _ns_ms_pill + ".",
                "<b>Bonus Attack Speed:</b> " + _ns_as_pill + ".",
                aghs_line("Increases bonus Movement Speed by 15% and bonus Attack Speed by 50. Killing an enemy hero resets cooldowns of all basic abilities."),
            ],
            tables=[_ns_ms_table, _ns_as_table],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ul_open())
    W(li_formula("Move Speed bonus changed",
                 "22/28/34/40%", "24% + 2% per 3 levels",
                 lambda L: 40.0, lambda L: 24.0 + 2.0 * (L // 3)))
    W(li_formula("Attack Speed bonus changed",
                 "20/40/60/80", "38 + 2 per level",
                 lambda L: 80.0, lambda L: 38.0 + 2.0 * L))
    W(li("Aghanim's Scepter: Increases bonus Movement Speed by 15% and bonus Attack Speed by 50. Killing an enemy hero resets cooldowns of all basic abilities", t("NEW")))
    W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
    W(ul_close())
    W(ability("Void"))
    W(ul_open())
    W(li("Aghanim's Shard: Now affects all units within 400 radius around the target", t("NEW")))
    W(ul_close())
    W(ability("Crippling Fear"))
    W(ul_open())
    W(li("No longer upgraded with Aghanim's Scepter", t("DEL")))
    W(ul_close())
    W(ability("Midnight Feast"))
    W(ul_open())
    W(li("New basic ability with both passive and active components — passively, Night Stalker heals himself <b>6/8/10/12 health</b> when attacking enemy units. Actively at night, eats a non-ancient creep to restore <b>10/15/20/25% max health</b> and <b>10/12/14/16% mana</b>. <b>Cast Range:</b> 125. <b>No Mana Cost.</b> <b>Cooldown:</b> 39/36/33/30s",
         t("NEW"),
         extra=inline_note("Attacks on allied units and buildings will not heal Night Stalker."
                           "<br>Can't be cast on allies.")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +5s Dark Ascension Duration replaced with +10 Crippling Fear DPS", t("REWORK")))
    W(li("Level 20 Talent +40 Crippling Fear DPS replaced with +75 Crippling Fear Radius", t("REWORK")))
    W(li("Level 25 Talent +100 Hunter in the Night Attack Speed replaced with +100 Midnight Feast Lifesteal", t("REWORK")))
    W(ul_close())

    # Nyx Assassin
    W(hero_header("Nyx Assassin"))
    W(ability_change(
        old=dict(
            name="Nyxth Sense",
            innate=True,
            desc=[
                "Passive.",
                "Nyx Assassin can <b>sense invisible heroes</b> in a <b>400 radius</b> around himself.",
            ],
        ),
        new=dict(
            name="Mana Burn",
            slug="nyx_assassin_neuro_sting",
            innate=True,
            desc=[
                "Passive.",
                "When Nyx Assassin deals damage with attacks or his abilities, he burns the affected unit's mana equal to <b>12% of damage dealt</b>.",
                "Damage reflected with Spiked Carapace also counts.",
            ],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Mind Flare", slug="nyx_assassin_jolt"))
    W(ul_open())
    W(li("Now burns 9/12/15/18% of the target's Max Mana", t("NEW")))
    W(ul_close())
    W(ability("Vendetta"))
    W(ul_open())
    W(li("Now also applies a 4s Break on hit", t("NEW")))
    W(li("Aghanim's Shard reworked: Decreases cooldown by 10s. For the first 15s, Nyx Assassin is hasted and has unobstructed pathing", t("REWORK")))
    W(ul_close())

    # Ogre Magi
    W(hero_header("Ogre Magi"))
    W(ability("Fireblast"))
    W(ul_open())
    W(li("Aghanim's Scepter: Now also upgrades Fireblast — becomes Refined Fireblast, reducing its cooldown by 1s and increasing its cast speed by 25%", t("NEW")))
    W(ul_close())
    W(ability("Multicast"))
    W(ul_open())
    W(li("Each point of Strength increases chances of Multicast by 0.0625%, so every 16 Strength points add 1%", t("NEW")))
    W(ul_close())
    W(ability("Unrefined Fireblast"))
    W(ul_open())
    W(li("Cooldown increased from 6s to 7s", b(6, 7, l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent -1s Fireblast Cooldown replaced with +2/0.01 Dumb Luck Mana / Mana Regen Per Strength", t("REWORK")))
    W(li("Level 10 Talent Ignite Burn Damage decreased from +12 to +10", b(12, 10)))
    W(li("Level 15 Talent +2/0.01 Dumb Luck Mana / Mana Regen Per Strength replaced with +20/35 Bloodlust / Self Attack Speed", t("REWORK")))
    W(li("Level 20 Talent +35 Bloodlust Attack Speed replaced with +175 Fireblast Damage", t("REWORK")))
    W(li("Level 25 Talent +220 Fireblast Damage replaced with +10% Multicast Chances (affects all types of multicast)", t("REWORK")))
    W(ul_close())

    # Omniknight
    W(hero_header("Omniknight"))
    W(ul_open())
    W(li("Base Armor decreased by 1", bstat_h("Omniknight", "ArmorPhysical", "7.40c", -1), extra=note_box(hero="Omniknight", field="ArmorPhysical", before_patch="7.40c")))
    W(li("Agility gain decreased from 2.0 to 1.7", b(2.0, 1.7)))
    W(ul_close())
    W(ability("Degen Aura"))
    W(ul_open())
    W(li("No longer levels with Guardian Angel", t("REWORK")))
    W(li_formula("Movement Slow changed",
                 "10/20/30/40%", "11% + 1% per level",
                 lambda L: 40.0, lambda L: 11.0 + 1.0 * L))
    W(ul_close())
    W(ability("Purification"))
    W(ul_open())
    W(li("Now pierces Debuff Immunity on enemies (previously only pierced Debuff Immunity on allies)", t("NEW")))
    W(ul_close())
    W(ability("Repel", slug="omniknight_martyr"))
    W(ul_open())
    W(li("Cooldown decreased from 50/45/40/35s to 40/36/32/28s", b([50, 45, 40, 35], [40, 36, 32, 28], l=True)))
    W(li("No longer provides bonus Strength", t("DEL")))
    W(li("No longer provides bonus Strength / HP Regen per Debuff", t("DEL"),
         extra=inline_note("As a result, provides only Debuff Immunity with 60% magic resistance, and 8/12/16/20 bonus health regen. Has no effects per dispelled debuffs")))
    W(ul_close())
    W(ability("Hammer of Purity"))
    W(ul_open())
    W(li("Now pierces Debuff Immunity", t("NEW")))
    W(li("Cooldown decreased from 20/15/10/5s to 13/10/7/4s", b([20, 15, 10, 5], [13, 10, 7, 4], l=True)))
    W(li("Bonus Base Damage decreased from 55/70/85/100% to 30/50/70/90%", b([55, 70, 85, 100], [30, 50, 70, 90])))
    W(li("Damage decreased from 25/50/75/100 to 20/40/60/80", b([25, 50, 75, 100], [20, 40, 60, 80])))
    W(li("Now heals Omniknight for 30% of the damage dealt over the next 5s", t("NEW")))
    W(ul_close())
    W(ability("Guardian Angel"))
    W(ul_open())
    W(li("Now is a no-target ability. The effect is applied in an aura centered around Omniknight that follows him", t("REWORK"),
         extra=inline_note("Has no linger duration")))
    W(li("Duration decreased from 5/6/7s to 4/4.5/5s", b([5, 6, 7], [4, 4.5, 5])))
    W(li("Radius increased from 400 to 700", b(400, 700)))
    W(li("Aghanim's Scepter reworked: Becomes global, affects buildings, and amplifies health restoration by 100%", t("REWORK")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Base Damage decreased from +35 to +30", b(35, 30)))
    W(li("Level 10 Talent +1s Repel Duration replaced with +200 Repel Cast Range", t("REWORK")))
    W(li("Level 15 Talent +5 Repel Strength/HP Regen Per Debuff replaced with -0.5s Hammer of Purity Cooldown", t("REWORK")))
    W(li("Level 20 Talent +2s Guardian Angel Duration replaced with +125 Degen Aura radius", t("REWORK")))
    W(ul_close())

    # Oracle
    W(hero_header("Oracle"))
    W(ability("Prognosticate"))
    W(ul_open())
    W(li("Oracle now also predicts Roshan's exact respawn timer", t("NEW")))
    W(ul_close())
    W(ability("False Promise"))
    W(ul_open())
    W(li("No longer upgraded with Aghanim's Scepter", t("DEL")))
    W(ul_close())
    def _tarot(slug, name, effect):
        return (f'<span class="tarot-card"><img src="../icons/abilities/oracle_diviners_deck_{slug}.png" '
                f'alt="" class="tarot-card-icon"><b>{name}:</b> {effect}</span>')

    W(ability("Diviner's Deck"))
    W(ul_open())
    W(li("Aghanim's Scepter: New passive ability — Oracle receives a Tarot Card Buff now and every 90 seconds. The buff is undispellable and lasts until the next one replaces it. Oracle always knows which buff will be next.",
         t("NEW"),
         extra=inline_note(
             _tarot("death",     "Death",      "+40% Spell Amplification") + "<br>"
             + _tarot("the_fool",   "The Fool",   "+100% Gold Gain") + "<br>"
             + _tarot("the_world",  "The World",  "+150% Intelligence") + "<br>"
             + _tarot("the_lovers", "The Lovers", "+40% Heal Amplification") + "<br>"
             + _tarot("the_tower",  "The Tower",  "Gain a 400 all-damage barrier which regenerates after not taking damage for 7s"))))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Fortune's End Heals/Damages for 80 Per Effect Dispelled replaced with +100 Fortune's End Radius", t("REWORK")))
    W(ul_close())

    # Outworld Destroyer
    W(hero_header("Outworld Destroyer"))
    W(ul_open())
    W(li("Base Agility decreased from 22 to 17", b(22, 17)))
    W(li("Base Armor decreased by 1", bstat_h("Outworld Destroyer", "ArmorPhysical", "7.40c", -1), extra=note_box(hero="Outworld Destroyer", field="ArmorPhysical", before_patch="7.40c")))
    W(ul_close())
    W(ability_change(
        old=dict(
            name="Ominous Discernment",
            innate=True,
            desc=[
                "Passive.",
                "Outworld Destroyer gains <b>2 extra mana per point of Intelligence</b>.",
            ],
        ),
        new=dict(
            name="Essence Flux",
            slug="obsidian_destroyer_equilibrium",
            innate=True,
            desc=[
                "Passive. Max Mana Restore now depends on the ability it procced on:",
                "<b>Regular abilities:</b> Max Mana Restoration is <b>40% + 5% per 5 levels</b>.",
                "<b>Attack modifiers that spend mana:</b> Max Mana Restoration is <b>25% + 5% per 5 levels</b>.",
            ],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ul_open())
    W(li_formula("For regular abilities Max Mana Restoration changed",
                 "25/35/45/55%", "40% + 5% per 5 levels",
                 lambda L: 55.0, lambda L: 40.0 + 5.0 * (L // 5),
                 levels=[1, 5, 10, 15, 20, 25, 30]))
    W(li_formula("For attack modifiers that spend mana Max Mana Restoration changed",
                 "25/35/45/55%", "25% + 5% per 5 levels",
                 lambda L: 55.0, lambda L: 25.0 + 5.0 * (L // 5),
                 levels=[1, 5, 10, 15, 20, 25, 30]))
    W(ul_close())
    W(ability("Objurgation"))
    W(ul_open())
    W(li("New basic ability with both passive and active components — passively, increases max mana by <b>80/160/240/320</b>. Active: creates an all-damage barrier equal to <b>120/180/240/300 + 12% of Outworld Destroyer's max mana</b>. <b>Duration:</b> 10s. <b>Mana Cost:</b> 250. <b>Cooldown:</b> 36/34/32/30s.",
         t("NEW"),
         extra=inline_note("Barrier can be dispelled. Multiple instances of Objurgation barrier stack.")))
    W(li("Aghanim's Scepter: Increases Max Mana to Barrier by 4%. Damage that would bring Outworld Destroyer below 20% is prevented, triggering a strong dispel and an automatic instance of undispellable Objurgation. This effect cannot trigger more than once every 80s, but refreshes on death", t("NEW")))
    W(ul_close())
    W(ability("Sanity's Eclipse", slug="obsidian_destroyer_sanity_eclipse"))
    W(ul_open())
    W(li("Cooldown decreased from 150/135/120s to 140/130/120s", b([150, 135, 120], [140, 130, 120], l=True)))
    W(li("Radius decreased from 450/525/600 to 450/500/550", b([450, 525, 600], [450, 500, 550])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +8% Astral Imprisonment Mana Capacity Steal replaced with +5% Essence Flux Mana Restored", t("REWORK")))
    W(li("Level 20 Talent +0.15 Sanity's Eclipse Mana Difference Multiplier replaced with +10% Astral Imprisonment Mana Capacity Steal", t("REWORK")))
    W(li("Level 20 Talent +450 Health replaced with -10s Objurgation Cooldown", t("REWORK")))
    W(ul_close())

    # Pangolier
    W(hero_header("Pangolier"))
    W(ability("Swashbuckle"))
    W(ul_open())
    W(li("Slow Duration increased from 0.4s to 0.6s", b(0.4, 0.6)))
    W(ul_close())
    W(ability("Shield Crash"))
    W(ul_open())
    W(li("Damage increased from 50/100/150/200 to 60/120/180/240", b([50, 100, 150, 200], [60, 120, 180, 240])))
    W(ul_close())
    W(ability("Lucky Shot"))
    W(ul_open())
    W(li("Armor Reduction decreased from 3/5/7/9 to 2/4/6/8", b([3, 5, 7, 9], [2, 4, 6, 8])))
    W(ul_close())
    W(ability("Rolling Thunder", slug="pangolier_gyroshell"))
    W(ul_open())
    W(li("Stun Duration increased from 0.8/1/1.2s to 1.2s", b([0.8, 1, 1.2], 1.2),
         extra=note_box("Doubles as a soft nerf at lower ranks: a target can't be hit by another Rolling Thunder stun until the previous one expires, so a longer stun also means a longer immune window between procs.")))
    W(ul_close())

    # Phantom Assassin
    W(hero_header("Phantom Assassin"))
    W(ability("Blur"))
    W(ul_open())
    W(li("No longer levels with Coup de Grace", t("REWORK")))
    W(li("Vanish Radius rescaled from 625/550/475/400 to 500", b([625, 550, 475, 400], 500)))
    W(li("Vanish Buffer rescaled from 0.4/0.6/0.8/1s to 0.8s", b([0.4, 0.6, 0.8, 1], 0.8)))
    W(li_formula("Active Movement Speed changed",
                 "6/9/12/15%", "9.5% + 0.5% per level",
                 lambda L: 15.0, lambda L: 9.5 + 0.5 * L))
    W(ul_close())

    # Phantom Lancer
    W(hero_header("Phantom Lancer"))
    W(ability("Illusory Armaments"))
    W(ul_open())
    W(li_formula("Min Damage increase changed",
                 "2% per 3 level ups", "2% per 3 levels",
                 lambda L: 2.0 * ((L - 1) // 3), lambda L: 2.0 * (L // 3),
                 levels=[1, 3, 4, 6, 7, 9, 12, 15, 18, 21, 24, 27, 30],
                 value_fmt="{:.0f}%"))
    W(ul_close())
    W(subnote("Bonus damage increases 1 level earlier (on levels 3/6/9... instead of 4/7/10...) and Phantom Lancer gains one more damage increase at level 30"))

    # Phoenix
    W(hero_header("Phoenix"))
    W(ability_change(
        old=dict(
            name="Blinding Sun",
            innate=True,
            desc=[
                "Passive.",
                "Debuffs from Icarus Dive, Fire Spirits, Sun Ray, and Supernova apply a stackable <b>2% miss chance per second</b>. Lasts <b>5 seconds</b>. Applying a new stack refreshes the duration.",
            ],
        ),
        new=dict(
            name="Dying Light",
            slug="phoenix_dying_light",
            innate=True,
            desc=[
                "Passive.",
                "Phoenix deals <b>4% of its missing health</b> as magic damage to all enemies in a <b>400 radius</b> every second. Damage tick rate: 0.2s.",
                "The effect is also present <b>during Supernova</b> — damage is calculated as if Phoenix was still present with the same health and health regen it had at the moment of the cast.",
            ],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +0.5% Blinding Sun Miss Chance replaced with +1% Dying Light Missing Health as Damage", t("REWORK")))
    W(ul_close())

    # Primal Beast
    W(hero_header("Primal Beast"))
    W(ability_change(
        old=dict(
            name="Colossal",
            slug="primal_beast_colossal",
            innate=True,
            desc=[
                "Passive.",
                "Due to his size, Primal Beast does 40% bonus damage to buildings.",
            ],
        ),
        new=dict(
            name="Colossal",
            slug="primal_beast_colossal",
            innate=True,
            desc=[
                "Passive, scales with Max Health.",
                "Has 10% base Slow Resistance.",
                "Gains +0.5% Area of Effect and +1% Slow Resistance per 100 Max Health.",
            ],
        ),
        summary="Innate reworked.",
        tag="rework",
    ))
    W(ability("Pulverize"))
    W(ul_open())
    W(li("AoE Radius decreased from 600 to 575", b(600, 575)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Cannot Be Slowed Or Rooted During Trample replaced with Colossal 2x Bonuses During Trample", t("REWORK")))
    W(ul_close())

    # Puck
    W(hero_header("Puck"))
    W(ability("Puckish"))
    W(ul_open())
    W(li("Health/Mana Restore rescaled from 10 + 2% to 3%", t("REWORK")))
    W(ul_close())
    W(subnote("Also unified into a single value"))
    W(ul_open())
    W(li("Spell Dodge Multiplier decreased from 3.5x to 3x", b(3.5, 3)))
    W(ul_close())
    W(ability("Illusory Orb"))
    W(ul_open())
    W(li("Speed increased from 550 to 750", b(550, 750)))
    W(li("Now additionally deals 3% of orb's Impact Damage every 0.5s in its AoE", t("NEW")))
    W(li("Now has curved vector targeting by default", t("MISC"),
         extra=inline_note("Can be put on alt-cast to launch the orb straight.")))
    W(ul_close())

    # Pudge
    W(hero_header("Pudge"))
    W(ability("Meat Shield", slug="pudge_flesh_heap"))
    W(ul_open())
    W(li("Permanent Bonus Strength rescaled from 1.1/1.4/1.7/2.0 to 1.6", b([1.1, 1.4, 1.7, 2.0], 1.6)))
    W(li("No longer levels with Dismember", t("REWORK")))
    W(ul_close())
    W(ability("Rot"))
    W(ul_open())
    W(li("No longer has a separate value for incoming heal reduction", t("MISC"),
         extra=inline_note("Still reduces incoming heals due to Health Restoration changes")))
    W(ul_close())

    # Pugna
    W(hero_header("Pugna"))
    W(ul_open())
    W(li("Base Movement Speed decreased from 330 to 325", b(330, 325)))
    W(ul_close())
    W(ability("Oblivion Savant"))
    W(ul_open())
    W(li("Now also increases Pugna's Spell Amplification by 1.5% per destroyed tower", t("NEW")))
    W(ul_close())
    W(ability("Nether Ward"))
    W(ul_open())
    W(li("Damage source changed from Nether Ward to the caster", t("REWORK")))
    W(ul_close())

    # Queen of Pain
    W(hero_header("Queen of Pain"))
    W(ability("Scream Of Pain"))
    W(ul_open())
    W(li("Damage increased from 75/150/225/300 to 90/175/260/345", b([75, 150, 225, 300], [90, 175, 260, 345])))
    W(li("25% of the damage dealt to heroes with this ability is reflected back to her", t("NEW")))
    W(ul_close())
    W(subnote("Does not trigger on damage to illusions. Damage done is nonlethal reflection damage"))
    W(ul_open())
    W(li("Also applies to Scream of Pain instances cast by Shadow Strike upgraded with Aghanim's Scepter", t("MISC")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Scream of Pain Damage increased from +100 to +115", b(100, 115)))
    W(ul_close())

    # Razor
    W(hero_header("Razor"))
    W(ability("Static Link"))
    W(ul_open())
    W(li("Damage Drain Rate increased from 5/10/15/20 to 6/12/18/24", b([5, 10, 15, 20], [6, 12, 18, 24])))
    W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
    W(ul_close())
    W(ability("Storm Surge"))
    W(ul_open())
    W(li("Aghanim's Shard: While Eye of the Storm is active, Storm Surge's strike chance is 2x as high, strike cooldown is decreased by 2s, and lightning strikes all enemies within Eye of the Storm's radius", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Storm Surge Slow and Damage increased from +25% to +30%", b(25, 30)))
    W(li("Level 10 Talent +10% Spell Lifesteal replaced with +4 Armor", t("REWORK")))
    W(ul_close())

    # Riki
    W(hero_header("Riki"))
    W(ability("Cloak and Dagger", slug="riki_backstab"))
    W(ul_open())
    W(li_formula("Agility Multiplier changed",
                 "0.6 + 0.05 per level up", "0.55 + 0.05 per level",
                 lambda L: 0.6 + (0.05) * L, lambda L: 0.55 + (0.05) * L,
                 effective_unchanged=True))
    W(ul_close())
    W(subnote("Effective values are not changed"))
    W(ability("Smoke Screen"))
    W(ul_open())
    W(li("Mana Cost rescaled from 65/70/75/80 to 75", b([65, 70, 75, 80], 75, l=True)))
    W(li("Miss Rate rescaled from 30/45/60/75% to 40/50/60/70%", b([30, 45, 60, 75], [40, 50, 60, 70])))
    W(ul_close())
    W(ability("Blink Strike"))
    W(ul_open())
    W(li("Slow Duration increased from 0.5s to 0.75s", b(0.5, 0.75)))
    W(ul_close())
    W(ability("Tricks of the Trade"))
    W(ul_open())
    W(li("Aghanim's Scepter bonus Cast Range increased from +300 to +500", b(300, 500)))
    W(ul_close())

    # Ringmaster
    W(hero_header("Ringmaster"))
    W(ability("Dark Carnival Barker", slug="ringmaster_dark_carnival_souvenirs"))
    W(ul_open())
    # 7.41: souvenir pool unified — previously each Dark Carnival facet drew
    # from its own 3-souvenir subset (Facet 2: Funhouse Mirror / Strongman Tonic
    # / Whoopee Cushion; Facet 3: Crystal Ball / Unicycle / Weighted Pie).
    # Now both facets share the same 4-souvenir pool. Crystal Ball and Weighted
    # Pie are dropped from the rotation entirely.
    _souvenir_tips = {
        "Funhouse Mirror": "Throws a mirror that on impact creates a hostile illusion of the target enemy hero, mimicking its abilities for a few seconds.",
        "Strongman Tonic": "Drinks a tonic granting Ringmaster bonus attack damage and movement speed for the duration.",
        "Unicycle":        "Mounts a unicycle for 10s. Reaches up to 750 speed (turn rate degrades 130→90). Attacking, casting, picking up runes, taking damage, or crashing dismounts.",
        "Whoopee Cushion": "Places a delayed-trigger cushion at target point that deals damage and slows enemies in its AoE on activation.",
        "Crystal Ball":    "Reveals target area, providing vision and True Sight for a duration.",
        "Weighted Pie":    "Throws a heavy pie at target, dealing damage and applying a heavy movement slow.",
    }
    _souvenirs_kept = ''.join(souvenir_chip(n, s, tooltip=_souvenir_tips[n]) for n, s in [
        ("Funhouse Mirror", "ringmaster_funhouse_mirror"),
        ("Strongman Tonic", "ringmaster_strongman_tonic"),
        ("Unicycle",        "ringmaster_summon_unicycle"),
        ("Whoopee Cushion", "ringmaster_whoopee_cushion"),
    ])
    _souvenirs_removed = ''.join(souvenir_chip(n, s, removed=True, tooltip=_souvenir_tips[n]) for n, s in [
        ("Crystal Ball",  "ringmaster_crystal_ball"),
        ("Weighted Pie",  "ringmaster_weighted_pie"),
    ])
    W(li("Souvenir pool unified across both Dark Carnival facets", t("REWORK"),
         # Visible tag is REWORK, but Crystal Ball + Weighted Pie were dropped
         # from the rotation — surface this row under the DEL filter too so
         # readers tracking removals don't miss it.
         force_tag="rework del",
         extra=inline_note(
             f'<span class="souvenir-group">'
             f'<span class="souvenir-group-label">In pool:</span>{_souvenirs_kept}'
             f'</span>'
             f'<span class="souvenir-group">'
             f'<span class="souvenir-group-label">Removed:</span>{_souvenirs_removed}'
             f'</span>'
         )))
    W(ul_close())
    W(ability("Escape Act", slug="ringmaster_the_box"))
    W(ul_open())
    W(li("Radius and Aghanim's Scepter's Explosion Radius now affected by AoE bonuses", t("NEW")))
    W(li("Targeted unit is no longer stunned for 0.5 seconds when placed in a box", t("DEL")))
    W(ul_close())
    W(ability("Impalement Arts", slug="ringmaster_impalement"))
    W(ul_open())
    W(li("Charges rescaled from 1/2/3/4 to 3", b([1, 2, 3, 4], 3)))
    W(li("Mana Cost decreased from 80 to 50", b(80, 50, l=True)))
    W(li("Impact damage rescaled from 50 to 20/35/50/65", b(50, [20, 35, 50, 65])))
    W(li("Max Health Damage per second (heroes) rescaled from 3.5/4/4.5/5% to 3/4/5/6%", b([3.5, 4, 4.5, 5], [3, 4, 5, 6])))
    W(li("Damage per second (creeps) decreased from 100 to 85/90/95/100", b(100, [85, 90, 95, 100])))
    W(li("Slow Duration decreased from 0.8s to 0.5/0.6/0.7/0.8s", b(0.8, [0.5, 0.6, 0.7, 0.8])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +85 Impalement Arts Impact Damage replaced with +1 Impalement Arts Charge", t("REWORK")))
    W(ul_close())

    # Rubick
    W(hero_header("Rubick"))
    W(ul_open())
    W(li("Base Damage increased by 1", bstat_h("Rubick", "AttackDamageMin", "7.40c", 1), extra=note_box(hero="Rubick", field="AttackDamageMin", before_patch="7.40c")))
    W(li("Damage at level 1 increased from 49–55 to 50–56", br(49, 55, 50, 56)))
    W(ul_close())
    W(ability_change(
        old=dict(
            name="Might and Magus",
            innate=True,
            desc=[
                "Passive.",
                "Grants self <b>1% base attack damage</b> bonus per Spell Amplification bonus.",
                "Grants self <b>0.5% Magic Resistance</b> bonus per Spell Amplification bonus.",
            ],
        ),
        new=dict(
            name="Curiosity",
            slug="rubick_curiosity",
            innate=True,
            desc=[
                "Passive.",
                "Rubick gains <b>1 stack of Curiosity per level</b>. Each stack grants <b>+1 base damage</b>, <b>+0.3% Buff/Debuff Duration</b>, and <b>+2 Area of Effect</b> bonus.",
                "If Rubick <b>sees an enemy Hero cast an ability</b> within 1200 distance of him, he gains <b>2 Curiosity for 20s</b>.",
                "If an enemy that currently provides temporary Curiosity dies within 3s after taking damage from Rubick, he gains <b>1 Curiosity permanently</b>.",
            ],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Telekinesis"))
    W(ul_open())
    W(li("Aghanim's Shard Land Distance bonus changed from +35% to +225 (flat)",
         b(506, 600),
         extra=inline_note("Computed off base Telekinesis Land Distance of 375. "
                           "Old: 375 × 1.35 = 506. New: 375 + 225 = 600.")))
    W(ul_close())
    W(ability("Fade Bolt"))
    W(ul_open())
    W(li("Now reduces both spell and attack damage by default", t("NEW")))
    W(li("Damage Reduction rescaled from 5/15/25/35% to 6/12/18/24%", b([5, 15, 25, 35], [6, 12, 18, 24])))
    W(ul_close())
    W(ability("Spell Steal"))
    W(ul_open())
    W(li("No longer grants 10/20/30% Debuff Amplification", t("DEL")))
    W(li("Stolen spells now have their cooldown decreased by 10/20/30%", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +0.25% Might and Magus Damage/Resistance replaced with +200 Health", t("REWORK")))
    W(li("Level 10 Talent +165 Telekinesis Landing Damage replaced with -2s Telekinesis Cooldown", t("REWORK")))
    W(li("Level 15 Talent +20% Fade Bolt Damage Reduction replaced with -3s Fade Bolt Cooldown", t("REWORK")))
    W(li("Level 15 Talent -25% Stolen Spells Cooldown replaced with -50% Stolen Spells Mana Cost", t("REWORK")))
    W(li("Level 20 Talent -5s Telekinesis Cooldown replaced with Telekinesis Landing Deals 325 Damage (now this talent applies damage to the thrown enemy as well)", t("REWORK"),
         extra=inline_note("It used to deal damage only in AoE, leaving the thrown enemy unharmed. Doesn't deal damage to thrown allies or self.")))
    W(li("Level 20 Talent -5s Fade Bolt Cooldown replaced with +12% Fade Bolt Damage Reduction", t("REWORK")))
    W(li("Level 25 Talent +400 Telekinesis Land Distance replaced with 2x Curiosity Bonuses", t("REWORK")))
    W(ul_close())

    # Sand King
    W(hero_header("Sand King"))
    W(ability("Caustic Finale", slug="sandking_caustic_finale"))
    W(ul_open())
    W(li("No longer levels with Epicenter", t("REWORK")))
    W(li_formula("Base Damage rescaled",
                 "20/40/60/80", "17 + 3 per level",
                 lambda L: 80.0, lambda L: 17.0 + 3.0 * L))
    W(li_formula("Max Health Damage rescaled",
                 "3/7/11/15%", "2.5% + 0.5% per level",
                 lambda L: 15.0, lambda L: 2.5 + 0.5 * L))
    W(li("Duration decreased from 4.5/5/5.5/6s to 4.5s", b([4.5, 5, 5.5, 6], 4.5)))
    W(ul_close())
    W(ability("Burrowstrike", slug="sandking_burrowstrike"))
    W(ul_open())
    W(li("Cast Range increased from 525/600/675/750 to 550/625/700/775", b([525, 600, 675, 750], [550, 625, 700, 775])))
    W(li("Sand King now immediately re-gains invisibility if the Burrowstrike ends within Sand Storm's AoE", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent +75/7 Base/Incremental Radius of Epicenter replaced with +6 Epicenter Pulses", t("REWORK")))
    W(li("Level 25 Talent 50% Sand Storm Slow replaced with 35% Sand Storm Slow and Blind", t("REWORK")))
    W(li("Level 25 Talent +8 Epicenter Pulses replaced with +125 Stinger Damage", t("REWORK")))
    W(ul_close())

    # Shadow Demon
    W(hero_header("Shadow Demon"))
    W(ability("Menace"))
    W(ul_open())
    W(li_formula("Damage amplification changed",
                 "2.5%", "1.9% + 0.1% per level",
                 lambda L: 2.5, lambda L: 1.9 + 0.1 * L))
    W(ul_close())
    W(ability("Disruption"))
    W(ul_open())
    W(li("Can now target Spirit Bear", t("MISC")))
    W(ul_close())
    W(ability("Disseminate"))
    W(ul_open())
    W(li("Shared Damage rescaled from 20/25/30/35% to 16/24/32/40%", b([20, 25, 30, 35], [16, 24, 32, 40])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent +150 Demonic Purge Damage replaced with -20s Demonic Purge Cooldown", t("REWORK")))
    W(li("Level 25 Talent -30s Demonic Purge Cooldown replaced with Demonic Purge Applies Shadow Poison", t("REWORK"),
         extra=inline_note("1 stack per second over the debuff duration.")))
    W(ul_close())

    # Shadow Fiend
    W(hero_header("Shadow Fiend"))
    W(ability("Necromastery"))
    W(ul_open())
    W(li("No longer levels with Requiem of Souls", t("REWORK")))
    W(li_formula("Damage per soul rescaled",
                 "1/2/3/4", "1.35 + 0.15 per level",
                 lambda L: 4.0, lambda L: 1.35 + 0.15 * L))
    W(li("Base Max Souls decreased from 20/22/24/26 to 20", b([20, 22, 24, 26], 20)))
    W(ul_close())
    W(ability("Shadowraze", slug="nevermore_shadowraze1"))
    W(ul_open())
    W(li("Damage decreased from 90/160/230/300 to 85/150/215/280", b([90, 160, 230, 300], [85, 150, 215, 280])))
    W(li("Now damage is increased by 3 per Necromastery soul", t("NEW")))
    W(li("Aghanim's Shard now also applies a stacking 12% slow debuff to enemies hit", t("NEW")))
    W(ul_close())
    W(ability_change(
        old=dict(
            name="Feast of Souls",
            slug="nevermore_frenzy",
            desc=[
                "Active. Costs <b>5 souls</b> to cast.",
                "Shadow Fiend gains <b>40/55/70/85 Attack Speed</b> and <b>5/7/9/11% Movement Speed</b> for the duration.",
            ],
        ),
        new=dict(
            name="Feast of Souls",
            slug="nevermore_frenzy",
            desc=[
                "Active. No longer requires souls to cast.",
                "Instead, while active, Shadow Fiend gains souls from <b>2 enemies in a 600 radius every 0.5s</b>, prioritizing heroes. Each enemy can provide souls once — creeps give <b>1 soul</b>, heroes give <b>3</b>. Can collect souls from up to <b>4/6/8/10 enemies</b>.",
                "After the effect ends, Shadow Fiend loses souls whose owners are still alive, retaining the rest for <b>8s</b>."
                + inline_note("The enemy threshold limits only the amount of enemies affected, not the total souls collected. At the cap of 10, you can collect souls from 5 heroes and 5 creeps for 20 souls. 10 Dummy Targets in Hero Demo mode yield 30 souls."),
            ],
        ),
        summary="Ability reworked.",
        tag="rework",
    ))
    W(ul_open())
    W(li("Bonus Attack Speed decreased from 40/55/70/85 to 35/50/65/80", b([40, 55, 70, 85], [35, 50, 65, 80])))
    W(li("Bonus Move Speed decreased from 5/7/9/11% to 4/6/8/10%", b([5, 7, 9, 11], [4, 6, 8, 10])))
    W(ul_close())
    W(ability("Requiem of Souls", slug="nevermore_requiem"))
    W(ul_open())
    W(li("Now can't use more than 20 souls per cast", t("NERF")))
    W(li("Aghanim's Scepter no longer has a damage penalty on the returning Requiem of Souls", t("BUFF")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +120 Shadowraze Damage replaced with +2 Feast of Souls Souls Collected Per Hero", t("REWORK")))
    W(li("Level 20 Talent +2 Damage Per Soul replaced with +5 Necromastery Max Souls", t("REWORK")))
    W(ul_close())

    # Shadow Shaman
    W(hero_header("Shadow Shaman"))
    W(ability("Fowl Play"))
    W(ul_open())
    W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
    W(li("Now adds a chicken illusion per 5 levels", t("NEW")))
    _ss_pill, _ss_table = scale_pill(
        "5% + 5% per 5 levels",
        lambda L: 5.0 + 5.0 * (L // 5),
        levels=[1, 5, 10, 15, 20, 25, 30],
        value_fmt="{:.0f}%",
    )
    W(li("Now also provides bonus movement speed equal to " + _ss_pill,
         t("NEW"), extra=_ss_table))
    W(ul_close())
    W(ability("Urnaconda"))
    W(ul_open())
    W(li("Aghanim's Shard: New ability — throws a jar at a location, dealing 275 damage to all enemies in a 225 radius and creating a Massive Serpent Ward that lasts for 15s. The ward has 4× health and damage of the normal Serpent Wards. <b>Cooldown:</b> 50s. <b>Mana Cost:</b> 115. <b>Cast Range:</b> 650",
         t("NEW")))
    W(ul_close())

    # Silencer
    W(hero_header("Silencer"))
    W(ul_open())
    W(li("Base Movement Speed increased from 290 to 300", b(290, 300)))
    W(ul_close())
    _sil_pill, _sil_table = scale_pill(
        "5% + 0.5% per level",
        lambda L: 5.0 + 0.5 * L,
        value_fmt="{:.1f}%",
    )
    W(ability_change(
        old=dict(
            name="Brain Drain",
            slug="silencer_brain_drain",
            innate=True,
            desc=[
                "Passive.",
                "Silencer permanently steals Intelligence from enemy heroes he kills or that die nearby.",
                "<b>Intelligence Stolen:</b> 2. <b>Steal Radius:</b> 925.",
                aghs_shard_line("Increases Intelligence Stolen to 4."),
            ],
        ),
        new=dict(
            name="Suffer In Silence",
            slug="silencer_brain_drain",
            innate=True,
            desc=[
                "Passive.",
                "Silencer takes less damage from and deals more damage to silenced targets. Damage modifier is " + _sil_pill + " for both reduction and amplification.",
                "If an enemy hero dies within <b>925 range</b> of Silencer or was debuffed by Silencer at the time of death, he <b>permanently steals 1 Intelligence</b>. If the victim was silenced, an <b>extra 1 Intelligence</b> is stolen.",
            ],
            tables=[_sil_table],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Arcane Curse", slug="silencer_curse_of_the_silent"))
    W(ul_open())
    W(li("No longer has 1.25x slow and damage multiplier against silenced enemies", t("DEL")))
    W(ul_close())
    W(ability("Glaives of Wisdom"))
    W(ul_open())
    W(li("Mana Cost decreased from 14/16/18/20 to 12/14/16/18", b([14, 16, 18, 20], [12, 14, 16, 18], l=True)))
    W(li("Aghanim's Shard: Increases Int Steal by 1 and causes Glaives to bounce once to a random enemy within 450 range", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +0.25 Arcane Curse Silenced Multiplier replaced with +7% Suffer In Silence Damage", t("REWORK")))
    W(li("Level 25 Talent Glaives of Wisdom Damage increased from +25% to +30%", b(25, 30)))
    W(li("Level 25 Talent 2 Arcane Curse charges replaced with +2s Global Silence Duration", t("REWORK")))
    W(ul_close())

    # Skywrath Mage
    W(hero_header("Skywrath Mage"))
    _sw_pill, _sw_table = scale_pill(
        "13.5 + 1.5 per level",
        lambda L: 13.5 + 1.5 * L,
        value_fmt="{:.1f}",
    )
    W(ability_change(
        old=dict(
            name="Ruin and Restoration",
            innate=True,
            desc=[
                "Passive, levels up with Mystic Flare.",
                "Passively provides Skywrath Mage with <b>20/30/40/50% Spell Lifesteal</b>.",
                "Has 80% penalty against creeps, similarly to other sources of Spell Lifesteal.",
            ],
        ),
        new=dict(
            name="Shield of the Scion",
            slug="skywrath_mage_shield_of_the_scion",
            innate=True,
            desc=[
                "Passive.",
                "Whenever Skywrath Mage deals magical damage with his abilities to an enemy hero, he gains a magic damage barrier equal to " + _sw_pill + " for <b>12s</b>.",
                "Each instance stacks independently.",
            ],
            tables=[_sw_table],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Concussive Shot"))
    W(ul_open())
    W(li("Now considers Spirit Bear as a true hero for prioritization. Creep Heroes are now considered as secondary targets", t("MISC")))
    W(ul_close())

    # Slardar
    W(hero_header("Slardar"))
    W(ability("Seaborn Sentinel"))
    W(ul_open())
    W(li("No longer levels with Corrosive Haze", t("REWORK")))
    W(li_formula("Bonus HP Regen changed",
                 "2.5/5/7.5/10", "1.75 + 0.25 per level",
                 lambda L: 10.0, lambda L: 1.75 + 0.25 * L))
    W(li("Aghanim's Scepter Bonus HP Regen decreased from +22 to +20", b(22, 20)))
    W(li_formula("Bonus Armor changed",
                 "3/4/5/6", "1.8 + 0.2 per level",
                 lambda L: 6.0, lambda L: 1.8 + 0.2 * L))
    W(li("Aghanim's Scepter Bonus Armor decreased from +10 to +8", b(10, 8)))
    _sdr_pill, _sdr_table = scale_pill(
        "11.4% + 0.6% per level",
        lambda L: 11.4 + 0.6 * L,
        value_fmt="{:.1f}%",
    )
    W(li("Flat 8/16/24/32 bonus damage replaced with " + _sdr_pill + " bonus attack damage",
         t("REWORK"), extra=_sdr_table))
    W(ul_close())
    W(ability("Guardian Sprint", slug="slardar_sprint"))
    W(ul_open())
    W(li("Slardar now has 100% slow resistance for the first 2.5s of Guardian Sprint. This bonus fades to 0 over the remaining duration", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +14 Seaborn Sentinel Bonus Attack Damage replaced with +30 Bash of the Deep Damage", t("REWORK")))
    W(li("Level 15 Talent +40 Bash of the Deep Damage replaced with -3 Corrosive Haze Armor", t("REWORK")))
    W(li("Level 20 Talent -4 Corrosive Haze Armor replaced with +16% Seaborn Sentinel Bonus Attack Damage", t("REWORK")))
    W(ul_close())

    # Slark
    W(hero_header("Slark"))
    W(ability("Essence Shift"))
    W(ul_open())
    W(li_formula("Duration changed",
                 "15s + 2.5s per level up", "12.5s + 2.5s per level",
                 lambda L: 15.0 + (2.5) * L, lambda L: 12.5 + (2.5) * L,
                 effective_unchanged=True))
    W(ul_close())
    W(subnote("Effective values are not changed"))
    W(ability("Saltwater Shiv"))
    W(ul_open())
    W(li("Stacks now have independent durations and don't refresh previous ones", t("REWORK")))
    W(li("Cooldown increased from 10/8/6/4s to 14/12/10/8s", b([10, 8, 6, 4], [14, 12, 10, 8], l=True)))
    W(li("Mana Cost increased from 20 to 25/30/35/40", b(20, [25, 30, 35, 40], l=True)))
    W(li("Cast Range is now Slark's attack range + 50", t("REWORK")))
    W(li("Stack Restoration Steal increased from 2/4/6/8% to 4/8/12/16%", b([2, 4, 6, 8], [4, 8, 12, 16])))
    W(li("Stack Regen Steal increased from 2/4/6/8 to 4/8/12/16", b([2, 4, 6, 8], [4, 8, 12, 16])))
    W(li("Stack Speed Steal increased from 2/4/6/8 to 4/8/12/16", b([2, 4, 6, 8], [4, 8, 12, 16])))
    W(li("Now also modifies incoming healing", t("NEW"),
         extra=inline_note("As a result of Health Restoration changes")))
    W(ul_close())

    # Snapfire
    W(hero_header("Snapfire"))
    _boomstick_min_pill, _boomstick_min_table = scale_pill(
        "495 + 5 per level",
        lambda L: 495.0 + 5.0 * L,
        value_fmt="{:.0f}",
    )
    _boomstick_max_pill, _boomstick_max_table = scale_pill(
        "50 + 5 per level",
        lambda L: 50.0 + 5.0 * L,
        value_fmt="{:.0f}",
    )
    W(ability_change(
        old=dict(
            name="Buckshot",
            innate=True,
            desc=[
                "Passive.",
                "Snapfire's attacks deal <b>25% more damage</b>, but they have a <b>25% chance</b> of a glancing shot that will deal <b>50% less damage</b>.",
            ],
        ),
        new=dict(
            name="Boomstick",
            innate=True,
            desc=[
                "Passive.",
                "Snapfire deals more damage with her attacks and abilities, the closer she is to her target.",
                "<b>Min Damage Amp:</b> 0% at a distance of " + _boomstick_min_pill + ".",
                "<b>Max Damage Amp:</b> 35% at a distance of " + _boomstick_max_pill + ".",
            ],
            tables=[_boomstick_min_table, _boomstick_max_table],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Scatterblast"))
    W(ul_open())
    W(li("Point-blank damage bonus decreased from 50% to 30%", b(50, 30)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Lil' Shredder Attacks increased from +1 to +2", b(1, 2)))
    W(ul_close())

    # Sniper
    W(hero_header("Sniper"))
    W(ability("Keen Scope"))
    W(ul_open())
    W(li("No longer levels with Assassinate", t("REWORK")))
    W(li("No longer increases attack range", t("DEL")))
    _sn_pill, _sn_table = scale_pill(
        "1.5% + 0.05% per level",
        lambda L: 1.5 + 0.05 * L,
        value_fmt="{:.2f}%",
    )
    W(li("Now increases damage from Sniper's attacks by " + _sn_pill + " for every 100 units of distance between him and the target",
         t("NEW"), extra=_sn_table))
    W(li("Also affects attack damage from Assassinate", t("NEW")))
    W(ul_close())
    W(ability("Take Aim"))
    W(ul_open())
    W(li("Now passively grants 160/240/320/400 attack range", t("NEW")))
    W(li("Active Bonus Attack Range rescaled from 100/150/200/250 to 75/150/225/300", b([100, 150, 200, 250], [75, 150, 225, 300])))
    W(ul_close())
    W(ability("Assassinate"))
    W(ul_open())
    W(li("No longer amplifies attack damage to 100/110/120%", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +55 Take Aim Attack Range Bonus replaced with +50 Take Aim Passive Attack Range", t("REWORK")))
    W(ul_close())

    # Spectre
    W(hero_header("Spectre"))
    W(ul_open())
    W(li("Base Movement Speed increased from 290 to 295", b(290, 295)))
    W(li("Base Health Regen increased from 1.0 to 1.5", b(1.0, 1.5)))
    W(ul_close())
    W(ability("Desolate"))
    W(ul_open())
    W(li_formula("Damage changed",
                 "25 + 2 per level up", "23 + 2 per level",
                 lambda L: 25.0 + (2.0) * L, lambda L: 23.0 + (2.0) * L,
                 effective_unchanged=True))
    W(ul_close())
    W(subnote("Effective values are not changed"))
    W(ability("Shadow Step"))
    W(ul_open())
    W(li("Cooldown decreased from 30/26/22/18s to 24/21/18/15s", b([30, 26, 22, 18], [24, 21, 18, 15], l=True)))
    W(li("Cast Range increased from 750/900/1050/1200 to 825/950/1075/1200", b([750, 900, 1050, 1200], [825, 950, 1075, 1200])))
    W(li("Illusion Damage increased from 32/38/44/50% to 35/40/45/50%", b([32, 38, 44, 50], [35, 40, 45, 50])))
    W(li("Illusion Damage Taken decreased from 200% to 200/185/170/155%", b(200, [200, 185, 170, 155])))
    W(ul_close())
    W(ability("Haunt"))
    W(ul_open())
    W(li("Cooldown decreased from 180/160/140s to 160/150/140s", b([180, 160, 140], [160, 150, 140], l=True)))
    W(li("Duration rescaled from 5/6/7s to 6s", b([5, 6, 7], 6)))
    W(li("Illusion Damage decreased from 30/55/80% to 30/50/70%", b([30, 55, 80], [30, 50, 70])))
    W(ul_close())

    # Spirit Breaker
    W(hero_header("Spirit Breaker"))
    W(ability_change(
        old=dict(
            name="Herd Mentality",
            innate=True,
            desc=[
                "Passive.",
                "Provides the hero on Spirit Breaker's team with the <b>least Experience points</b> a buff that increases their Experience gain by <b>50%</b> until they reach the level of the second-least.",
            ],
        ),
        new=dict(
            name="Empowering Haste",
            slug="spirit_breaker_bull_rush",
            innate=True,
            desc=[
                "Passive.",
                "Spirit Breaker gains bonus Movement Speed whenever he stuns an enemy. Effect depends on unit type: <b>stunning a hero</b> gives <b>+8% for 2s</b>; <b>other units</b> give <b>+2% for 1s</b>.",
                "Multiple stuns stack with <b>independent durations</b>. Bull Rush duration is paused during Charge of Darkness, but it can still gain new stacks.",
                "Bonus allows Spirit Breaker to go <b>over the max movement speed limit</b>.",
            ],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Charge of Darkness"))
    W(ul_open())
    W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
    W(ul_close())
    W(ability("Greater Bash"))
    W(ul_open())
    W(li("Aghanim's Scepter: Increases knockback by roughly 30%. If a knocked-back enemy collides with another enemy, the second enemy is also bashed, and the original target takes 25% of Spirit Breaker's Greater Bash damage again", t("NEW"),
         extra=inline_note(
             "This effect is applied to Charge of Darkness and Nether Strike as well, since those abilities use Greater Bash.<br>"
             "Creeps take 25% damage of repeated damage.<br>"
             "Bodies of killed units keep flying and pushing enemies."
         )))
    W(ul_close())
    W(ability("Planar Pocket"))
    W(ul_open())
    W(li("Aghanim's Shard: Now grants Planar Pocket", t("NEW")))
    W(li("Cooldown increased from 25s to 30s", b(25, 30, l=True)))
    W(li("Self Magic Resistance decreased from 75% to 40%", b(75, 40)))
    W(li("Effect now ends if Spirit Breaker is more than 900 units away from the target", t("REWORK")))
    W(li("Now can be cast without cancelling Charge of Darkness", t("REWORK")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +45 Damage replaced with +60 Charge of Darkness Bonus Speed", t("REWORK")))
    W(li("Level 20 Talent -0.3s Greater Bash Cooldown replaced with +8%/+2% Empowering Haste Movespeed Bonus", t("REWORK")))
    W(ul_close())

    # Storm Spirit
    W(hero_header("Storm Spirit"))
    W(ability("Galvanized"))
    W(ul_open())
    W(li("Leveling up Ball Lightning no longer grants 3 Galvanized charges", t("DEL")))
    W(ul_close())
    W(ability("Static Remnant"))
    W(ul_open())
    W(li("Remnants now spawn at Storm Spirit's location and move at 300 speed to the target location", t("NEW")))
    W(ul_close())

    # Sven
    W(hero_header("Sven"))
    W(ul_open())
    W(li("Base strength increased from 23 to 24", b(23, 24)))
    W(li("Damage at level 1 increased from 60–62 to 61–63", br(60, 62, 61, 63)))
    W(ul_close())
    _sv_pill, _sv_table = scale_pill(
        "0.08 + 0.02 per level",
        lambda L: 0.08 + 0.02 * L,
        value_fmt="{:.2f}",
    )
    W(ability_change(
        old=dict(
            name="Vanquisher",
            innate=True,
            desc=[
                "Passive.",
                "Sven's attacks deal <b>15% more damage</b> to <b>stunned enemies</b>.",
                "Worked off Sven's base attack damage; talent line scaled the bonus.",
            ],
        ),
        new=dict(
            name="Wrath of God",
            slug="sven_wrath_of_god",
            innate=True,
            desc=[
                "Passive.",
                "Increases the attack damage Sven gains per point of Strength by " + _sv_pill + ".",
                "<b>Disabled by Break.</b>",
            ],
            tables=[_sv_table],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Warcry"))
    W(ul_open())
    W(li("Aghanim's Shard reworked: makes Warcry undispellable, increases radius from 700 to 900, and grants a <b>300 physical damage barrier</b> + an additional <b>+3% movement speed</b> bonus when active",
         t("NEW"),
         extra=inline_note("No longer provides a passive aura.")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +10% Vanquisher Bonus Damage replaced with +20% God's Strength Slow Resistance", t("REWORK")))
    W(li("Level 20 Talent +20% God's Strength Slow Resistance replaced with -25% Storm Hammer Cooldown and Mana Cost", t("REWORK")))
    W(ul_close())

    # Techies
    W(hero_header("Techies"))
    _tch_pill, _tch_table = scale_pill(
        "0.08% + 0.02% per level",
        lambda L: 0.08 + 0.02 * L,
        value_fmt="{:.2f}%",
    )
    W(ability_change(
        old=dict(
            name="Minefield Sign",
            slug="techies_minefield_sign",
            innate=True,
            desc=[
                "Active.",
                "Places a sign that makes mines within a <b>500 radius</b> invulnerable.",
                "<b>Cast Point:</b> 1.5s. <b>Cooldown:</b> 60s. <b>Duration:</b> 60s. Only one sign can exist at a time.",
                aghs_line("Increases radius to 1000 and duration to 4 minutes. When an enemy hero gets within 200 units of the sign, the entire 1000 radius becomes a minefield for 10s — enemy units take 300 damage for every 200 units moved. Minefield area becomes visible to enemies once activated. The sign is destroyed after the minefield expires."),
            ],
        ),
        new=dict(
            name="M.A.D.",
            slug="techies_mutually_assured_destruction",
            innate=True,
            desc=[
                "Passive.",
                "Increases mana regen by a portion of Techies' max mana equal to " + _tch_pill + ".",
                "When Techies die, they leave behind a barrel that explodes after <b>1.5s</b>, dealing magical damage equal to <b>50 + 30% of their max mana</b> to enemies in a <b>400 AoE</b>. The barrel provides 400 obstructed vision until it explodes.",
                aghs_shard_line("Increases mana-to-damage by 10%. Adds an active component — Techies plant the M.A.D. barrel and detonate it later via a sub-ability. The barrel is invisible and can be destroyed before detonation begins. Detonating makes it visible and immortal, then it explodes after the same 1.5s delay. Only one M.A.D. can exist via the active cast at a time. Barrel Health: 200. Cast Range: 450. No Mana Cost. Cooldown: 30s. Cast Point: 1s."),
            ],
            tables=[_tch_table],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Reactive Tazer"))
    W(ul_open())
    W(li("Can now always be cast on allies", t("NEW")))
    W(li("Cast Range increased from 500 to 600", b(500, 600)))
    W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
    W(ul_close())
    W(ability("Blast Off!", slug="techies_suicide"))
    W(ul_open())
    W(li("Now deals its self damage before damaging enemies", t("MISC")))
    W(li("Techies are now rooted and disarmed instead of self-stunned during Blast Off's leap animation", t("MISC")))
    W(ul_close())
    W(ability("Proximity Mines", slug="techies_land_mines"))
    W(ul_open())
    W(li("Damage source changed from Proximity Mines to the caster", t("REWORK")))
    W(ul_close())
    W(ability("Minefield Sign"))
    W(ul_open())
    W(li("Now only available with Aghanim's Scepter", t("REWORK")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +3 Mana Regen replaced with +25% Reactive Tazer Buff and Disarm Duration", t("REWORK")))
    W(li("Level 25 Talent Damage increased from +252 to +253", b(252, 253)))
    W(ul_close())

    # Templar Assassin
    W(hero_header("Templar Assassin"))
    W(ul_open())
    W(li("Base Health Regen decreased from 1 to 0", b(1, 0)))
    W(ul_close())
    _ta_ramp_pill, _ta_ramp_table = scale_pill(
        "2.05s − 0.05s per level",
        lambda L: 2.05 - 0.05 * L,
        value_fmt="{:.2f}s",
    )
    _ta_hp_pill, _ta_hp_table = scale_pill(
        "2.7 + 0.3 per level",
        lambda L: 2.7 + 0.3 * L,
        value_fmt="{:.1f}",
    )
    _ta_mp_pill, _ta_mp_table = scale_pill(
        "2.2 + 0.2 per level",
        lambda L: 2.2 + 0.2 * L,
        value_fmt="{:.1f}",
    )
    W(ability_change(
        old=dict(
            name="Third Eye",
            innate=True,
            desc=[
                "Passive.",
                "Templar Assassin and her teammates can see <b>Roshan's respawn timer</b>. The indicator is displayed above the Scan ability.",
            ],
        ),
        new=dict(
            name="Inner Peace",
            slug="templar_assassin_inner_peace",
            innate=True,
            desc=[
                "Passive.",
                "After remaining stationary for 0.25s, Templar Assassin begins meditating, gaining bonus health regen and mana regen. Bonuses linearly ramp from 0 up to their maximum, reached after " + _ta_ramp_pill + ".",
                "Moving from the current position or taking damage from an enemy <b>resets</b> the regen bonuses.",
                "<b>Max Health Regen:</b> " + _ta_hp_pill + ".  <b>Max Mana Regen:</b> " + _ta_mp_pill + ".",
            ],
            tables=[_ta_ramp_table, _ta_hp_table, _ta_mp_table],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Refraction"))
    W(ul_open())
    W(li("Aghanim's Shard: Increases bonus damage by 30 and allows Refraction to be cast while disabled", t("NEW")))
    W(ul_close())
    W(ability("Meld"))
    W(ul_open())
    W(li("Now, if the attack that broke Meld splits with Psi Blades, Bonus Damage and Armor Reduction are now applied to all affected enemies", t("NEW")))
    W(ul_close())
    W(ability("Psionic Trap"))
    W(ul_open())
    W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
    W(li("Aghanim's Scepter: When activated, Traps now also silence enemies from 0.25s up to 3s depending on the trap charge", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +3 Meld Armor reduction replaced with +3 Psionic Traps", t("REWORK")))
    W(li("Level 15 Talent Refraction Can Be Cast While Disabled replaced with +225 Meld Attack Range", t("REWORK")))
    W(li("Level 20 Talent +40 Refraction Damage replaced with +4 Meld Armor Reduction", t("REWORK")))
    W(ul_close())

    # Terrorblade
    W(hero_header("Terrorblade"))
    W(ul_open())
    W(li("Base Armor increased by 1", bstat_h("Terrorblade", "ArmorPhysical", "7.40c", 1), extra=note_box(hero="Terrorblade", field="ArmorPhysical", before_patch="7.40c")))
    W(ul_close())
    W(ability("Conjure Image"))
    W(ul_open())
    W(li("Illusion Damage increased from 20/25/30/35% to 25/30/35/40%", b([20, 25, 30, 35], [25, 30, 35, 40])))
    W(ul_close())
    W(ability("Demon Zeal"))
    W(ul_open())
    W(li("Cooldown decreased from 60s to 45s", b(60, 45, l=True)))
    W(li("Duration decreased from 30s to 25s", b(30, 25)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +15% Reflection Slow/Damage replaced with -25% Sunder Minimum HP Swap", t("REWORK")))
    W(ul_close())

    # Tidehunter
    W(hero_header("Tidehunter"))
    W(ul_open())
    W(li("Strength gain increased from 3.6 to 3.7", b(3.6, 3.7)))
    W(ul_close())
    W(ability_change(
        old=dict(
            name="Blubber",
            innate=True,
            desc=[
                "Passive.",
                "Tidehunter removes negative status effects (<b>Strong Dispel</b>) if he takes more than <b>500 damage</b> from player-controlled sources. Damage counter resets after <b>7s</b>.",
            ],
        ),
        new=dict(
            name="Leviathan's Catch",
            slug="tidehunter_leviathans_catch",
            innate=True,
            desc=[
                "Passive.",
                "Whenever an enemy hero dies while affected by any of Tidehunter's debuffs or is killed by him, they <b>drop a fish</b>.",
                "Tidehunter can eat the fish to grow in size and <b>permanently gain +3 Max Health, +2 Attack Range, and +1 Bonus Damage Block</b>. Tidehunter also <b>automatically eats a fish on every level-up</b>."
                + inline_note(
                    "The fish flies 400 units towards Tidehunter upon spawning, stays in the world indefinitely and can be destroyed by an attack from Tidehunter's enemies.<br>"
                    "Bonus Damage Block is only applied if there is a source of damage block being applied to an incoming physical attack."
                ),
            ],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Anchor Smash"))
    W(ul_open())
    W(li("Radius changed from 375 to 225 + Tidehunter's Attack Range", t("REWORK"),
         extra=inline_note("Tidehunter's base Attack Range is 150, so the effective radius at level 1 is 375 — unchanged before Fish bonuses.")))
    W(ul_close())
    W(ability("Kraken Shell"))
    W(ul_open())
    W(li("Now applies a strong dispel to Tidehunter if he takes more than 600/550/500/450 damage within 7 seconds", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Blubber effect triggers Anchor Smash replaced with Kraken Shell Cleanse triggers Anchor Smash", t("REWORK")))
    W(ul_close())

    # Timbersaw
    W(hero_header("Timbersaw"))
    W(ability("Exposure Therapy"))
    W(ul_open())
    W(li("No longer levels with Chakram", t("REWORK")))
    W(li_formula("Mana gain per tree destroyed changed",
                 "4/6/8/10", "3.75 + 0.25 per level",
                 lambda L: 10.0, lambda L: 3.75 + 0.25 * L))
    W(ul_close())

    # Tinker
    W(hero_header("Tinker"))
    W(ul_open())
    W(li("Base health regen increased from 0 to 0.5", b(0, 0.5)))
    W(li("Base Movement Speed decreased from 310 to 305", b(310, 305)))
    W(ul_close())
    W(ability("Laser"))
    W(ul_open())
    W(li("Aghanim's Scepter no longer adds bounces", t("DEL")))
    W(ul_close())
    W(ability("March of the Machines"))
    W(ul_open())
    W(li("Aghanim's Scepter: Robots apply a non-stacking heal over time of 35 health per second to allies they come through. Heal duration: 4 seconds", t("NEW")))
    W(ul_close())
    W(ability_change(
        summary="New ability.",
        tag="new",
        old=dict(
            name="Defense Matrix",
            slug="tinker_defense_matrix",
            desc=[
                "Surrounds the target ally with an energy field that absorbs <b>100/180/240/320</b> magical damage and grants <b>10/20/30/40%</b> Status Resistance. Lasts 12 seconds.",
                "Cast Range: 700/750/800/850. Mana Cost: 70/80/90/100. Cooldown: 20s.",
            ],
        ),
        new=dict(
            name="Deploy Turrets",
            slug="tinker_deploy_turrets",
            desc=[
                "After a 0.5s delay, airdrops a group of three uncontrollable turrets at the target 250 radius area, dealing <b>40/80/120/160</b> magical damage, destroying trees and pushing away enemies by 100 units and Tinker by 350.",
                "Turrets seek enemy heroes within <b>650/700/750/800</b> range and shoot missiles in their direction every 1.5 seconds. The missile deals <b>20/40/60/80</b> magical damage to the enemy it hits and 50% of the damage to other enemies within 200 AoE. Each turret has <b>40/80/120/160</b> health and exists for 4.5 seconds.",
                "<b>Stats:</b> Gold Bounty 5/10/15/20. XP Bounty 5/10/15/20. Turn Rate 0.55. Missile Speed 1200. Missile Flight Distance 650/700/750/800.",
                "<b>Cast:</b> Cast Range 600. Mana Cost 100/120/140/160. Cooldown 24/22/20/18s. Cast Point 0.1s."
                + inline_note(
                    "Each of three turrets activates with a small delay after the previous one (0.1s, 0.6s, and 1.1s after deployment)."
                    "<br>The missile flies in a forward direction and can be dodged by moving out of its way."
                    "<br>Turrets target heroes only, but missiles can hit creeps on their way."
                    "<br>Turrets prioritize the same hero until they are out of reach. Splash damage is not dealt to the hit unit itself."),
                aghs_line("Turrets activate 0.3s faster, and fire missiles 20% faster, which results in firing one additional volley of missiles."),
            ],
        ),
    ))
    W(ability("Rearm"))
    W(ul_open())
    W(li("Cooldown decreased from 7/6/5s to 5.5/5/4.5s", b([7, 6, 5], [5.5, 5, 4.5], l=True)))
    W(ul_close())
    W(ability("Warp Flare", slug="tinker_warp_grenade"))
    W(ul_open())
    W(li("Teleport distance now depends on Warp Flare cast range and scales with distance from Tinker, so that nearby enemies are teleported further than far enemies", t("REWORK"),
         extra=inline_note("Max teleportation distance is 60% of Warp Flare's cast range and decreases down to 0 at the max cast range (700 by default).")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +60 Defense Matrix Damage Barrier replaced with +100 Deploy Turrets Tinker Knockback", t("REWORK")))
    W(li("Level 20 Talent +10% Defense Matrix Status Resistance replaced with +60 Deploy Turrets Missile Damage", t("REWORK")))
    W(li("Level 25 Talent: +40 Intelligence replaced with -0.25s Time to Rearm", t("REWORK")))
    W(li("Level 25 Talent: Laser AoE increased from 200 to 250", b(200, 250)))
    W(ul_close())

    # Tiny
    W(hero_header("Tiny"))
    W(ability_change(
        old=dict(
            name="Craggy Exterior",
            slug="tiny_craggy_exterior",
            innate=True,
            desc=[
                "Passive.",
                "Enemies that attack Tiny get a stacking debuff that decreases their attack damage by <b>2/3/4/5%</b> per stack (levels with Grow). <b>Max Stacks:</b> 10. <b>Debuff Duration:</b> 5s (refreshes on each stack).",
            ],
        ),
        new=dict(
            name="Insurmountable",
            slug="tiny_insurmountable",
            innate=True,
            desc=[
                "Passive.",
                "Slow Resistance now also applies to <b>Attack Speed Slows</b>.",
                "Tiny gains <b>Slow Resistance equal to 20% of his Strength</b> and <b>Status Resistance equal to 10% of his Strength</b>.",
            ],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Avalanche"))
    W(ul_open())
    W(li("Mana Cost increased from 95/110/125/140 to 105/120/135/150", b([95, 110, 125, 140], [105, 120, 135, 150], l=True)))
    W(li("Damage decreased from 100/190/280/370 to 90/180/270/360", b([100, 190, 280, 370], [90, 180, 270, 360])))
    W(ul_close())
    W(ability("Toss"))
    W(ul_open())
    W(li("Mana Cost rescaled from 110/125/140/155 to 125", b([110, 125, 140, 155], 125, l=True)))
    W(ul_close())
    W(ability("Tree Grab"))
    W(ul_open())
    W(li("Mana Cost decreased from 40 to 40/35/30/25", b(40, [40, 35, 30, 25], l=True)))
    W(li("Cooldown decreased from 16/15/14/13s to 15/12/9/6s", b([16, 15, 14, 13], [15, 12, 9, 6], l=True)))
    W(li("Cast Range increased from 165 to 200", b(165, 200)))
    W(li("Attacks rescaled from 5 to 4/5/6/7", b(5, [4, 5, 6, 7])))
    W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
    W(ul_close())
    W(ability("Tree Throw", slug="tiny_toss_tree"))
    W(ul_open())
    W(li("No longer applies a slow on the tossed tree by default", t("DEL")))
    W(ul_close())
    W(ability("Grow"))
    W(ul_open())
    W(li("Aghanim's Shard: Thrown trees and tossed units deal 20% more damage in their AoE, have +125 radius, and apply a 25% movement slow and a 45 attack speed slow to all units in the AoE of Toss, Tree Throw, and Tree Volley for 2.5s. Damage is not increased for the Tossed unit itself", t("NEW")))
    W(ul_close())
    W(ability("Tree Volley", slug="tiny_tree_channel"))
    W(ul_open())
    W(li("Now uses the bonus damage value of Tree Throw and bonuses from Aghanim's Shard", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Avalanche Cast Range decreased from +200 to +150", b(200, 150)))
    W(li("Level 15 Talent Avalanche Damage decreased from +100 to +90", b(100, 90)))
    W(ul_close())

    # Treant Protector
    W(hero_header("Treant Protector"))
    W(ability("Nature's Guise"))
    W(ul_open())
    W(li_formula("Cooldown changed",
                 "35s - 1s per level up", "36s - 1s per level",
                 lambda L: 35.0 + (-1.0) * L, lambda L: 36.0 + (-1.0) * L, l=True,
                 effective_unchanged=True))
    W(ul_close())
    W(subnote("Effective values are not changed"))
    W(ability("Living Armor"))
    W(ul_open())
    W(li("Mana Cost increased from 40/45/50/55 to 65/70/75/80", b([40, 45, 50, 55], [65, 70, 75, 80], l=True)))
    W(li("Max Damage Blocked decreased from 120 to 60/80/100/120", b(120, [60, 80, 100, 120])))
    W(li("Damage Block Decrease improved from 35/30/25/20 to 20", b([35, 30, 25, 20], 20)))
    W(ul_close())
    W(ability("Eyes In The Forest"))
    W(ul_open())
    W(li("Charge Restore Time increased from 55s to 135s", b(55, 135, l=True)))
    W(li("Duration increased from 300s to 360s", b(300, 360)))
    W(li("Max Charges decreased from 3 to 2", b(3, 2)))
    W(ul_close())

    # Troll Warlord
    W(hero_header("Troll Warlord"))
    W(ability("Battle Stance", slug="troll_warlord_switch_stance"))
    W(ul_open())
    W(li("Troll Warlord gains 1 armor per 30 bonus attack speed", t("NEW")))
    W(ul_close())
    W(ability("Berserker's Rage"))
    W(ul_open())
    W(li("No longer provides +3/4/5/6 Bonus Armor while in melee form", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +115 Whirling Axes Damage replaced with +1s Battle Trance Duration", t("REWORK")))
    W(li("Level 20 Talent +10 Berserker's Rage Armor replaced with +160 Whirling Axes Damage", t("REWORK")))
    W(li("Level 20 Talent +1.5s Battle Trance Duration replaced with Allies Receive Battle Trance Attack Speed", t("REWORK")))
    W(ul_close())

    # Tusk
    W(hero_header("Tusk"))
    W(ability("Bitter Chill"))
    W(ul_open())
    W(li("No longer levels with Walrus Punch!", t("REWORK")))
    W(li_formula("Attack Speed Slow rescaled",
                 "20/40/60/80", "17 + 3 per level",
                 lambda L: 80.0, lambda L: 17.0 + 3.0 * L))
    W(li("Now only affects enemy heroes", t("REWORK")))
    W(ul_close())
    W(ability("Tag Team"))
    W(ul_open())
    W(li("Now always a basic ability for Tusk", t("REWORK")))
    W(ul_close())
    W(ability("Ice Shards"))
    W(ul_open())
    W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
    W(ul_close())
    W(ability("Drinking Buddies"))
    W(ul_open())
    W(li("Aghanim's Shard: Tusk reaches out to tag an allied unit, pulling them closer. Once tagged, both Tusk and his tagged ally gain 25% bonus movement speed and 10 bonus armor for 6s. Can be put on alt-cast to only pull Tusk towards his ally with 50% reduced cast range. Cast Range: 1000. Mana Cost: 80. Cooldown: 14s", t("NEW")))
    W(li("No longer provides 20/50/80/110 bonus attack damage", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent -6s Ice Shards Cooldown replaced with -6s Snowball Cooldown", t("REWORK")))
    W(li("Level 25 Talent -8s Snowball Cooldown replaced with Ice Shards Slow by 50% and Deal 110 DPS (only affects enemies trapped inside)", t("REWORK")))
    W(ul_close())

    # Underlord
    W(hero_header("Underlord"))
    W(ability("Invading Force", slug="abyssal_underlord_raid_boss"))
    W(ul_open())
    W(li("No longer levels with Fiend's Gate", t("REWORK")))
    W(li_formula("Damage Reduction rescaled",
                 "4/6/8/10%", "3.7% + 0.3% per level",
                 lambda L: 10.0, lambda L: 3.7 + 0.3 * L))
    W(li_formula("Movement Speed bonus rescaled",
                 "11/14/17/20%", "9.5% + 0.5% per level",
                 lambda L: 20.0, lambda L: 9.5 + 0.5 * L))
    W(ul_close())
    W(ability("Firestorm"))
    W(ul_open())
    W(li("Wave Damage increased from 30/50/70/90 to 30/55/80/105", b([30, 50, 70, 90], [30, 55, 80, 105])))
    W(ul_close())
    W(ability("Atrophy Aura"))
    W(ul_open())
    W(li("Damage Reduction increased from 6/14/22/30% to 8/16/24/32%", b([6, 14, 22, 30], [8, 16, 24, 32])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Firestorm Cooldown Reduction increased from 4s to 5s", b(4, 5)))
    W(li("Level 25 Talent Fiend's Gate DPS increased from 125 to 160", b(125, 160)))
    W(ul_close())

    # Undying
    W(hero_header("Undying"))
    W(ul_open())
    W(li("Base Agility increased from 10 to 13", b(10, 13)))
    W(li("Base Armor decreased by 1", bstat_h("Undying", "ArmorPhysical", "7.40c", -1), extra=note_box(hero="Undying", field="ArmorPhysical", before_patch="7.40c")))
    W(ul_close())
    W(ability("Flesh Golem"))
    W(ul_open())
    W(li("Attacks now spawn the current level of Tombstone Zombie", t("NEW")))
    W(ul_close())

    # Vengeful Spirit
    W(hero_header("Vengeful Spirit"))
    W(ul_open())
    W(li("Base Movement Speed increased from 295 to 300", b(295, 300)))
    W(li("Base Attack Time improved from 1.7s to 1.5s", b(1.7, 1.5, l=True)))
    W(ul_close())
    W(ability("Retribution"))
    W(ul_open())
    W(li("Now also makes Vengeful Spirit to gain benefits of both melee and ranged attacks", t("NEW")))
    W(li("Now killer's icon is shown as a buff on Vengeful Spirit to know who to hate", t("MISC")))
    W(ul_close())
    W(ability("Vengeance Aura", slug="vengefulspirit_command_aura"))
    W(ul_open())
    W(li("Now provides 1.2x the bonus for Vengeful Spirit herself", b(1.0, 1.2),
         extra=inline_note("Self-bonus values: <b>12/18/24/30%</b> (vs. <b>10/15/20/25%</b> for allies)."
                           "<br>With Level 25 Talent: <b>31.2/37.2/43.2/49.2%</b> (vs. <b>26/31/36/41%</b> for allies).")))
    W(li("Aghanim's Scepter upgrade no longer refreshes ability cooldowns on activating", t("DEL")))
    W(li("Aghanim's Scepter now increases self-bonus up to 1.3x", t("NEW")))
    W(li("Aghanim's Scepter illusion is now fully affected by Vengeance Aura's bonus", t("NEW")))
    W(li("Aghanim's Scepter illusion damage taken decreased from 115% to 100%", b(115, 100)))
    W(ul_close())

    # Venomancer
    W(hero_header("Venomancer"))
    _ven_dps_pill, _ven_dps_table = scale_pill(
        "9 + 1 per level",
        lambda L: 9.0 + 1.0 * L,
        value_fmt="{:.0f}",
    )
    _ven_dur_pill, _ven_dur_table = scale_pill(
        "4.5s + 0.5s per level",
        lambda L: 4.5 + 0.5 * L,
        value_fmt="{:.1f}s",
    )
    W(ability_change(
        old=dict(
            name="Septic Shock",
            innate=True,
            desc=[
                "Passive.",
                "Venomancer's attacks deal extra magical damage based on how many debuffs the target has (only counts debuffs from Venomancer and his Plague Wards). <b>Base Damage per debuff:</b> 10%.",
                aghs_line("Increases damage per debuff from 10% to 20%. Plague Wards also deal Septic Shock damage based on their attack damage."),
            ],
        ),
        new=dict(
            name="Poison Sting",
            slug="venomancer_poison_sting",
            innate=True,
            desc=[
                "Passive.",
                "Imbues Venomancer's attacks with poison: <b>" + _ven_dps_pill + "</b> damage per second and a flat <b>10% movement slow</b>.",
                "<b>Duration:</b> " + _ven_dur_pill + ".",
            ],
            tables=[_ven_dps_table, _ven_dur_table],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Venomous Gale"))
    W(ul_open())
    W(li("Aghanim's Shard reworked: Increases cast range and projectile speed by 25%. Creates 2 Plague Wards around every enemy hero hit", t("REWORK")))
    W(ul_close())
    W(ability("Snakebite"))
    W(ul_open())
    W(li("New basic ability — Venomancer summons a Spawn of Aktok to sink its fangs into an enemy, dealing <b>40/60/80/100</b> magic damage and applying a deadly toxin which does <b>20/25/30/35</b> magical damage per second for 6 seconds. When the target attacks, they take the initial magic damage again. <b>Cast Range:</b> 600. <b>Mana Cost:</b> 70/80/90/100. <b>Cooldown:</b> 20/18/16/14s",
         t("NEW")))
    W(ul_close())
    W(ability_change(
        old=dict(
            name="Noxious Plague",
            slug="venomancer_noxious_plague",
            desc=[
                # Source: data/patchnotes_english.txt → DOTA_Patch_7_33_venomancer_venomancer_noxious_plague_2 (introducing patch) + subsequent tweak rows up to 7.40c.
                "Infects an enemy with a deadly plague that does an initial burst of damage and additional damage over time based on the unit's maximum health.",
                "Enemies in a radius around the target are slowed, with values decreasing the farther you are from the affected enemy.",
                "When the target dies or the debuff expires/is absorbed, all nearby enemies are infected with a noncommunicable version of the plague.",
                "<b>Duration:</b> 5s. <b>Initial Damage:</b> 200/300/400. <b>Max HP as Damage:</b> 3/4/5%. <b>Debuff Radius:</b> 800. <b>Min/Max Slow:</b> 15% / 50%. <b>Cooldown:</b> 100/90/80s. <b>Mana Cost:</b> 200/300/400.",
            ],
        ),
        new=dict(
            name="Noxious Plague",
            slug="venomancer_noxious_plague",
            desc=[
                # Source: data/patchnotes_english.txt → DOTA_Patch_7_41_venomancer_venomancer_noxious_plague_{2,3,8,9} verbatim + remaining stat lines derived from 7.40c baseline modified by 7.41 deltas (_5,_6,_7,_10,_11).
                "Infects an enemy with a deadly plague that does an initial burst of damage and additional damage over time based on the unit's maximum health. Initial Damage is now non-lethal.",
                "No longer has AoE effect, now affects only the host.",
                "Now when the plague spreads, it also carries all debuffs placed by Venomancer. Now spreads a second time, but all spreads after the first one deal no initial damage."
                + inline_note("Doesn't stack. Applying plague to an already plague-infected unit will deal projectile damage again, but won't affect the remaining debuff duration. Duration of carried debuffs is fixed and cannot be altered with Status Resistance or Debuff Amplification."),
                "<b>Duration:</b> 4s. <b>Initial Damage:</b> 150/200/250. <b>Max HP as Damage:</b> 2/3/4%. <b>Spread Radius:</b> 700. <b>Cooldown:</b> 100/90/80s. <b>Mana Cost:</b> 200/250/300.",
                aghs_line("Decreases cooldown by 35s. Reduces Magic Resistance of affected units by 20% and allows additional spreads to deal initial damage."),
            ],
        ),
        summary="Ability reworked.",
        tag="rework",
    ))
    W(ul_open())
    W(li("Mana Cost decreased from 200/300/400 to 200/250/300", b([200, 300, 400], [200, 250, 300], l=True)))
    W(li("Duration decreased from 5s to 4s", b(5, 4)))
    W(li("Initial Damage decreased from 200/300/400 to 150/200/250", b([200, 300, 400], [150, 200, 250])))
    W(li("Spread Radius decreased from 800 to 700", b(800, 700)))
    W(li("Max HP as damage decreased from 3/4/5% to 2/3/4%", b([3, 4, 5], [2, 3, 4])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Poison Sting Slow increased from +5% to +7%", b(5, 7)))
    W(li("Level 15 Talent -1s Plague Ward Cooldown replaced with +75 Noxious Plague Spread Radius", t("REWORK")))
    W(li("Level 20 Talent +50 Base Damage replaced with -2s Plague Ward Cooldown", t("REWORK")))
    W(li("Level 20 Talent +1% Noxious Plague Max HP Damage replaced with +40% Snakebite Damage (applies to both initial damage and damage per second)", t("REWORK")))
    W(li("Level 25 Talent Noxious Plague Aura reduces 200 Attack Speed replaced with Snakebite Undispellable", t("REWORK")))
    W(ul_close())

    # Viper
    W(hero_header("Viper"))
    W(ul_open())
    W(li("Agility gain increased from 2.7 to 2.9", b(2.7, 2.9)))
    W(li("Base Attack Speed decreased from 120 to 110", b(120, 110)))
    W(ul_close())
    W(ability("Predator"))
    W(ul_open())
    W(li("Base Damage per Missing Health Percentage increased from 0.15 to 0.25", b(0.15, 0.25)))
    W(ul_close())
    W(ability("Corrosive Skin"))
    W(ul_open())
    W(li("Aghanim's Scepter now also gradually increases Corrosive Skin's magic resistance and damage per second while he is in Nethertoxin, up to 50% increased effect after 4s", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +10% Poison Attack slow/damage replaced with +15 Corrosive Skin Damage Per Second", t("REWORK")))
    W(li("Level 15 Talent +20 Corrosive Skin Damage Per Second replaced with +15% Poison Attack Slow / Damage", t("REWORK")))
    W(li("Level 15 Talent +30 Nethertoxin Min/Max Damage replaced with +20/40 Nethertoxin Min/Max Damage", t("REWORK")))
    W(li("Level 20 Talent Predator Damage Per Missing Health increased from +0.3 to +0.35", b(0.3, 0.35)))
    W(ul_close())

    # Visage
    W(hero_header("Visage"))
    _visage_satg_pill, _visage_satg_table = scale_pill(
        "45.75s − 0.75s per level",
        lambda L: 45.75 - 0.75 * L,
        value_fmt="{:.2f}s",
    )
    W(ability_change(
        old=dict(
            name="Lurker",
            innate=True,
            desc=[
                "Passive.",
                "Visage's ability cooldowns are <b>reduced as long as he's not taking damage</b>. Gains a stack every 2s without damage taken. Each stack grants <b>2% cooldown speed</b> (max 10 stacks). Stacks fade after 2s upon taking any damage.",
            ],
        ),
        new=dict(
            name="Silent as the Grave",
            slug="visage_silent_as_the_grave",
            innate=True,
            desc=[
                "Active.",
                "Visage gains <b>flying movement and +12% movement speed for 20s</b>. Upon attacking or casting, he loses both effects, but he and his familiars gain <b>+10% attack damage for 2s</b>.",
                "<b>Mana Cost:</b> 50.  <b>Cooldown:</b> " + _visage_satg_pill + ".",
                aghs_line("Increases bonus movement speed by +12%, bonus damage by +10%, bonus damage duration by +2s, and flight duration by +10s. While flight is active, Silent as the Grave grants <b>invisibility</b> to Visage and his familiars.",
                          inline_note_text="Invisibility for Visage and each familiar are not connected."),
            ],
            tables=[_visage_satg_table],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ul_open())
    W(li("Mana Cost decreased from 115 to 50", b(115, 50, l=True)))
    W(li_formula("Cooldown changed",
                 "45s", "45.75s − 0.75s per level",
                 lambda L: 45.0, lambda L: 45.75 - 0.75 * L,
                 l=True, value_fmt="{:.2f}s"))
    W(ul_close())
    W(ability("Summon Familiars"))
    W(ul_open())
    W(li("Cooldown decreased from 130/120/110s to 120/110/100s", b([130, 120, 110], [120, 110, 100], l=True)))
    W(li("Familiar Health rescaled from 500/600/700 to 450/600/750", b([500, 600, 700], [450, 600, 750], force_overall="buff")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +6 Visage and Familiars Attack Damage replaced with +6 Visage and Familiars Base Damage", t("REWORK")))
    W(li("Level 10 Talent +4 Lurker Max Stacks replaced with -1s Soul Assumption Cooldown", t("REWORK")))
    W(li("Level 20 Talent Soul Assumption Damage Per Charge increased from +25 to +30", b(25, 30)))
    W(ul_close())

    # Void Spirit
    W(hero_header("Void Spirit"))
    W(ul_open())
    W(li("Base Damage decreased by 4", t("MISC") + bstat_h("Void Spirit", "AttackDamageMin", "7.40c", -4), extra=note_box(hero="Void Spirit", field="AttackDamageMin", before_patch="7.40c", extra_note="Damage at level 1 unchanged due to innate ability changes")))
    W(ul_close())
    W(ability_change(
        old=dict(
            name="Intrinsic Edge",
            slug="void_spirit_intrinsic_edge",
            innate=True,
            desc=[
                # Source: data/patchnotes_english.txt → DOTA_Patch_7_36_void_spirit_hero_innate_void_spirit_intrinsic_edge_{1,2,2_info} + 7.36b tweak.
                "Passive.",
                "Void Spirit gains <b>25%</b> more secondary bonuses from Primary Attributes."
                + inline_note("Health Regen from Strength, Armor from Agility, Mana Regen and Magic Resistance from Intelligence."),
            ],
        ),
        new=dict(
            name="Intrinsic Edge",
            slug="void_spirit_intrinsic_edge",
            innate=True,
            desc=[
                # Source: data/patchnotes_english.txt → DOTA_Patch_7_41_void_spirit_void_spirit_intrinsic_edge_{1,7,8,9} folded into a coherent description.
                "Passive.",
                "Void Spirit gains <b>30%</b> more secondary bonuses from Primary Attributes, and his attack damage per point of attribute is multiplicatively increased by <b>15%</b>."
                + inline_note("Health Regen from Strength, Attack Speed from Agility, Mana Regen from Intelligence. No longer provides Armor or Magic Resistance."),
            ],
        ),
        summary="Innate reworked.",
        tag="rework",
    ))
    W(ul_open())
    W(li("Attack damage per attribute multiplier increased from 0.45 to 0.5175", b(0.45, 0.5175)))
    W(li("Secondary bonuses increased from 25% to 30%", b(25, 30)))
    W(li("The result of these changes:", t("MISC"),
         extra=inline_note(
             "Damage at level 1 is unchanged at 52–56."
             "<br>Damage gain per level increased from 3.6 to 4.1 — " + b(3.6, 4.1) +
             "<br>Damage at level 30 increased from 174–178 to 192–196 — " + br(174, 178, 192, 196)
         )))
    W(ul_close())
    W(ability("Aether Remnant"))
    W(ul_open())
    W(li("Aghanim's Shard True Sight no longer reveals wards", t("NERF")))
    W(ul_close())
    W(ability("Resonant Pulse"))
    W(ul_open())
    W(li("Barrier Amount per hero hit increased from 35/50/65/80 to 50/70/90/110", b([35, 50, 65, 80], [50, 70, 90, 110])))
    W(ul_close())

    # Warlock
    W(hero_header("Warlock"))
    W(ability("Eldritch Summoning"))
    W(ul_open())
    W(li("No longer levels with Chaotic Offering", t("REWORK")))
    W(li_formula("Minor Imp Health rescaled",
                 "50/130/210/290", "5 + 15 per level",
                 lambda L: 290.0, lambda L: 5.0 + 15.0 * L))
    W(li_formula("Minor Imp Explosion Damage rescaled",
                 "25/70/115/160", "20 + 20 per 3 hero levels",
                 lambda L: 160.0, lambda L: 20.0 + 20.0 * (L // 3)))
    W(li_formula("Minor Imp movement speed rescaled",
                 "300/315/330/345", "297 + 3 per level",
                 lambda L: 345.0, lambda L: 297.0 + 3.0 * L))
    W(li("Minor Imp attack damage rescaled from 10-11/14-15/18-19/22-23/26-27 to 20-21", br(26, 27, 20, 21)))
    W(li("Aghanim's Shard now increases health of minor imps by 80 and explosion damage by 45", t("MISC"),
         extra=inline_note("Same values as before, but explicitly stated now.")))
    W(ul_close())

    # Weaver
    W(hero_header("Weaver"))
    W(ability_change(
        old=dict(
            name="Rewoven",
            innate=True,
            desc=[
                "Passive.",
                "Every time Weaver casts an ability, he gains <b>+50 attack range</b> for <b>7s</b>. Effect stacks independently per cast.",
            ],
        ),
        new=dict(
            name="Threads of Fate",
            innate=True,
            desc=[
                "Passive.",
                "After dealing damage to an enemy hero with an attack or ability, if Weaver remains within <b>700 range</b> of them for <b>1.5s</b>, he establishes a <b>Thread of Fate</b> that slows the enemy's movement by <b>100% for 0.2s</b> and ties them to Weaver.",
                "Each established thread grants <b>+10% bonus damage</b> to Weaver. Threads last up to <b>6s</b> and break if the distance becomes longer than <b>900</b>.",
                "If the enemy dies with a Thread of Fate established, the thread's bonuses linger for an additional <b>5s</b>."
                + inline_note("Effects linger even if the enemy dies just as the thread is about to be established."),
            ],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +60 Shukuchi Damage replaced with +50 Shukuchi Movement Speed", t("REWORK")))
    W(li("Level 15 Talent +20 Mana Break replaced with +90 Shukuchi Damage", t("REWORK")))
    W(li("Level 20 Talent Bonus Damage on Geminate decreased from +70 to +60", b(70, 60)))
    W(ul_close())

    # Windranger
    W(hero_header("Windranger"))
    W(ul_open())
    W(li("Base Movement Speed decreased from 290 to 285", b(290, 285)))
    W(ul_close())
    W(ability_change(
        old=dict(
            name="Easy Breezy",
            innate=True,
            desc=[
                "Passive.",
                "Windranger's movement speed <b>cannot drop below 240</b>. Max Movement Speed cap increased from 550 to <b>600</b>.",
            ],
        ),
        new=dict(
            name="Tailwind",
            slug="windrunner_tailwind",
            innate=True,
            desc=[
                "Passive.",
                "Using an ability conjures a stacking <b>Tailwind</b> that gives Windranger a brief burst of movement speed. The bonus starts gradually fading halfway through the duration.",
                "<b>Movement Speed Bonus per stack:</b> 35%.  <b>Duration:</b> 2s.",
                "Passively increases Windranger's <b>max movement speed cap to 600</b>.",
                aghs_line("Attacks also grant Tailwind effect. Increases Tailwind duration to 3s and makes it undispellable."),
            ],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Windrun"))
    W(ul_open())
    W(li("Movement Speed Bonus decreased from 60% to 50%", b(60, 50)))
    W(li("Cooldown decreased from 15/14/13/12s to 14/13/12/11s", b([15, 14, 13, 12], [14, 13, 12, 11], l=True)))
    W(li("No longer upgraded with Aghanim's Scepter", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +4 All Attributes replaced with +0.75s Windrun Duration", t("REWORK")))
    W(li("Level 15 Talent -2s Windrun Cooldown replaced with +40 Tailwind Max Movespeed", t("REWORK")))
    W(li("Level 25 Talent Windrun Cannot be Dispelled replaced with Powershot Executes Enemy Heroes Under 15% Max HP (Execute Threshold ranges from 10-15% Max HP Based on channel time and reduces with each unit the arrow comes through)", t("REWORK")))
    W(ul_close())

    # Winter Wyvern
    W(hero_header("Winter Wyvern"))
    W(ability_change(
        old=dict(
            name="Eldwurm Scholar",
            innate=True,
            desc=[
                "Passive.",
                "When an allied hero picks up a <b>Wisdom Rune</b>, the 3 heroes that wouldn't benefit from it gain <b>20% of the experience</b> instead.",
            ],
        ),
        new=dict(
            name="Eldwurm's Edda",
            slug="winter_wyvern_eldwurms_edda",
            innate=True,
            desc=[
                "Item-based.",
                "Winter Wyvern starts the game with the <b>Eldwurm's Edda</b> item. After <b>10 minutes</b> it can be consumed, increasing the <b>current and maximum level of one basic ability by 1</b>.",
                "Also increases Winter Wyvern's <b>Intelligence by 25%</b> of its base value at the time of consumption.",
                "<b>Level-5 values</b> are automatically calculated by applying 50% of the difference in all values between levels 3 and 4 (except mana cost — kept the same as level 4).",
            ],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Arctic Burn"))
    W(ul_open())
    W(li("No longer has a one debuff per cast restriction on enemy heroes", t("BUFF")))
    W(li("Burn Duration decreased from 5s to 3s", b(5, 3)))
    W(li("Movement Slow decreased from 16/24/32/40% to 15/20/25/30%", b([16, 24, 32, 40], [15, 20, 25, 30])))
    W(ul_close())
    W(ability("Cold Embrace"))
    W(ul_open())
    W(li("Aghanim's Shard reworked: Decreases cooldown by 4s. Allied units gain 60% bonus attack damage for 6s when emerging from the icy cocoon", t("REWORK")))
    W(ul_close())
    W(ability("Winter's Curse"))
    W(ul_open())
    W(li("Attack Speed rescaled from 65 to 50/65/80", b(65, [50, 65, 80])))
    W(li("Maximum Duration rescaled from 4/5.5/7s to 6s", b([4, 5.5, 7], 6)))
    W(li("Bonus Duration per hero decreased from 2s to 1.5s", b(2, 1.5)))
    W(li("Bonus duration per hero can now be applied after the cast if an enemy hero becomes affected", t("NEW")))
    W(ul_close())
    W(subnote("Still can't be longer than the maximum duration"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Splinter Blast Shatter Radius decreased from +250 to +175", b(250, 175)))
    W(li("Level 20 Talent Arctic Burn Slow decreased from +17% to +15%", b(17, 15)))
    W(ul_close())

    # Witch Doctor
    W(hero_header("Witch Doctor"))
    W(ability("Death Ward"))
    W(ul_open())
    W(li("Attack Range increased from 600 to 600/625/650", b(600, [600, 625, 650])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +2 Paralyzing Cask bounces replaced with -3s Paralyzing Cask Cooldown", t("REWORK")))
    W(li("Level 20 Talent +75 Death Ward Attack Range replaced with Maledict bursts deal 75% damage in a 800 AoE (each burst sends projectiles that deal 75% of its damage at all enemy units within 800 range)", t("REWORK")))
    W(li("Level 25 Talent -6s Paralyzing Cask Cooldown replaced with +6 Paralyzing Cask Bounces", t("REWORK")))
    W(ul_close())

    # Wraith King
    W(hero_header("Wraith King"))
    W(ul_open())
    W(li("Base Armor decreased by 1", bstat_h("Wraith King", "ArmorPhysical", "7.40c", -1), extra=note_box(hero="Wraith King", field="ArmorPhysical", before_patch="7.40c")))
    W(ul_close())
    W(ability("Vampiric Spirit"))
    W(ul_open())
    W(li("No longer levels with Reincarnation", t("REWORK")))
    W(li_formula("Lifesteal changed",
                 "10/20/30/40%", "14% + 1% per level",
                 lambda L: 40.0, lambda L: 14.0 + 1.0 * L))
    W(li_formula("Wraith Duration changed",
                 "3.5/4/4.5/5s", "4.25s + 0.25s per 6 levels",
                 lambda L: 5.0, lambda L: 4.25 + 0.25 * (L // 6),
                 value_fmt="{:.2f}s",
                 inline_note_text="Up to 5.5s at level 30. Also increased by 1s with Aghanim's Scepter."))
    W(li("Bonus Attack Speed rescaled from 30/45/60/75 to 55", b([30, 45, 60, 75], 55)))
    W(li("Bonus Move Speed rescaled from 10/15/20/25% to 20%", b([10, 15, 20, 25], 20)))
    W(ul_close())
    W(ability("Bone Guard"))
    W(ul_open())
    W(li("Now always a basic ability for Wraith King", t("REWORK")))
    W(li("Skeleton movespeed increased from 340 to 350", b(340, 350)))
    W(ul_close())
    W(ability("Mortal Strike"))
    W(ul_open())
    W(li("Aghanim's Shard reworked: Critical strikes curse their target, dealing 75% of the damage dealt again after a 3 second delay. Vampiric Spirit's lifesteal applies to the curse damage", t("REWORK")))
    W(ul_close())
    W(ability("Reincarnation"))
    W(ul_open())
    W(li("Mana Cost decreased from 225 to 220/110/0", b(225, [220, 110, 0], l=True)))
    W(li("Now spawns 2/3/4 per enemy hero within slow radius", t("NEW")))
    W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
    W(ul_close())

    # Zeus
    W(hero_header("Zeus"))
    W(ul_open())
    W(li("Base Strength increased from 19 to 21", b(19, 21)))
    W(li("Base Damage increased by 1–3", bstat_h("Zeus", "AttackDamageMin", "7.40c", 1),
         extra=note_box(hero="Zeus", field="AttackDamageMin", before_patch="7.40c") + inline_note("Damage spread increased from 8 to 10 — " + b(8, 10))))
    W(li("Damage at level 1 increased from 52–60 to 53–63", br(52, 60, 53, 63)))
    W(li("Base Movement Speed decreased from 315 to 305", b(315, 305)))
    W(li("Base Armor decreased by 1", bstat_h("Zeus", "ArmorPhysical", "7.40c", -1), extra=note_box(hero="Zeus", field="ArmorPhysical", before_patch="7.40c")))
    W(ul_close())
    W(ability("Static Field"))
    W(ul_open())
    W(li("No longer levels with Thundergod's Wrath", t("REWORK")))
    W(li_formula("Damage changed",
                 "2.5/3/3.5/4%", "3.45% + 0.05% per level",
                 lambda L: 4.0, lambda L: 3.45 + 0.05 * L))
    W(ul_close())
    W(ability("Arc Lightning"))
    W(ul_open())
    W(li("Mana Cost rescaled from 75/85/95/105 to 85/90/95/100", b([75, 85, 95, 105], [85, 90, 95, 100], l=True)))
    W(li("Base Damage increased from 90/120/150/180 to 105/130/155/180", b([90, 120, 150, 180], [105, 130, 155, 180])))
    W(ul_close())
    W(ability("Lightning Bolt"))
    W(ul_open())
    W(li("Vision and True Sight radius increased from 500 to 600", b(500, 600)))
    W(ul_close())
    W(ability("Thundergod's Wrath"))
    W(ul_open())
    W(li("Now applies the True Sight before the damage and strikes even untargetable and still invisible enemies", t("NEW")))
    W(ul_close())
    W(subnote("It used to simply reveal invisible heroes without dealing damage to them. Now it will work similarly to Lightning Bolt, dealing damage even to units affected by Smoke of Deceit, Dark Willow's Shadow Realm, Phantom Assassin's Blur, Slark's Shadow Dance or Depth Shroud, etc."))
    W(ul_open())
    W(li("Vision and True Sight radius increased from 500 to 600", b(500, 600)))
    W(ul_close())
    W(ability("Nimbus", slug="zuus_cloud"))
    W(ul_open())
    W(li("Damage source changed from Nimbus to the caster", t("REWORK")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent -0.4s Arc Lightning Cooldown replaced with -20% Arc Lightning Mana Cost/Cooldown", t("REWORK")))
    W(li("Level 25 Talent +2% Static Field Damage replaced with 3 Heavenly Jump Charges", t("REWORK")))
    W(ul_close())

    write_footer()
    save_html('patches/7.41.html')

