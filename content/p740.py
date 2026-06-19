import html as _html
from patch.api import *

_NC_CDN = "../icons/units/npc_dota_neutral_"

def build():
    write_head("7.40", "15.12.2025")

    # ===== GENERAL UPDATES =====
    W(section("General Updates"))

    # ---- Captains Mode ----
    W(plain_header("Captains Mode"))
    W(ul_open())
    W(li("Changed order of the first and the third ban phases", t("REWORK")))
    W(ul_close())
    # Full Captains Mode draft (24 steps), Old over New, rendered as a token board
    # (see cm_draft / docs/captains-mode.md). Structure Ban7-Pick2-Ban3-Pick6-Ban4-Pick2
    # (esports.gg/gosugamers, 7.34). Only the 1st + 3rd ban phases changed in 7.40;
    # bans 3-2-2 / 4-1-2 first/second-pick team, picks alternate 1-3-1.
    # F/S = ban by first/second-pick team; f/s = pick by first/second-pick team.
    W(cm_draft(
        ("Ban 1",  "FSSFSSF", "FFSSFSS"),   # CHANGED in 7.40
        ("Pick 1", "fs",      "fs"),
        ("Ban 2",  "FFS",     "FFS"),
        ("Pick 2", "sffssf",  "sffssf"),     # snake: 2nd,1st,1st,2nd,2nd,1st pick team
        ("Ban 3",  "FSSF",    "FSFS"),       # CHANGED in 7.40
        ("Pick 3", "fs",      "fs"),
    ))

    W(plain_header("General Changes"))
    # One ul so the tag-order sorter ranks across all three (NEW → NEW → REWORK);
    # they were split across two uls before, which left REWORK between the two NEWs.
    W(ul_open())
    W(li("All Facets that used to have 6 All Attributes bonuses now have 7 bonuses again " + info_tip(
            "Batrider's Arsonist", "Magnus' Diminishing Return", "Meepo's More Meepo",
            "Monkey King's Simian Stride", "Night Stalker's Voidbringer", "Silencer's Synaptic Split",
            header="Affected facets:"), t("BUFF")))
    W(li("Tier 4 Towers now have a Barracks Reinforcement buff. Each allied barracks that has not been destroyed provides +4 armor to both Tier 4 towers", t("NEW"), extra=inline_note("Bonus is for each individual building, totaling in +24 Armor for 6 Barracks")))
    W(li("Talents no longer require a skill point to level", t("REWORK"), extra=inline_note("Now talents are learned by using their own talent points available at levels 10, 15, 20, 25, 27, 28, 29, and 30. This results in all +2 All Attributes bonuses skilled by level 22")))
    W(ul_close())
    W(formula_change(
        "Assist Gold Formula",
        "60 + ( ( VictimNetworth * 0.037 ) / NumHeroes )",
        "15 + ( ( 50 + ( VictimNetworth * 0.037 ) ) / NumHeroes )",
        vary=("NumHeroes", "Heroes", [1, 2, 3, 4, 5]),
        fixed={"VictimNetworth": 10000},
        unit="Gold",
    ))
    W(ul_open())
    W(li("Melee Creep: Gold Bounty now increases by 1 per lane creep upgrade interval (every 7:30)", t("NEW")))
    W(li("Flagbearer Creep: Gold Bounty now increases by 1 per lane creep upgrade interval", t("NEW")))
    W(li("Flagbearer Creep: AoE Bounty Radius increased from 1200 to 1500", b(1200, 1500)))
    W(li("Flagbearer Creep: When killed by a player controlled unit, the Flagbearer Creep always grants Bonus Bounty to the killer's hero regardless of the hero's proximity to the Flagbearer Creep", t("REWORK")))
    W(li("Flagbearer Creep: Bonus Gold from killing Flagbearers is now classified as creep gold instead of ability gold", t("QoL"), extra=inline_note("Has no gameplay effect, but makes a post game gold breakdown more accurate")))
    W(li("Flagbearer Creep: Inspiration Aura no longer affects heroes", t("DEL")))
    W(li("Flagbearer Creep: Inspiration Aura now also provides a magic resistance bonus to affected creeps starting with 0% and improving by 4% with every lane creep upgrade interval, up to a maximum of 15 upgrades", t("NEW")))
    W(ul_close())
    W(ul_open())
    W(li_formula("Courier respawn time decreased",
                 "60s + 6s per Hero Level", "45s + 5s per Hero Level",
                 lambda L: 60 + 6 * L, lambda L: 45 + 5 * L, l=True))
    W(li("Courier no longer has a 15% movement speed penalty while carrying a Clarity, Enchanted Mango, Faerie Fire, Healing Salve, or Tango", t("BUFF")))
    W(li("Flying Courier will now go to a more obscure shopping area within range of the Secret Shop when using Go To Secret Shop", t("QoL")))
    W(ul_close())
    W(ul_open())
    W(li("All illusions now have 800 daytime vision and 400 nighttime vision", b([1800, 800], [800, 400], slash=True),
         extra=inline_note("Previously inherited the hero's full vision (typically 1800 daytime / 800 nighttime)")))
    W(ul_close())

    W(plain_header("Map Objectives"))
    W(subgroup("Roshan"))
    W(ul_open())
    W(li("Roshan is no longer considered a hero for Lifesteal mechanics. As a result, Physical Lifesteal from damage to Roshan is reduced by 40%, and Spell Lifesteal from damage to Roshan is reduced by 80%", t("NEW")))
    W(li("Roar of Retribution: Disarm debuff is no longer dispellable", t("NEW")))
    W(li("Slam: No longer has double duration against creeps", t("DEL")))
    W(li("Slam: Now deals double damage to creeps", t("NEW")))
    W(ul_close())
    W(subgroup("Tormentor"))
    W(ul_open())
    W(li("Added a Tormentor Timer near the minimap. Functions similarly to the Roshan Timer. Can be pinged to communicate the current state of Tormentor", t("QoL")))
    W(li("Pinging Tormentor's location in world will trigger the same ping as the timer (same behavior the Roshan Timer has)", t("QoL")))
    W(li("The minimap now only has one Tormentor icon and reflects where Tormentor is or will spawn", t("QoL")))
    W(li("The Shining: Now only starts dealing damage to the surrounding enemies when attacked/damaged", t("REWORK")))
    W(ul_close())
    W(subgroup("Runes"))
    W(ul_open())
    W(li("Bounty Rune: Now grants gold based on when it was created, not when it was activated", t("REWORK")))
    W(li("Haste Rune: Duration no longer increases by 3s per rune cycle, and is always 22s now", t("DEL")))
    W(li("Invisibility Rune: No longer grants incoming damage reduction", t("DEL")))
    W(ul_close())

    W(plain_header("Terrain Changes", terrain_link="7.40"))
    # One ul for the whole category so the tag-order sorter ranks across all rows
    # (NEW → BUFF → NERF → DEL → MISC); the source paragraph splits were arbitrary.
    W(ul_open())
    W(li("Extended the streams into both Radiant and Dire bases and added defender's gate to the outside of the respective safe lanes where the stream flows", t("MISC")))
    W(li("Removed some trees inside the base near the new safelane defender's gate positions", t("MISC")))
    W(li("The Hard camp nearest to Tier 3 towers where the streams used to start has been demoted to a 'medium' camp", t("NERF")))
    W(li("Moved the safelane medium amphibian neutral camp closest to the Tier 2 tower up the stream, slightly closer to the respective bases", t("MISC")))
    W(li("Lowered the Wisdom Shrine areas to low ground, compared to the respective offlanes, filled them with water and connected to the water areas by the Tier 1 towers", t("MISC")))
    W(li("Moved Wisdom Shrines and Watchers to the low ground and slightly closer to the Tier 1 towers. These Watchers now have vision over the shrines at night", t("MISC")))
    W(li("Hard camps nearest to Wisdom Shrines have been moved slightly back towards the bases", t("MISC")))
    W(li("Changed the 'bridges' to actual bridges", t("MISC")))
    W(li("Slightly expanded the entrance to the bridge by the Lotus pools and adjusted the area within the nearby water areas", t("MISC")))
    W(li("The Hard camp in the 'triangle' has been demoted to a 'medium' camp", t("NERF")))
    W(li("Twin Gate mana cost decreased from 75 to 30", b(75, 30, l=True)))
    W(li("Twin Gates now refund the mana cost if the teleporting channel was interrupted", t("NEW")))
    W(li("Cleared up some areas around the Tormentor locations", t("MISC")))
    W(li("The watchers nearest to the mid-lane and near the small water camps south/north of the tier 1 tower have been removed", t("DEL")))
    W(li("The watchers in the primary jungles have been repositioned from stairs near the small camp to the cliff above the bounty runes", t("MISC")))
    W(li("Added additional blocks preventing flying movement around the edges of the map (e.g. the highground areas behind the Tormentors will no longer be accessible by Batrider during Firefly)", t("NEW")))
    W(li("Watcher night vision range decreased from 800 to 450", b(800, 450)))
    W(li("Watcher capture time decreased from 1.5s to 1s", b(1.5, 1, l=True)))
    W(li("Defender's Gate vision radius increased from 525 to 700", b(525, 700)))
    W(li("Defender's Gate will now show their vision radius when holding ALT (similarly to Wards, Watchers, etc.)", t("QoL")))
    W(li("Removed a tree between Dire Safelane Tier 1 tower and the small pull camp", t("MISC")))
    W(li("Very slightly adjusted the paths and spawn points of the Radiant Offlane lane creeps, and the position of the Radiant Offlane Tier 2 tower. This results in creeps pathing to the right of the tier 2 tower instead of sometimes splitting up to go around it", t("MISC")))
    W(li("Radiant Secret Shop trigger area moved slightly towards the radiant Tier 1 tower and more centered around the shopkeeper", t("MISC")))
    W(ul_close())

    W(plain_header("Invulnerability Targeting"))
    W(section_intro("Invulnerability targeting rules have been updated — most items and abilities that previously could target and/or affect invulnerable units no longer do so."))
    W(subgroup("Items"))
    W(ul_open())
    W(li("Nullifier's Nullify can no longer target invulnerable units", t("DEL")))
    W(ul_close())
    W(subgroup("Neutral Creeps"))
    W(ul_open())
    W(li("Satyr Banisher's Purge can no longer target invulnerable units", t("DEL")))
    W(ul_close())
    W(subgroup("Heroes"))
    W(ul_open())
    W(li("Dark Seer's Vacuum no longer affects invulnerable units", t("DEL")))
    W(li("Naga Siren's Ensnare can no longer target invulnerable units unless this invulnerability is provided by Song of the Siren", t("REWORK")))
    W(li("Ogre Magi's Bloodlust can no longer target invulnerable units", t("DEL"), extra=inline_note("Can still target invulnerable buildings (i.e. Tier 2-4 towers when the previous ones are not destroyed)")))
    W(li("Oracle's Fortune's End can no longer target invulnerable units, but does affect invulnerable units in the radius", t("DEL")))
    W(li("Shadow Demon's Demonic Purge can no longer target invulnerable units", t("DEL")))
    W(li("Shadow Demon's Demonic Cleanse can no longer target invulnerable units", t("DEL")))
    W(li("Sniper's Assassinate can no longer target invulnerable units", t("DEL")))
    W(li("Sven's Storm Hammer with Aghanim's Scepter can no longer target invulnerable units, but does affect invulnerable units in the radius", t("DEL")))
    W(li("Vengeful Spirit's Nether Swap can no longer target invulnerable units", t("DEL")))
    W(ul_close())
    W(subgroup("Cyclone"))
    W(section_intro("Since Cyclone effects also make the unit invulnerable, all changes above apply to them as well — these are the special cases:"))
    W(ul_open())
    _cyclone_proj_note = "Also dispels Cyclone if the spell projectile was launched (or started channeling) before the target got Cycloned"
    W(li("Nullifier's Nullify will dispel Cyclone off the target immediately if Cyclone was cast on a unit already affected by the Nullify debuff", t("MISC"), extra=inline_note(_cyclone_proj_note)))
    W(li("Oracle's Fortune's End cannot target Cycloned units, but will dispel Cyclone off the units in AoE around the target", t("MISC"), extra=inline_note(_cyclone_proj_note)))
    W(li("Sven's Storm Hammer with Aghanim's Scepter cannot target Cycloned units, but will dispel Cyclone off the units in AoE around the target", t("MISC"), extra=inline_note(_cyclone_proj_note)))
    W(ul_close())

    # ===== NEUTRAL CREEP UPDATES =====
    W(section("Neutral Creep Updates"))

    W(unit_header("Satyr Mindstealer", _NC_CDN + "satyr_soulstealer.png"))
    W(ability("Mana Burn", icon_url="../icons/abilities/satyr_soulstealer_mana_burn.png"))
    W(ul_open())
    W(li("Target's intelligence multiplier decreased from 2/2.5/3/4x to 1/1.5/2/2.5x",
         b([2, 2.5, 3, 4], [1, 1.5, 2, 2.5])))
    W(ul_close())

    W(unit_header("Satyr Banisher", _NC_CDN + "satyr_trickster.png"))
    W(ability("Purge", icon_url="../icons/abilities/satyr_trickster_purge.png"))
    W(ul_open())
    W(li("Can no longer target invulnerable units", t("DEL")))
    W(ul_close())

    # ===== ITEM UPDATES =====
    W(section("Item Updates"))
    W(item_header("Clarity"))
    W(ul_open())
    W(li("Initial and maximum stock increased from 4 to 5", b(4, 5)))
    W(li("Cost increased from 50 to 60", b(50, 60, l=True)))
    W(ul_close())
    W(item_header("Healing Salve"))
    W(ul_open())
    W(li("Initial and maximum stock increased from 4 to 5", b(4, 5)))
    W(li("No longer has half duration when cast on an ally", t("DEL")))
    W(li("Now heals for half the amount per second when cast on an ally", t("NEW")))
    W(ul_close())
    W(item_header("Iron Branch"))
    W(ul_open())
    W(li("Cost increased from 50 to 55", b(50, 55, l=True)))
    W(ul_close())
    W(item_header("Observer Ward"))
    W(ul_open())
    W(li("Observer Wards cannot be planted within 300 units of another Observer Ward from the same team that has been planted within the last second", t("QoL")))
    W(li("Plant no longer increased by cast range increases", t("DEL")))
    W(ul_close())
    W(item_header("Sentry Ward"))
    W(ul_open())
    W(li("Sentry Wards cannot be planted within 300 units of another Sentry Ward from the same team that has been planted within the last second", t("QoL")))
    W(li("Plant no longer increased by cast range increases", t("DEL")))
    W(ul_close())
    W(item_header("Smoke of Deceit"))
    W(ul_open())
    W(li("Can be used directly from the backpack", t("QoL")))
    W(li("Has no cooldown when entering the main inventory from the backpack", t("QoL")))
    W(ul_close())
    W(item_header("Tango"))
    W(ul_open())
    W(li("Initial and maximum stock increased from 8 to 10", b(8, 10)))
    W(li("Shared Tango now heals for half the amount per second", t("NEW")))
    W(ul_close())
    W(item_header("Roshan's Banner"))
    W(ul_open())
    W(li("Now upgrades with each subsequent drop", t("NEW"), extra=inline_note("Effect radius rescaled from 650 to 600/900/1200 " + b(650, [600, 900, 1200]))))
    W(li("Hits to kill increased from 6 to 6/8/10", b(6, [6, 8, 10])))
    W(ul_close())
    W(item_header("Ghost Scepter"))
    W(ul_open())
    W(li("Ghost Form magic damage vulnerability decreased from 40% to 30%", b(40, 30, l=True)))
    W(ul_close())
    W(item_header("Ring of Tarrasque"))
    W(ul_open())
    W(li("Cost decreased from 1800 to 1700", b(1800, 1700, l=True)))
    W(ul_close())
    W(item_header("Shadow Amulet"))
    W(ul_open())
    W(li("Cost decreased from 1000 to 900", b(1000, 900, l=True)))
    W(ul_close())
    W(item_header("Tiara of Selemene"))
    W(ul_open())
    W(li("Cost decreased from 1800 to 1700", b(1800, 1700, l=True)))
    W(ul_close())
    W(item_header("Voodoo Mask"))
    W(ul_open())
    W(li("Cost decreased from 700 to 650", b(700, 650, l=True)))
    W(ul_close())
    W(item_header("Bloodstone"))
    W(ul_open())
    W(li("Total cost decreased from 4400 to 4350 due to Voodoo Mask cost decrease", b(4400, 4350, l=True)))
    W(li("Spell Lifesteal bonus increased from +20% to +25%", b(20, 25)))
    W(li("Bloodpact spell lifesteal multiplier decreased from 4x to 3x", b(4, 3)))
    W(ul_close())
    W(item_header("Boots of Bearing", changed=True))
    W(auto_components_change("Boots of Bearing", "7.40"))
    W(properties_change(
        old=[("BUFF", "+15 Health Regen")],
        new=[("",    "+18 Health Regen", b(15, 18))]))
    W(item_header("Crimson Guard"))
    W(ul_open())
    W(li("Guard buff is no longer dispellable", t("NEW")))
    W(ul_close())
    W(item_header("Dagon"))
    W(ul_open())
    W(li("Total cost decreased from 2850 to 2800 due to Voodoo Mask cost decrease", b(2850, 2800, l=True), extra=inline_note("Total cost for all levels decreased from 2850/4000/5150/6300/7450 to 2800/3950/5100/6250/7400 " + b([2850,4000,5150,6300,7450], [2800,3950,5100,6250,7400], l=True))))
    W(ul_close())
    W(item_header("Diffusal Blade"))
    W(ul_open())
    W(li("Manabreak no longer applied by illusions", t("DEL")))
    W(ul_close())
    W(item_header("Disperser"))
    W(ul_open())
    W(li("Suppress now applies basic dispel to any target", t("NEW")))
    W(li("Manabreak no longer applied by illusions", t("DEL")))
    W(ul_close())
    W(item_header("Ethereal Blade", changed=True))
    W(auto_components_change("Ethereal Blade", "7.40"))
    W(properties_change(
        old=[("BUFF", "+8 All Attributes"),
             ("DEL",  "+300 Mana"),
             ("DEL",  "+3 Mana Regen"),
             ("DEL",  "+250 Cast Range")],
        new=[("",    "+24 All Attributes", b(8, 24))]))
    W(ul_open())
    W(li("Recipe cost decreased from 1600 to 900. Total cost decreased from 5375 to 5200", b(1600, 900, l=True)))
    W(li("Ether Blast magic damage vulnerability decreased from 40% to 30%", b(40, 30)))
    W(li("Ether Blast attributes as damage changed from (1.5x the target's primary attribute) to (1x the sum of the caster's attributes)", t("REWORK")))
    W(ul_close())
    W(item_header("Glimmer Cape"))
    W(ul_open())
    W(li("Recipe cost increased from 350 to 450", t("MISC") + b(350, 450, l=True), extra=inline_note("Total cost unchanged at 2150 due to Shadow Amulet cost decrease")))
    W(ul_close())
    W(item_header("Guardian Greaves", changed=True))
    W(auto_components_change("Guardian Greaves", "7.40"))
    W(properties_change(
        old=[("BUFF", "+4 Armor")],
        new=[("",    "+5 Armor", b(4, 5))]))
    W(ul_open())
    W(li("Recipe cost decreased from 1450 to 1125. Total cost decreased from 5050 to 4300", b(1450, 1125, l=True)))
    W(li("Guardian Aura no longer provides armor", t("DEL")))
    W(li("Guardian Aura no longer provides additional bonuses when below 25% health to anyone but the wearer", t("DEL")))
    W(li("Guardian Aura no longer provides increased armor and increased mana regeneration when below 25% health", t("DEL"), extra=inline_note("Still provides bonus health regeneration to the wearer when below 25% health")))
    W(ul_close())
    W(item_header("Hand of Midas"))
    W(ul_open())
    W(li("Transmute no longer has an experience multiplier", t("DEL")))
    W(li("Transmute charge restore time decreased from 110s to 90s", b(110, 90, l=True)))
    W(ul_close())
    W(item_header("Heart of Tarrasque"))
    W(ul_open())
    W(li("Total cost decreased from 5200 to 5100 due to Ring of Tarrasque cost decrease", b(5200, 5100, l=True)))
    W(li("Max Health Regen bonus decreased from +1.4% to +1%", b(1.4, 1)))
    W(li("Now also provides passive Behemoth's Blood", t("NEW")))
    W(li("Passive: Wearer's health regen is increased by 1.5% of missing health", "",
         extra=inline_note("Multiple instances of Behemoth's Blood don't stack")))
    W(ul_close())
    W(item_header("Heaven's Halberd"))
    W(ul_open())
    W(li("Disarm is now only dispellable by strong dispels", t("BUFF"), extra=inline_note("Still does not pierce debuff immunity")))
    W(li("Disarm no longer has separate disarm durations for melee and ranged targets. Duration is always 3 seconds", t("NERF")))
    W(li("Disarm cooldown increased from 18s to 20s", b(18, 20, l=True)))
    W(ul_close())
    W(item_header("Helm of the Dominator"))
    W(ul_open())
    W(li("Dominate gold and experience bounty when dominating a creep decreased from 100% to 50%", b(100, 50)))
    W(ul_close())
    W(item_header("Holy Locket", changed=True))
    W(auto_components_change("Holy Locket", "7.40"))
    W(properties_change(
        old=[("NERF", "+9 All Attributes")],
        new=[("",    "+7 All Attributes", b(9, 7))]))
    W(ul_open())
    W(li("Recipe cost increased from 800 to 1340", t("MISC") + b(800, 1340, l=True), extra=inline_note("Total cost unchanged at 2250 due to Iron Branch cost increase")))
    W(li("Energy Charge automatic charge gain time increased from 8s to 10s", b(8, 10, l=True)))
    W(li("Energy Charge max charges increased from 20 to 25", b(20, 25)))
    W(li("Energy Charge cast range increased from 500 to 600", b(500, 600)))
    W(li("Energy Charge mana restore per charge decreased from 17 to 15", b(17, 15)))
    W(li("Energy Charge active now also increases the target's incoming Healing Amplification by 10% for 4s", t("NEW"), extra=inline_note("This occurs before the Energy Charge heal")))
    W(ul_close())
    W(item_header("Khanda", changed=True))
    W(auto_components_change("Khanda", "7.40"))
    W(properties_change(
        old=[("NERF", "+8 Mana Regen"),
             ("BUFF", "+200 Health"),
             ("BUFF", "+200 Mana")],
        new=[("",    "+3 Mana Regen",       b(8, 3)),
             ("",    "+450 Health",         b(200, 450)),
             ("",    "+450 Mana",           b(200, 450)),
             ("NEW", "+7 Health Regeneration")]))
    W(item_header("Magic Wand"))
    W(ul_open())
    W(li("Total cost increased from 450 to 460 due to Iron Branch cost increase", b(450, 460, l=True)))
    W(ul_close())
    W(item_header("Mekansm"))
    W(ul_open())
    W(li("Armor bonus increased from +4 to +5", b(4, 5)))
    W(ul_close())
    W(item_header("Meteor Hammer"))
    W(ul_open())
    W(li("Meteor Hammer stun duration increased from 0.5s to 0.75s", b(0.5, 0.75)))
    W(ul_close())
    W(item_header("Nullifier"))
    W(ul_open())
    W(li("Nullify can no longer target invulnerable units", t("DEL")))
    W(ul_close())
    W(item_header("Octarine Core", changed=True))
    W(auto_components_change("Octarine Core", "7.40"))
    W(ul_open())
    W(li("Total cost increased from 4800 to 4900 due to Tiara of Selemene cost decrease", b(4800, 4900, l=True)))
    W(li("Can no longer be disassembled", t("DEL")))
    W(ul_close())
    W(item_header("Pavise"))
    W(ul_open())
    W(li("Armor bonus increased from +2 to +3", b(2, 3)))
    W(ul_close())
    W(item_header("Perseverance"))
    W(ul_open())
    W(li("Can now be disassembled", t("NEW")))
    W(ul_close())
    W(item_header("Pipe of Insight"))
    W(ul_open())
    W(li("Recipe cost increased from 700 to 800", t("MISC") + b(700, 800, l=True), extra=inline_note("Total cost unchanged at 3725 due to Ring of Tarrasque cost decrease")))
    W(ul_close())
    W(item_header("Phylactery", changed=True))
    W(auto_components_change("Phylactery", "7.40"))
    W(properties_change(
        old=[("DEL", "+200 Health"),
             ("DEL", "+200 Mana")],
        new=[("NEW", "+6.5 Health Regen"),
             ("NEW", "+2.5 Mana Regen")]))
    W(ul_open())
    W(li("Recipe cost decreased from 300 to 200 " + b(300, 200, l=True) + ". Total cost increased from 2500 to 2600", b(2500, 2600, l=True)))
    W(ul_close())
    W(item_header("Radiance"))
    W(ul_open())
    W(li("Evasion bonus increased from +15% to +25%", b(15, 25)))
    W(li("Burn no longer causes enemies to miss 15% of their attacks", t("DEL")))
    W(li("Burn no longer does extra damage to illusions", t("DEL")))
    W(ul_close())
    W(item_header("Refresher Orb", changed=True))
    W(auto_components_change("Refresher Orb", "7.40"))
    W(properties_change(
        old=[("DEL",  "+10 Damage"),
             ("NERF", "+18 Health Regen"),
             ("NERF", "+8 Mana Regen")],
        new=[("",    "+12 Health Regen", b(18, 12)),
             ("",    "+6 Mana Regen",    b(8, 6))]))
    W(ul_open())
    W(li("Recipe cost increased from 200 to 1600", t("MISC") + b(200, 1600, l=True), extra=inline_note("Total cost unchanged at 5000 due to Ring of Tarrasque and Tiara of Selemene cost decrease")))
    W(ul_close())
    W(item_header("Revenant's Brooch"))
    W(ul_open())
    W(li("Recipe cost increased from 600 to 650", t("MISC") + b(600, 650, l=True), extra=inline_note("Total cost unchanged at 3300 due to Voodoo Mask cost decrease")))
    W(ul_close())
    W(item_header("Scythe of Vyse"))
    W(ul_open())
    W(li("Recipe cost increased from 600 to 700", t("MISC") + b(600, 700, l=True), extra=inline_note("Total cost unchanged at 5200 due to Tiara of Selemene cost decrease")))
    W(ul_close())
    W(item_header("Shadow Blade"))
    W(ul_open())
    W(li("Total cost decreased from 3350 to 3250 due to Shadow Amulet cost decrease", b(3350, 3250, l=True)))
    W(ul_close())
    W(item_header("Shiva's Guard"))
    W(ul_open())
    W(li("Arctic Blast no longer does extra damage to illusions", t("DEL")))
    W(ul_close())
    W(item_header("Silver Edge"))
    W(ul_open())
    W(li("Total cost decreased from 5800 to 5700 due to Shadow Amulet cost decrease", b(5800, 5700, l=True)))
    W(li("Shadow Walk debuff now caps the target's movement speed to 200. This debuff is not dispellable and does not pierce debuff immunity", t("NEW")))
    W(ul_close())
    W(item_header("Urn of Shadows"))
    W(ul_open())
    W(li("Bonus Mana Regen decreased from +1.4 to +1.25", b(1.4, 1.25)))
    W(li("Soul Release charge gain radius increased from 1400 to 1500", b(1400, 1500)))
    W(li("Soul Release charges can now be gained by all copies of Urn of Shadows item", t("MISC"), extra=inline_note("This change is exclusive to Urn of Shadows and doesn't affect Spirit Vessel")))
    W(li("Soul Release charges can now be gained by both Urn of Shadows and Spirit Vessel from the same hero death", t("MISC"), extra=inline_note("Example to show the result of these two changes:<br>Two allied heroes. Both of them have both Urn of Shadows and Spirit Vessel. An enemy hero dies within 1500 range from them. Both Urns of Shadows will gain a charge. Spirit Vessel will also gain a charge as well, but only for the ally that was closer to the dying enemy")))
    W(ul_close())
    W(item_header("Spirit Vessel"))
    W(ul_open())
    W(li("Soul Release charge gain radius increased from 1400 to 1500", b(1400, 1500)))
    W(li("Soul Release charges can now be gained by both Urn of Shadows and Spirit Vessel from the same hero death", t("MISC")))
    W(ul_close())
    W(item_header("Veil of Discord", changed=True))
    W(auto_components_change("Veil of Discord", "7.40"))
    W(properties_change(
        old=[("BUFF", "+4 Health Regen")],
        new=[("",    "+4.5 Health Regen", b(4, 4.5))]))
    W(item_header("Wind Waker"))
    W(ul_open())
    W(li("Cyclone cooldown increased from 16s to 19s", b(16, 19, l=True)))
    W(ul_close())
    W(item_header("Wraith Band"))
    W(ul_open())
    W(li("Attack Speed bonus increased from +5 to +6", b(5, 6)))
    W(ul_close())

    # ===== NEUTRAL ITEM UPDATES =====
    W(section("Neutral Item Updates"))

    W(plain_header("Artifact changes", dynamics=False, sublabel=True))
    W(item_header("Ripper's Lash"))
    W(ul_open())
    W(li("Item cycled out", t("DEL")))
    W(ul_close())
    W(item_header("Sister's Shroud"))
    W(ul_open())
    W(li("Item cycled out", t("DEL")))
    W(ul_close())
    W(item_header("Spark of Courage"))
    W(ul_open())
    W(li("Item cycled out", t("DEL")))
    W(ul_close())
    W(item_header("Ash Legion Shield", new="New Tier 1 Artifact"))
    W(ul_open())
    W(li("Active: Shield Wall. Decreases wearer's movement speed by 12 to give all friendly player-controlled units within 800 radius a 140 physical damage barrier. Duration: 6s. No Mana Cost. Cooldown: 40s", t("NEW"), extra=inline_note("Doesn't affect ward units")))
    W(ul_close())
    W(item_header("Duelist Gloves", new="Returning Tier 1 Artifact"))
    W(ul_open())
    W(li("Passive: Boldness. Provides 20 attack speed if there are any enemy heroes within 1200 units", t("NEW")))
    W(ul_close())
    W(item_header("Weighted Dice", new="New Tier 1 Artifact"))
    W(ul_open())
    W(li("Passive: Loaded. When calculating wearer's base damage or creep bounty from last hits, the value is computed 2 times and the highest value is taken", t("NEW")))
    W(ul_close())
    W(item_header("Brigand's Blade"))
    W(ul_open())
    W(li("Item cycled out", t("DEL")))
    W(ul_close())
    W(item_header("Defiant Shell", new="Returning Tier 2 Artifact"))
    W(ul_open())
    W(li("Passive: Reciprocity. When attacked, the hero counter-attacks a target within their attack range for 80% of their normal attack damage. Cooldown: 5s. Can't proc attack modifiers", t("NEW"),
         extra=inline_note("Dormant Curio increases counter-attack damage from 80% to 104%")))
    W(ul_close())
    W(item_header("Searing Signet"))
    W(ul_open())
    W(li("Burn Through total damage increased from 72 to 90", b(72, 90), extra=inline_note("Dormant Curio Total Damage increased from 93.6 to 117")))
    W(li("Burn Through now does 50% less damage to non-hero targets", t("NERF")))
    W(ul_close())
    W(item_header("Gale Guard"))
    W(ul_open())
    W(li("Item cycled out", t("DEL")))
    W(ul_close())
    W(item_header("Jidi Pollen Bag"))
    W(ul_open())
    W(li("Pollinate Duration decreased from 12s to 9s", b(12, 9)))
    W(li("Pollinate Max Health Damage decreased from 12% to 9%", b(12, 9), extra=inline_note("Dormant Curio Max Health Damage decreased from 15.6% to 11.7%")))
    W(li("Pollinate Cooldown decreased from 45s to 25s", b(45, 25, l=True)))
    W(ul_close())
    W(item_header("Psychic Headband"))
    W(ul_open())
    W(li("Psychic Push can now target allies", t("NEW"), extra=inline_note("Still can't target the wearer themself")))
    W(ul_close())
    W(item_header("Unrelenting Eye"))
    W(ul_open())
    W(li("Moved from Tier 5 to Tier 3", t("REWORK")))
    W(li("Relentless no longer provides status resistance for nearby enemies", t("DEL")))
    W(li("Relentless max slow resistance decreased from 100% to 50%", b(100, 50), extra=inline_note("Dormant Curio Max Slow Resistance decreased from 130% to 65%")))
    W(li("Relentless slow resistance loss per enemy hero in range decreased from 20% to 10%", b(20, 10)))
    W(li("Relentless search radius changed from 600 to the hero's attack range", t("REWORK")))
    W(ul_close())
    W(item_header("Magnifying Monocle"))
    W(ul_open())
    W(li("Item cycled out", t("DEL")))
    W(ul_close())
    W(item_header("Outworld Staff"))
    W(ul_open())
    W(li("Item cycled out", t("DEL")))
    W(ul_close())
    W(item_header("Pyrrhic Cloak"))
    W(ul_open())
    W(li("Item cycled out", t("DEL")))
    W(ul_close())
    W(item_header("Flayer's Bota", new="New Tier 4 Artifact"))
    W(ul_open())
    W(li("Active: Bloodthirst. Increases wearer's base damage by 15% and attack speed by 30 for 6s. No Mana Cost. Cooldown: 65s", t("NEW"),
         extra=inline_note("Dormant Curio increases bonus base damage from 15% to 19.5% and attack speed from 30 to 39")))
    W(li("Passive: Bloodrush. The cooldown of Bloodthirst is reset whenever an enemy hero dies with 1200 units", t("NEW")))
    W(ul_close())
    W(item_header("Giant's Maul"))
    W(ul_open())
    W(li("Crushing Blow critical damage decreased from 150% to 140%", b(150, 140), extra=inline_note("Dormant Curio critical damage decreased from 195% to 182%")))
    W(ul_close())
    W(item_header("Idol of Scree'auk", new="New Tier 4 Artifact"))
    W(ul_open())
    W(li("Active: False Flight. Grants phased movement, 50% slow resistance, and 25% evasion for 5s. No Mana Cost. Cooldown: 30s", t("NEW"),
         extra=inline_note("Dormant Curio increases duration from 5s to 6.5s")))
    W(ul_close())
    W(item_header("Metamorphic Mandible", new="New Tier 4 Artifact"))
    W(ul_open())
    W(li("Active: Pupate. The wearer enters an insect form for 4 seconds, increasing magic resistance by 35% and movement speed by 15%, but decreasing size by 20% and armor by 45%. No Mana Cost. Cooldown: 30s. Can be dispelled. Can't be cast while channeling", t("NEW"),
         extra=inline_note("Dormant Curio increases duration from 4s to 5.2s")))
    W(ul_close())
    W(item_header("Rattlecage", new="Returning Tier 4 Artifact"))
    W(ul_open())
    W(li("Passive: Reverberate. After taking 180 damage from any source, the wearer fires up to 2 projectiles at random nearby enemies within a 600 unit radius, prioritizing heroes, that deal 110 damage and slows the targets movement and attack speed by 100% for 0.2s", t("NEW"),
         extra=inline_note("Dormant Curio increases damage from 110 to 143")))
    W(ul_close())
    W(item_header("Helm of the Undying"))
    W(ul_open())
    W(li("Item cycled out", t("DEL")))
    W(ul_close())
    W(item_header("Dezun Bloodrite"))
    W(ul_open())
    W(li("Moved from Tier 4 to Tier 5", t("REWORK")))
    W(li("Blood Invocation area of effect bonus increased from 12% to 16%", b(12, 16), extra=inline_note("Dormant Curio Area of Effect bonus increased from 15.6% to 20.8%")))
    W(ul_close())
    W(item_header("Riftshadow Prism", new="New Tier 5 Artifact"))
    W(ul_open())
    W(li("Active: Refract. Spends 10% of the wearer's current health to create a full health illusion that lasts for 20s. The illusion has 50% outgoing damage and 240% incoming damage. No Mana Cost. Cooldown: 30s", t("NEW"),
         extra=inline_note("Dormant Curio increases illusion outgoing damage from 50% to 65%")))
    W(ul_close())

    # ===== HERO UPDATES =====
    W(section("Hero Updates"))


    # Abaddon
    W(hero_header("Abaddon"))
    W(ul_open())
    W(li("Base Strength decreased from 22 to 21", b(22, 21)))
    W(li("Base Agility decreased from 23 to 22", b(23, 22)))
    W(li("Damage at level 1 decreased by 1 (from 50–60 to 49–59)", br(50, 60, 49, 59)))
    W(ul_close())
    W(facet_header("abaddon_the_quickening"))
    W(ul_open())
    W(li("Borrowed Time: Cooldown reduction on hero death decreased from 6s to 5s", b(6, 5)))
    W(ul_close())
    W(ul_open())
    W(li("Mist Coil: Cooldown increased from 6.5/6/5.5/5s to 8/7/6/5s", b([6.5, 6, 5.5, 5], [8, 7, 6, 5], l=True)))
    W(li("Damage/Heal increased from 80/150/220/290 to 95/160/225/290", b([80, 150, 220, 290], [95, 160, 225, 290])))
    W(ul_close())

    # Alchemist
    W(hero_header("Alchemist"))
    W(ability("Acid Spray", slug="alchemist_acid_spray"))
    W(ul_open())
    W(li("Mana Cost increased from 105/110/115/120 to 120", b([105, 110, 115, 120], 120, l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Damage per Greevil's Greed stack increased from +2 to +2.5", b(2, 2.5)))
    W(ul_close())

    # Anti-Mage
    W(hero_header("Anti-Mage"))
    W(ability("Counterspell Ally", slug="antimage_counterspell_ally"))
    W(ul_open())
    W(li("Ability removed", t("DEL")))
    W(ul_close())
    W(ability("Counterspell", slug="antimage_counterspell"))
    W(ul_open())
    W(li("Aghanim's Shard no longer provides Counterspell Ally ability", t("DEL")))
    W(li("Aghanim's Shard illusion outgoing damage increased from 75% to 100%", b(75, 100)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Persecutor Min/Max Movement Slow increased from +7.5/15% to +9/18%", b([7.5, 15], [9, 18])))
    W(ul_close())

    # Arc Warden
    W(hero_header("Arc Warden"))
    W(ul_open())
    W(li("Base attack speed increased from 100 to 110", b(100, 110)))
    W(ul_close())
    W(ability("Magnetic Field", slug="arc_warden_magnetic_field"))
    W(ul_open())
    W(li("Mana Cost rescaled from 50/70/90/110 to 60/70/80/90", b([50, 70, 90, 110], [60, 70, 80, 90], l=True)))
    W(ul_close())

    # Axe
    W(hero_header("Axe"))
    W(ability("Berserker's Call", slug="axe_berserkers_call"))
    W(ul_open())
    W(li("Duration increased from 1.8/2.2/2.6/3s to 2.1/2.4/2.7/3s", b([1.8, 2.2, 2.6, 3], [2.1, 2.4, 2.7, 3])))
    W(li("Cooldown increased from 17/15/13/11s to 18/16/14/12s", b([17, 15, 13, 11], [18, 16, 14, 12], l=True)))
    W(ul_close())
    W(ability("Battle Hunger", slug="axe_battle_hunger"))
    W(ul_open())
    W(li("No longer has an armor-based damage multiplier", t("DEL")))
    W(li("Damage type changed from Physical to Pure", t("REWORK")))
    W(li("No longer has reduced movement slow against creeps", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +10% Battle Hunger Slow replaced with +12 Battle Hunger Damage Per Second", t("REWORK")))
    W(li("Level 20 Talent Counter Helix Damage increased from +30 to +40", b(30, 40)))
    W(li("Level 20 Talent +100 Culling Blade Damage replaced with +15 Strength", t("REWORK")))
    W(li("Level 25 Talent 2x Battle Hunger Armor Multiplier replaced with +150 Culling Blade Damage", t("REWORK")))
    W(ul_close())

    # Bane
    W(hero_header("Bane"))
    W(ability("Nightmare", slug="bane_nightmare"))
    W(ul_open())
    W(li("Cooldown increased from 24/21/18/15s to 25/22/19/16s", b([24, 21, 18, 15], [25, 22, 19, 16], l=True)))
    W(ul_close())
    W(ability("Fiend's Grip", slug="bane_fiends_grip"))
    W(ul_open())
    W(li("Aghanim's Scepter Illusion damage taken increased from 200% to 225%", b(200, 225, l=True)))
    W(ul_close())

    # Batrider
    W(hero_header("Batrider"))
    W(ul_open())
    W(li("Daytime Vision Range increased from 1600 to 1800", b(1600, 1800)))
    W(ul_close())
    W(facet_header("batrider_arsonist"))
    W(ul_open())
    W(li("Arsonist: No longer has decreased number of +2 All Attributes bonuses", t("BUFF")))
    W(ul_close())
    W(ul_open())
    W(li("Flamebreak: Movement Slow decreased from 8/16/24/32% to 6/12/18/24%", b([8, 16, 24, 32], [6, 12, 18, 24])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Flaming Lasso Cooldown Reduction increased from 7s to 8s", b(7, 8)))
    W(ul_close())

    # Beastmaster
    W(hero_header("Beastmaster"))
    W(ul_open())
    W(li("Call of the Wild Boar: Boar's Base Attack Time worsened from 1.25s to 1.35s", b(1.25, 1.35, l=True)))
    W(ul_close())
    W(ability("Wild Axes", slug="beastmaster_wild_axes"))
    W(ul_open())
    W(li("Damage per axe rescaled from 35/65/95/125 to 30/65/100/135", b([35, 65, 95, 125], [30, 65, 100, 135], force_overall="buff")))
    W(ul_close())
    W(ability("Inner Beast", slug="beastmaster_inner_beast", innate=False))
    W(ul_open())
    W(li("Bonus Attack Speed rescaled from 15/30/45/60 to 10/30/50/70", b([15, 30, 45, 60], [10, 30, 50, 70])))
    W(ul_close())

    # Bloodseeker
    W(hero_header("Bloodseeker"))
    W(ability("Sanguivore", slug="bloodseeker_sanguivore"))
    W(ul_open())
    W(li("Base heal increased from 25 to 30", b(25, 30)))
    W(li("No longer upgraded with Aghanim's Shard or Aghanim's Scepter", t("DEL")))
    W(ul_close())
    W(ability("Bloodrage", slug="bloodseeker_bloodrage"))
    W(ul_open())
    W(li("Aghanim's Scepter effect moved to Aghanim's Shard", t("MISC")))
    W(li("Aghanim's Shard target's max health as pure damage decreased from 3% to 2%", b(3, 2)))
    W(ul_close())
    W(ability("Rupture", slug="bloodseeker_rupture"))
    W(ul_open())
    W(li("Aghanim's Scepter: Increases current health as initial damage by 3%. Replaces cooldown with 2 charges with the same charge restoration time", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +15% Bloodrage Spell Amplification replaced with +30 Bloodrage Attack Speed", t("REWORK")))
    W(li("Level 15 Talent +8% Rupture Initial Damage replaced with -0.7% Bloodrage Max Health DPS For Allies", t("REWORK")))
    W(li("Level 20 Talent -0.7% Bloodrage Max Health DPS For Allies replaced with +20 Agility", t("REWORK")))
    W(li("Level 25 Talent 2 Rupture Charges replaced with +2.5s Blood Rite Silence Duration", t("REWORK")))
    W(ul_close())

    # Bounty Hunter
    W(hero_header("Bounty Hunter"))
    W(facet_header("bounty_hunter_mugging"))
    W(ul_open())
    W(li("Cutpurse: Visual effect of gold flying towards Bounty Hunter is no longer visible to enemies if Bounty Hunter is invisible", t("QoL")))
    W(ul_close())
    W(ul_open())
    W(li("Shadow Walk: Stun Duration increased from 0.8/1/1.2/1.4s to 1/1.2/1.4/1.6s", b([0.8, 1, 1.2, 1.4], [1, 1.2, 1.4, 1.6])))
    W(ul_close())

    # Brewmaster
    W(hero_header("Brewmaster"))
    W(ul_open())
    W(li("Strength gain decreased from 3.7 to 3.2", b(3.7, 3.2)))
    W(li("Intelligence gain increased from 1.6 to 1.9", b(1.6, 1.9)))
    W(ul_close())
    W(facet_header("brewmaster_roll_out_the_barrel"))
    W(ul_open())
    W(li("Roll Out the Barrel: Facet removed", t("DEL")))
    W(ul_close())
    W(facet_header("brewmaster_drunken_master"))
    W(ul_open())
    W(li("Drunken Master: Facet removed", t("DEL")))
    W(ul_close())
    _lc_pill, _lc_table = scale_pill("10.5% + 0.5% per level up",
                                     lambda L: 10.5 + 0.5 * L,
                                     value_fmt="{:.1f}%")
    W(ability_change(
        old=dict(
            name="Belligerent",
            innate=True,
            desc=[
                "Passive.",
                "Whenever Brewmaster respawns or comes out of Primal Split, he gains <b>25%</b> bonus attack damage. Duration on respawn: 45s. Duration after Primal Split: 15s.",
            ],
        ),
        new=dict(
            name="Liquid Courage",
            slug="brewmaster_liquid_courage",
            innate=True,
            desc=[
                "Passive. Improves with Brewmaster's level.",
                "When Brewmaster drops below 50% Health he gains a Status Resistance buff, and his movement speed alternates every 1 second between faster and slower. The effect grows stronger at lower health, scaling from 0 up to max values at 20% Health.",
                "Max Status Resistance is " + _lc_pill + ", Max Speed Increase is <b>25%</b>, Max Speed Slow is <b>10%</b>.",
                aghs_shard_line("Brewmaster may activate the ability to toss a strong drink to himself or a teammate, granting the max effects of his innate for 5 seconds plus 2% Max HP Regen per second. Cast Range: 800. Mana Cost: 50. Cooldown: 20s."),
            ],
            tables=[_lc_table],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Thunder Clap", slug="brewmaster_thunder_clap"))
    W(ul_open())
    W(li("Cast point improved from 0.35s to 0.3s", b(0.35, 0.3, l=True)))
    W(li("Mana Cost rescaled from 90/100/110/120 to 100", b([90, 100, 110, 120], 100, l=True)))
    W(li("Radius rescaled from 325/350/375/400 to 375", b([325, 350, 375, 400], 375)))
    W(ul_close())
    W(ability("Cinder Brew", slug="brewmaster_cinder_brew"))
    W(ul_open())
    W(li("Now rolls a barrel of ale that deals 40/70/100/130 physical damage to enemies in its path and drenches enemies along the way and around the target location", t("NEW")))
    W(ul_close())
    W(ability("Drunken Brawler", slug="brewmaster_drunken_brawler"))
    W(ul_open())
    W(li("Moved Brewed Up effect from Cinder Brew to Drunken Brawler", t("MISC"), extra=inline_note("When Brewmaster casts any ability, he becomes Brewed Up for 5 seconds, gaining +150% to his stance bonuses. If he is already Brewed Up, the duration is extended by 1s. After Brewed Up ends, Brewmaster is hungover and cannot become Brewed Up again for 9 seconds")))
    W(li("Stance visual indicator is now always present around Brewmaster", t("QoL")))
    W(li("Stances can now be switched without cancelling channeling or invisibility", t("MISC")))
    W(ul_close())

    # Each Drunken Brawler stance rendered as a standalone ability block using
    # the stance spellicons. A dashed connector (drawStanceConnectors() in
    # scripts.js) anchors them as children of Drunken Brawler above — same
    # concept as Primal Split → brewlings.
    W(ability("Earth Stance", slug="brewmaster_drunken_brawler_earth"))
    W(ul_open())
    W(li("Magic Resistance increased from 5/10/15/20% to 8/12/16/20%", b([5, 10, 15, 20], [8, 12, 16, 20])))
    W(ul_close())
    W(ability("Fire Stance", slug="brewmaster_drunken_brawler_fire"))
    W(ul_open())
    W(li("Attack Speed increased from 10/15/20/25 to 10/20/30/40", b([10, 15, 20, 25], [10, 20, 30, 40])))
    W(ul_close())
    W(ability("Void Stance", slug="brewmaster_drunken_brawler_void"))
    W(ul_open())
    W(li("Stance removed", t("DEL")))
    W(ul_close())
    W(ability("Primal Companion", slug="brewmaster_primal_companion"))
    W(ul_open())
    W(li("Ability removed", t("DEL")))
    W(ul_close())
    W(ability("Primal Split", slug="brewmaster_primal_split"))
    W(ul_open())
    W(li("Duration increased from 16/18/20s to 16/20/24s", b([16, 18, 20], [16, 20, 24])))
    W(li("All Brewlings now receive their respective Drunken Brawler stances", t("NEW")))
    W(li("No longer upgraded with Aghanim's Shard", t("DEL")))
    W(li("Aghanim's Scepter: Allows Brewmaster to cancel the ability early and provides Brewed Up bonus to all Brewlings on cast. Also increases ability's level to 4, improving Brewlings' stats and abilities", t("NEW")))
    W(ul_close())

    # Each brewling rendered as an ability_change comparison card. Same
    # name on both sides → "in-place" mode hides the duplicate header.
    # Each brewling is a standalone ability block. A dashed connector
    # (drawn by drawBrewlingConnectors() in scripts.js) visually anchors
    # them as children of Primal Split above.
    W(ability("Earth Brewling", slug="brewmaster_earth_unit", icon_url="../icons/units/brewmaster_earth_unit.png"))
    W(ul_open())
    W(li("Debuff Immunity ability renamed to Earth Element. No longer grants Debuff Immunity; now provides 80% Status Resistance and 60% Magic Resistance instead", t("REWORK")))
    W(li("Damage increased from 25/60/95 to 35/70/105", b([25, 60, 95], [35, 70, 105]),
         extra=inline_note("From 20–30/55–65/90–100 to 30–40/65–75/100–110")))
    W(li("Movement Speed increased from 330/350/370 to 330/355/380", b([330, 350, 370], [330, 355, 380])))
    W(li("Demolish Bonus Building Damage decreased from 50/100/150 to 40/80/120", b([50, 100, 150], [40, 80, 120])))
    W(li("Aghanim's Scepter increases Brewling level by 1. " + info_tip(
            "4100 HP.", "8 HP Regen.", "135–145 Damage.", "9 Armor.", "",
            "Hurl Boulder: 200 Damage, 2s Stun.", "Demolish: 160 bonus building damage.",
            header="Level 4 stats are:"), t("NEW")))
    W(ul_close())
    W(ability("Storm Brewling", slug="brewmaster_storm_unit", icon_url="../icons/units/brewmaster_storm_unit.png"))
    W(ul_open())
    W(li("Damage increased from 20/40/60 to 30/50/70", b([20, 40, 60], [30, 50, 70]),
         extra=inline_note("From 15–25/35–45/55–65 to 25–35/45–55/65–75")))
    W(li("Aghanim's Scepter increases Brewling level by 1. " + info_tip(
            "2500 HP.", "8 HP Regen.", "85–95 Damage.", "",
            "Wind Walk: 320 bonus damage, 55% bonus movement speed.",
            "Cyclone: 6s hero duration, 100 damage on landing.",
            header="Level 4 stats are:"), t("NEW")))
    W(ul_close())
    W(ability("Fire Brewling", slug="brewmaster_fire_unit", icon_url="../icons/units/brewmaster_fire_unit.png"))
    W(ul_open())
    W(li("Aghanim's Scepter increases Brewling level by 1. " + info_tip(
            "1750 HP.", "8 HP Regen.", "215–225 Damage.", "24 Armor.", "",
            "Permanent Immolation: 100 damage per second.",
            header="Level 4 stats are:"), t("NEW")))
    W(ul_close())
    W(ability("Void Brewling", slug="brewmaster_void_unit", icon_url="../icons/units/brewmaster_void_unit.png"))
    W(ul_open())
    W(li("Brewling removed", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +1.5s Thunder Clap Duration replaced with +1s Drunken Brawler Brew Up / Extend Duration", t("REWORK")))
    W(li("Level 10 Talent +10 Brewlings Damage replaced with +14 Brewlings Base Damage", t("REWORK")))
    W(li("Level 15 Talent Cinder Brew Damage/Duration increased from +30% to 40%", b(30, 40)))
    W(li("Level 15 Talent +1x Brewed Up multiplier for Drunken Brawler replaced with +600 Brewlings Health", t("REWORK")))
    W(li("Level 20 Talent +1200 Brewlings Health replaced with -15s Primal Split Cooldown", t("REWORK")))
    W(li("Level 25 Talent Brewlings Gain Drunken Brawler Passive replaced with 1.5x Drunken Brawler Stance Bonuses", t("REWORK")))
    W(ul_close())

    # Bristleback
    W(hero_header("Bristleback"))
    W(ul_open())
    W(li("Strength gain increased from 2.7 to 2.8", b(2.7, 2.8)))
    W(ul_close())
    W(facet_header("bristleback_snot_rocket"))
    W(ul_open())
    W(li("Viscous Nasal Goo: No longer has increased Armor Loss per stack", t("DEL")))
    W(ul_close())
    W(ul_open())
    W(li("Viscous Nasal Goo: Armor Loss per stack increased from 1.5/2/2.5/3 to 2/2.5/3/3.5 by default", b([1.5, 2, 2.5, 3], [2, 2.5, 3, 3.5])))
    W(ul_close())

    # Broodmother
    W(hero_header("Broodmother"))
    W(ability("Insatiable Hunger", slug="broodmother_insatiable_hunger"))
    W(ul_open())
    W(li("Aghanim's Shard no longer increases duration", t("DEL")))
    W(ul_close())
    W(ability("Spin Web", slug="broodmother_spin_web"))
    W(ul_open())
    W(li("Broodmother's illusions now also benefit from the web", t("NEW")))
    W(ul_close())
    W(ability("Incapacitating Bite", slug="broodmother_incapacitating_bite"))
    W(ul_open())
    W(li("Attack Bonus increased from 2/4/6/8 to 3/6/9/12", b([2, 4, 6, 8], [3, 6, 9, 12])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +1.5% Spider's Milk Heal replaced with +20% Insatiable Hunger Lifesteal", t("REWORK")))
    W(li("Level 15 Talent Spiderlings Health increased from +125 to +150", b(125, 150)))
    W(li("Level 15 Talent Incapacitating Bite Attack Bonus decreased from +12 to +10", b(12, 10)))
    W(li("Level 20 Talent +35 Attack Speed replaced with +25% Incapacitating Bite Slow/Miss Chance", t("REWORK")))
    W(li("Level 25 Talent +30% Incapacitating Bite Slow/Miss Chance replaced with +14% Spin Web Move Speed and Ignore Speed Limit", t("REWORK")))
    W(ul_close())

    # Centaur Warrunner
    W(hero_header("Centaur Warrunner"))
    W(ability("Rawhide", slug="centaur_rawhide"))  # innate (auto-detected)
    W(ul_open())
    W(li("Bonus Max Health decreased from 30 to 25", b(30, 25)))
    W(ul_close())
    W(ability("Work Horse", slug="centaur_work_horse"))
    W(ul_open())
    W(li("Cooldown increased from 24s to 35s", b(24, 35, l=True)))
    W(li("Duration decreased from 8s to 7s", b(8, 7)))
    W(ul_close())

    # Chaos Knight
    W(hero_header("Chaos Knight"))
    W(ul_open())
    W(li("Min Base Damage increased by 5", bstat_h("Chaos Knight", "AttackDamageMin", "7.39e", 5), extra=note_box(hero="Chaos Knight", field="AttackDamageMin", before_patch="7.39e")))
    W(li("Max Base Damage decreased by 5", bstat_h("Chaos Knight", "AttackDamageMax", "7.39e", -5), extra=note_box(hero="Chaos Knight", field="AttackDamageMax", before_patch="7.39e")))
    W(li("Damage at level 1 changed from 48–78 to 53–73", br(48, 78, 53, 73), extra=inline_note("Damage spread decreased from 30 to 20")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent +10s Phantasm Duration replaced with -125% Phantasm Damage Taken", t("REWORK")))
    W(ul_close())

    # Chen
    W(hero_header("Chen"))
    W(ability("Penitence", slug="chen_penitence"))
    W(ul_open())
    W(li("Mana Cost increased from 70/75/80/85 to 80/90/100/110", b([70, 75, 80, 85], [80, 90, 100, 110], l=True)))
    W(li("Cooldown increased from 14/13/12/11s to 20/17/14/11s", b([14, 13, 12, 11], [20, 17, 14, 11], l=True)))
    W(li("No longer grants bonus attack range", t("DEL")))
    W(li("Now deals 50/75/100/125 pure damage by default", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Penitence Deals 175 Damage replaced with +75 Penitence Damage", t("REWORK")))
    W(li("Level 20 Talent Divine Favor Heal Amplification decreased from +20% to +15%", b(20, 15)))
    W(ul_close())

    # Clinkz
    W(hero_header("Clinkz"))
    W(facet_header("clinkz_suppressive_fire"))
    W(ul_open())
    W(li("Suppressive Fire: Facet removed", t("DEL")))
    W(ul_close())
    W(facet_header("clinkz_engulfing_step"))
    W(ul_open())
    W(li("Engulfing Step: Facet removed", t("DEL")))
    W(ul_close())
    W(ability_change(
        old=dict(
            name="Bone and Arrow",
            innate=True,
            desc=[
                "Passive.",
                "Clinkz summons a Skeleton Archer when he dies. Tower hits on the archers count as hero hits.",
            ],
        ),
        new=dict(
            name="Infernal Shred",
            slug="clinkz_infernal_shred",
            innate=True,
            desc=[
                "Passive.",
                "Clinkz and his skeletons apply a stacking debuff that causes their attacks to pierce up to <b>20%</b> of the target's armor. Clinkz applies 2% per attack, his skeletons apply 1%. Debuff lasts 5 seconds. " + info_tip("Doesn't affect the target's armor directly — it simply improves attacks for Clinkz and his skeletons."),
            ],
        ),
        summary="New innate ability.",
        tag="new",
    ))
    W(ability("Tar Bomb", slug="clinkz_tar_bomb"))
    W(ul_open())
    W(li("Ability removed", t("DEL")))
    W(ul_close())
    W(ability("Strafe", slug="clinkz_strafe"))
    W(ul_open())
    W(li("Skeleton Archers attack speed factor decreased from 60% to 50%", b(60, 50)))
    W(ul_close())
    W(ability("Searing Arrows", slug="clinkz_searing_arrows"))
    W(ul_open())
    W(li("Returning as base ability", t("NEW"), extra=inline_note("Imbues Clinkz's arrows with fire for extra 18/32/46/60 extra damage. Skeleton Archers always fire Searing Arrows with 50% reduced damage. Mana Cost: 10<br><br>Skeleton Archers target the enemy attacked by Clinkz with Searing Arrows effect")))
    W(ul_close())
    W(ability("Death Pact", slug="clinkz_death_pact"))
    W(ul_open())
    W(li("No longer creates Skeleton Archers", t("DEL")))
    W(ul_close())
    W(ability("Skeleton Walk", slug="clinkz_wind_walk"))
    W(ul_open())
    W(li("Skeleton Archer stats and Aghanim's Scepter upgrade are now part of Skeleton Walk", t("MISC")))
    W(li("Skeleton Archer Duration rescaled from 15/20/25/30s to 20/25/30s", t("REWORK"), extra=inline_note("Also applies to Burning Army")))
    W(ul_close())
    W(ability("Burning Barrage", slug="clinkz_burning_barrage"))
    W(ul_open())
    W(li("No longer slows the targets", t("DEL")))
    W(ul_close())
    W(ability("Burning Army", slug="clinkz_burning_army"))
    W(ul_open())
    W(li("Spawn Interval improved from 0.15s to 0.1s", b(0.15, 0.1, l=True)))
    W(li("Skeleton count increased from 5 to 6", b(5, 6)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Tar Bomb Multishot replaced with Searing Arrows Multishot", t("REWORK")))
    W(ul_close())

    # Clockwerk
    W(hero_header("Clockwerk"))
    W(ability("Jetpack", slug="rattletrap_jetpack"))
    W(ul_open())
    W(li("Now can be toggled on and off for the duration of the buff. Toggle cooldown: 1s", t("NEW")))
    W(ul_close())
    W(ability("Overclocking", slug="rattletrap_overclocking"))
    W(ul_open())
    W(li("Rocket Flare cooldown increased from 3s to 3.5s", b(3, 3.5, l=True)))
    W(ul_close())

    # Crystal Maiden
    W(hero_header("Crystal Maiden"))
    W(ul_open())
    W(li("Base Damage decreased by 2", t("MISC") + bstat_h("Crystal Maiden", "AttackDamageMin", "7.39e", -2), extra=note_box(hero="Crystal Maiden", field="AttackDamageMin", before_patch="7.39e", extra_note="Damage at level 1 unchanged at 48–54")))
    W(li("Base Intelligence increased from 18 to 20", b(18, 20)))
    W(ul_close())

    # Dark Seer
    W(hero_header("Dark Seer"))
    W(ul_open())
    W(li("Base Intelligence increased from 21 to 22", b(21, 22)))
    W(li("Damage at level 1 increased by 1 (from 52–58 to 53–59)", br(52, 58, 53, 59)))
    W(ul_close())
    W(ability("Vacuum", slug="dark_seer_vacuum"))
    W(ul_open())
    W(li("No longer affects invulnerable units", t("DEL")))
    W(ul_close())

    # Dark Willow
    W(hero_header("Dark Willow"))
    W(ability("Cursed Crown", slug="dark_willow_cursed_crown"))
    W(ul_open())
    W(li("Stun Duration increased from 1.2/1.6/2/2.4s to 1.5/1.8/2.1/2.4s", b([1.2, 1.6, 2, 2.4], [1.5, 1.8, 2.1, 2.4])))
    W(ul_close())
    W(ability("Terrorize", slug="dark_willow_terrorize"))
    W(ul_open())
    W(li("Jex return speed increased from 600 to 800", b(600, 800)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +150 Cursed Crown AoE replaced with -15s Terrorize Cooldown", t("REWORK")))
    W(ul_close())

    # Dawnbreaker
    W(hero_header("Dawnbreaker"))
    W(ul_open())
    W(li("Base Damage increased by 1", bstat_h("Dawnbreaker", "AttackDamageMin", "7.39e", 1), extra=note_box(hero="Dawnbreaker", field="AttackDamageMin", before_patch="7.39e")))
    W(li("Damage at level 1 increased from 49–53 to 50–54", br(49, 53, 50, 54)))
    W(ul_close())
    W(ability("Solar Guardian", slug="dawnbreaker_solar_guardian"))
    W(ul_open())
    W(li("Aghanim's Scepter no longer reduces air time or channel time", t("DEL")))
    W(li("Aghanim's Scepter Heal per pulse increased from 55/85/115 to 60/90/120", b([55, 85, 115], [60, 90, 120])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +12 Damage replaced with +15% Break of Dawn Max Damage", t("REWORK")))
    W(ul_close())

    # Dazzle
    W(hero_header("Dazzle"))
    W(ul_open())
    W(li("Base Strength increased from 18 to 19", b(18, 19), extra=inline_note("Damage at level 1 unchanged")))
    W(li("Intelligence gain decreased from 3.7 to 3.5", b(3.7, 3.5)))
    W(li("Damage gain per level decreased from 3.5 to 3.4", b(3.5, 3.4)))
    W(ul_close())
    W(ability("Nothl Projection", slug="dazzle_nothl_projection"))
    W(ul_open())
    W(li("Aghanim's Shard healing amplification decreased from 20% to 15%", b(20, 15)))
    W(ul_close())

    # Death Prophet
    W(hero_header("Death Prophet"))
    W(ability("Witchcraft", slug="death_prophet_witchcraft"))
    W(ul_open())
    _pill1 = scale_pill("0.75% + 0.75% per level up", lambda L: 0.75 + 0.75*L,
                        levels=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 25, 30])
    W(li("Movement speed bonus changed from 0.5% per hero level to " + _pill1[0] + "", t("REWORK"), extra=_pill1[1]))
    W(ul_close())
    W(ability("Exorcism", slug="death_prophet_exorcism"))
    W(ul_open())
    W(li("No longer provides 4/8/12% bonus movespeed", t("DEL")))
    W(li("Aghanim's Scepter spirit bonus damage increased from 50% to 60%", b(50, 60)))
    W(ul_close())

    # Doom
    W(hero_header("Doom"))
    W(ul_open())
    W(li("Intelligence gain increased from 1.7 to 1.9", b(1.7, 1.9)))
    W(ul_close())
    W(facet_header("doom_bringer_boost_selling"))
    W(ul_open())
    W(li("Boost Selling: Facet removed", t("DEL")))
    W(ul_close())
    W(ul_open())
    W(li("Doom: Aghanim's Scepter now also increases damage per second from 25/45/65 to 40/60/80", b([25, 45, 65], [40, 60, 80])))
    W(ul_close())

    # Dragon Knight
    W(hero_header("Dragon Knight"))
    W(ul_open())
    W(li("Base Agility decreased from 16 to 14", b(16, 14)))
    W(ul_close())
    W(ability("Elder Dragon Form", slug="dragon_knight_elder_dragon_form"))
    W(ul_open())
    W(li("Bonus Attack Damage decreased from 20/60/100/140 to 20/50/80/110", b([20, 60, 100, 140], [20, 50, 80, 110])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent 30% Breathe Fire Damage Reduction replaced with -2s Breathe Fire Cooldown", t("REWORK")))
    W(li("Level 20 Talent +85% Breathe Fire Damage/Cast Range in Dragon Form replaced with +60% Breathe Fire Damage/Cast Range", t("REWORK")))
    W(ul_close())

    # Drow Ranger
    W(hero_header("Drow Ranger"))
    W(ability("Frost Arrows", slug="drow_ranger_frost_arrows"))
    W(ul_open())
    W(li("Movement Slow increased from 10/20/30/40% to 15/25/35/45%", b([10, 20, 30, 40], [15, 25, 35, 45])))
    W(ul_close())
    W(ability("Marksmanship", slug="drow_ranger_marksmanship"))
    W(ul_open())
    W(li("Disable range decreased from 400 to 325", b(400, 325)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Gust Costs No Mana replaced with -25% Frost Arrows Mana Cost", t("REWORK")))
    W(ul_close())

    # Earth Spirit
    W(hero_header("Earth Spirit"))
    W(ul_open())
    W(li("Base Damage decreased by 6", bstat_h("Earth Spirit", "AttackDamageMin", "7.39e", -6), extra=note_box(hero="Earth Spirit", field="AttackDamageMin", before_patch="7.39e")))
    W(li("Damage at level 1 decreased from 53–57 to 47–51", br(53, 57, 47, 51)))
    W(ul_close())
    W(facet_header("earth_spirit_resonance"))
    W(ul_open())
    W(li("Resonance: Facet removed", t("DEL")))
    W(ul_close())
    W(facet_header("earth_spirit_stepping_stone"))
    W(ul_open())
    W(li("Stepping Stone: Facet removed", t("DEL")))
    W(ul_close())
    W(facet_header("earth_spirit_ready_to_roll"))
    W(ul_open())
    W(li("Ready to Roll: Facet removed", t("DEL")))
    W(ul_close())
    W(ul_open())
    W(li("Stone Remnant: Now passively grants +2.5% bonus attack damage per currently unused charge", t("NEW")))
    W(li("Whenever Earth Spirit uses another ability on Stone Remnant, he gains +7.5% bonus attack damage for 10s (effect doesn't stack)", t("NEW")))
    W(li_formula("Max Ability Charges increased",
                 "7 + 1 additional charge at every 5th level",
                 "7 + 1 per 4 hero level ups",
                 lambda L: 7 + L // 5,
                 lambda L: 7 + L // 4,
                 levels=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 25, 30]))
    W(ul_close())
    W(ul_open())
    W(li("Boulder Smash: Cooldown rescaled from 22/18/14/10s to 20/17/14/11s", b([22, 18, 14, 10], [20, 17, 14, 11], l=True)))
    W(ul_close())
    W(ul_open())
    W(li("Geomagnetic Grip: Aghanim's Shard reworked. Can now target allied units by default with 550/600/650/700 cast range.", t("NEW"), extra=inline_note("Aghanim's Shard rework: Decreases cooldown by 3s and increases allied unit cast range and speed by 50%<br><br>Can't pull allies that are affected by Leash, Root, Bind, Duel, Chronosphere or Black Hole")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent -3s Geomagnetic Grip Cooldown replaced with -2s Boulder Smash Cooldown", t("REWORK")))
    W(li("Level 20 Talent +180 Rolling Boulder Damage replaced with +175% Rolling Boulder Damage from Strength", t("REWORK")))
    W(li("Level 25 Talent -3s Boulder Smash Cooldown replaced with +175 Geomagnetic Grip Remnant Damage", t("REWORK")))
    W(li("Level 25 Talent Magnetize Undispellable replaced with Earth Spirit Magnetizes Himself", t("REWORK"), extra=inline_note("Applies Magnetize at its current duration to enemy Heroes around Earth Spirit, and can be refreshed with Stone Remnants")))
    W(ul_close())

    # Earthshaker
    W(hero_header("Earthshaker"))
    W(ability("Fissure", slug="earthshaker_fissure"))
    W(ul_open())
    W(li("Damage decreased from 110/170/230/290 to 100/160/220/280", b([110, 170, 230, 290], [100, 160, 220, 280])))
    W(li("Aghanim's Shard no longer allows Fissure walking", t("DEL")))
    W(ul_close())
    W(ability("Echo Slam", slug="earthshaker_echo_slam"))
    W(ul_open())
    W(li("Echo Damage decreased from 90/100/110 to 70/90/110", b([90, 100, 110], [70, 90, 110])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Enchant Totem Damage increased from +50% to +65%", b(50, 65)))
    W(ul_close())

    # Elder Titan
    W(hero_header("Elder Titan"))
    W(ability("Astral Spirit", slug="elder_titan_ancestral_spirit"))
    W(ul_open())
    W(li("Return Astral Spirit and Move Astral Spirit sub-abilities can now be used while Elder Titan is disabled", t("MISC")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Astral Spirit Move Speed Per Hero increased from +2% to +2.5%", b(2, 2.5)))
    W(li("Level 20 Talent Natural Order Radius increased from +100 to +150", b(100, 150)))
    W(ul_close())

    # Ember Spirit
    W(hero_header("Ember Spirit"))
    W(ability("Flame Guard", slug="ember_spirit_flame_guard"))
    W(ul_open())
    W(li("Cooldown decreased from 35s to 32s", b(35, 32, l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Searing Chains Duration decreased from +1s to +0.8s", b(1, 0.8)))
    W(li("Level 20 Talent Searing Chains Damage decreased from +60 to +50", b(60, 50)))
    W(ul_close())

    # Enchantress
    W(hero_header("Enchantress"))
    W(facet_header("enchantress_overprotective_wisps"))
    W(ul_open())
    W(li("Nature's Attendants: Wisp maximum decreased from 4 to 3", b(4, 3)))
    W(ul_close())
    W(ul_open())
    W(li_formula("Rabble-Rouser: Damage amplification changed",
                 "10% + 4% per Enchantress level", "4% + 4% per Enchantress level up",
                 lambda L: 10 + 4 * L, lambda L: 4 + 4 * L,
                 value_fmt="{:g}%"))
    W(li("Now also affects units that come under Enchantress' control", t("NEW")))
    W(ul_close())
    W(ul_open())
    W(li("Enchant: Creep Attack Damage Bonus decreased from 0/25/50/75 to 0/20/40/60", b([0, 25, 50, 75], [0, 20, 40, 60])))
    W(li("Enchanted units may now be bound to a persistent hotkey", t("QoL")))
    W(ul_close())
    W(ul_open())
    W(li("Little Friends: Affected creeps now gain damage buff from Rabble-Rouser for the duration in case they did not have it", t("MISC")))
    W(li("Bonus Attack Speed decreased from 100 to 70", b(100, 70)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +10 Enchanted Creep Armor replaced with +5 Armor for Enchantress and her units", t("REWORK"), extra=inline_note("Requires at least 1 level of Enchant")))
    W(li("Level 20 Talent +60 Untouchable Attack Slow replaced with +9 Nature's Attendants Wisps", t("REWORK")))
    W(li("Level 25 Talent +12 Nature's Attendants Wisps replaced with +70 Untouchable Attack Slow", t("REWORK")))
    W(ul_close())

    # Enigma
    W(hero_header("Enigma"))
    W(ability("Malefice", slug="enigma_malefice"))
    W(ul_open())
    W(li("Aghanim's Shard now also spawns an Eidolon if the target dies before the effect expires", t("MISC")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Malefice Instance Damage increased from +50 to +60", b(50, 60)))
    W(ul_close())

    # Faceless Void
    W(hero_header("Faceless Void"))
    W(ability("Time Dilation", slug="faceless_void_time_dilation"))
    W(ul_open())
    W(li("Now always applies one instance of damage and slow in addition to the per cooldown instances", t("NEW")))
    W(li("Slow per cooldown decreased from 7/8/9/10% to 4/5/6/7%", b([7, 8, 9, 10], [4, 5, 6, 7], l=True)))
    W(li("DPS per cooldown decreased from 7/9/11/13 to 4/6/8/10", b([7, 9, 11, 13], [4, 6, 8, 10], l=True)))
    W(li("Duration decreased from 8/9/10/11s to 7/8/9/10s", b([8, 9, 10, 11], [7, 8, 9, 10])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Time Dilation DPS Per Cooldown decreased from +9 to +6", b(9, 6, l=True)))
    W(li("Level 15 Talent Time Dilation Slow per Cooldown decreased from +12% to +8%", b(12, 8, l=True)))
    W(ul_close())

    # Grimstroke
    W(hero_header("Grimstroke"))
    W(ability("Phantom's Embrace", slug="grimstroke_ink_creature"))
    W(ul_open())
    W(li("Cooldown is now also refreshed if the phantom's target dies before the phantom latches to it", t("NEW")))
    W(ul_close())
    W(ability("Soulbind", slug="grimstroke_soul_chain"))
    W(ul_open())
    W(li("Ability can now be reflected", t("NEW"),
         extra=inline_note("Reflected spells get casted onto both units affected by Soulbind")))
    W(ul_close())
    W(ability("Dark Portrait", slug="grimstroke_dark_portrait"))
    W(ul_open())
    W(li("Illusion Outgoing Damage decreased from 150% to 125%", b(150, 125)))
    W(li("Illusion Damage Taken decreased from 350% to 275%", b(350, 275, l=True)))
    W(ul_close())

    # Gyrocopter
    W(hero_header("Gyrocopter"))
    W(facet_header("gyrocopter_afterburner"))
    W(ul_open())
    W(li("Rocket Barrage: Movespeed duration decreased from 4.5s to 4s", b(4.5, 4)))
    W(ul_close())
    W(ul_open())
    W(li("Call Down: Missile Damage decreased from 250/425/600 to 200/350/500", b([250, 425, 600], [200, 350, 500])))
    W(ul_close())

    # Hoodwink
    W(hero_header("Hoodwink"))
    W(facet_header("hoodwink_hunter"))
    W(ul_open())
    W(li("Scurry: Active cast range decreased from 75/150/225/300 to 50/100/150/200", b([75, 150, 225, 300], [50, 100, 150, 200])))
    W(li("Scurry: Active Attack Range decreased from 75/150/225/300 to 50/100/150/200", b([75, 150, 225, 300], [50, 100, 150, 200])))
    W(ul_close())
    W(ul_open())
    W(li("Mistwoods Wayfarer: Ability can no longer target trees affecting Acorn Shot or Bushwhack", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +1.5 Mana Regen replaced with +150 Health", t("REWORK")))
    W(li("Level 10 Talent +1 Scurry Ability Charge replaced with +50 Bushwhack Damage", t("REWORK")))
    W(li("Level 15 Talent +60 Bushwhack Damage replaced with +1 Scurry Ability Charge", t("REWORK")))
    W(ul_close())

    # Invoker
    W(hero_header("Invoker"))
    W(facet_header("invoker_wex_focus"))
    W(ul_open())
    W(li("E.M.P.: Aghanim's Shard drag speed decreased from 150 to 125", b(150, 125)))
    W(ul_close())
    W(ul_open())
    W(li("Alacrity: Mana Cost decreased from 90 to 75", b(90, 75, l=True)))
    W(li("Cast Range increased from 650 to 700", b(650, 700)))
    W(ul_close())
    W(ul_open())
    W(li_formula("Ice Wall: Damage increased",
                 "25 + 5 × Exort Level", "24 + 6 × Exort Level",
                 lambda E: 25 + 5 * E, lambda E: 24 + 6 * E,
                 levels=list(range(1, 11)), level_prefix='E',
                 value_fmt="{:g}"))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Cold Snap Cooldown Reduction increased from 5s to 6s", b(5, 6)))
    W(li("Level 20 Talent +35 Alacrity Damage/Speed changed to +50", t("MISC")))
    W(ul_close())

    # Io
    W(hero_header("Io"))
    W(ul_open())
    W(li("Base Strength increased from 17 to 19", b(17, 19)))
    W(li("Base Intelligence decreased from 23 to 21", b(23, 21), extra=inline_note("Damage at level 1 unchanged (45–51)")))
    W(ul_close())
    W(ability("Spirits", slug="wisp_spirits"))
    W(ul_open())
    W(li("Mana Cost decreased from 100/110/120/130 to 90/100/110/120", b([100, 110, 120, 130], [90, 100, 110, 120], l=True)))
    W(li("Cooldown decreased from 22/21/20/19s to 15s", b([22, 21, 20, 19], 15, l=True)))
    W(li("Duration decreased from 19s to 15s", b(19, 15)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +12 Attack Damage to Tethered Units replaced with +7 Strength", t("REWORK")))
    W(li("Level 15 Talent +60 Spirits Hero Damage replaced with +50% Spirits Damage", t("REWORK")))
    W(li("Level 25 Talent Unslowable during Overcharge replaced with -1.5s Relocate Cast Delay", t("REWORK")))
    W(ul_close())

    # Jakiro
    W(hero_header("Jakiro"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent -2s Dual Breath Cooldown replaced with +60 Ice Path Base Damage", t("REWORK")))
    W(li("Level 10 Talent +150 Attack Range replaced with +30 Liquid Fire Attack Speed Slow", t("REWORK")))
    W(li("Level 15 Talent +60 Ice Path Base Damage replaced with -3s Dual Breath Cooldown", t("REWORK")))
    W(li("Level 15 Talent +50 Liquid Fire Attack Speed Slow replaced with +175 Attack Range", t("REWORK")))
    W(li("Level 25 Talent Liquid Frost and Fire Max Health Damage increased from +2.5% to +3%", b(2.5, 3)))
    W(ul_close())

    # Juggernaut
    W(hero_header("Juggernaut"))
    W(ul_open())
    W(li("Base Agility decreased from 34 to 32", b(34, 32)))
    W(li("Damage at level 1 decreased from 56–58 to 54–56", br(56, 58, 54, 56)))
    W(ul_close())
    W(ability("Blade Fury", slug="juggernaut_blade_fury"))
    W(ul_open())
    W(li("Mana Cost increased from 105/110/115/120 to 120", b([105, 110, 115, 120], 120, l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Healing Ward Hits to Kill decreased from +2 to +1", b(2, 1)))
    W(ul_close())

    # Keeper of the Light
    W(hero_header("Keeper of the Light"))
    W(ul_open())
    W(li("Base Intelligence increased from 23 to 24", b(23, 24)))
    W(li("Damage at level 1 increased from 43–50 to 44–51", br(43, 50, 44, 51)))
    W(ul_close())
    W(ability("Blinding Light", slug="keeper_of_the_light_blinding_light"))
    W(ul_open())
    W(li("Damage increased from 85/130/175/220 to 90/140/190/240", b([85, 130, 175, 220], [90, 140, 190, 240])))
    W(ul_close())
    W(ability("Chakra Magic", slug="keeper_of_the_light_chakra_magic"))
    W(ul_open())
    W(li("Mana Restore increased from 75/150/225/300 to 90/160/230/300", b([75, 150, 225, 300], [90, 160, 230, 300])))
    W(ul_close())
    W(ability("Will-O-Wisp", slug="keeper_of_the_light_will_o_wisp"))
    W(ul_open())
    W(li("Damage increased from 75 to 85", b(75, 85)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent -5s Blinding Light Cooldown replaced with +90 Blinding Light Damage", t("REWORK")))
    W(ul_close())

    # Kez
    W(hero_header("Kez"))
    W(ul_open())
    W(li("Base Strength increased from 19 to 20", b(19, 20)))
    W(ul_close())
    W(ability("Switch Discipline", slug="kez_switch_weapons"))
    W(ul_open())
    W(li_formula("Cooldown reduction per level increased from 0.2s to 0.25s. Cooldown changed",
                 "8s − 0.2s per level", "8s − 0.25s per level",
                 lambda L: 8 - 0.2 * L, lambda L: 8 - 0.25 * L, l=True,
                 value_fmt="{:g}s"))
    W(li("Katana Base Attack Time improved from 2.0s to 1.8s", b(2.0, 1.8, l=True)))
    W(li("Katana Bonus Agility Base Damage decreased from 20% to 12%", b(20, 12)))
    W(ul_close())
    W(ability("Kazurai Katana", slug="kez_kazurai_katana"))
    W(ul_open())
    W(li("Damage per second rescaled from 5/7/9/11 to 3/6/9/12%", b([5, 7, 9, 11], [3, 6, 9, 12])))
    W(li("The active effect may only trigger up to a maximum of 500 stacks", t("REWORK")))
    W(li("Aghanim's Shard now also increases Max Stacks to 1000 and stack as burst damage from 50% to 100%", t("REWORK")))
    W(ul_close())
    W(ability("Falcon Rush", slug="kez_falcon_rush"))
    W(ul_open())
    W(li("No longer causes Kez to have a fixed attack rate or any interaction with attack speed", t("NEW")))
    W(li("Echo Attack Damage decreased from 45/55/65/75% to 35/40/45/50%", b([45, 55, 65, 75], [35, 40, 45, 50])))
    W(li("Echoes now have 50% reduced chance to proc random effects", t("NERF"), extra=inline_note("Echo with Maelstrom (25% chance) will have a 12.5% chance to proc its passive")))
    W(li("Echoes can no longer trigger Marks, but may still create them", t("NERF"), extra=inline_note("However, their chance to mark will be reduced from 18% to 9% due to the proc chance change mentioned before")))
    W(li("Rush Speed decreased from 1000 to 850", b(1000, 850)))
    W(ul_close())
    W(ability("Shodo Sai", slug="kez_shodo_sai"))
    W(ul_open())
    W(li("Marked Stun Duration decreased from 0.5s to 0.4s", b(0.5, 0.4)))
    W(li("Parry Stun Duration decreased from 0.5s to 0.4s", b(0.5, 0.4)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent +50% Attack Damage Added to Talon Toss replaced with +60 Attack Speed During Falcon Rush", t("REWORK")))
    W(ul_close())

    # Kunkka
    W(hero_header("Kunkka"))
    W(ability("Torrent", slug="kunkka_torrent"))
    W(ul_open())
    W(li("Damage increased from 80/160/240/320 to 110/180/250/320", b([80, 160, 240, 320], [110, 180, 250, 320])))
    W(ul_close())
    W(ability("X Marks the Spot", slug="kunkka_x_marks_the_spot"))
    W(ul_open())
    W(li("Cooldown decreased from 30/24/18/12s to 24/20/16/12s", b([30, 24, 18, 12], [24, 20, 16, 12], l=True)))
    W(ul_close())

    # Legion Commander
    W(hero_header("Legion Commander"))
    W(ability("Press The Attack", slug="legion_commander_press_the_attack"))
    W(ul_open())
    W(li("Mana Cost decreased from 110 to 100", b(110, 100, l=True)))
    W(ul_close())
    W(ability("Moment of Courage", slug="legion_commander_moment_of_courage"))
    W(ul_open())
    W(li("Cooldown rescaled from 1.9/1.5/1.1/0.7s to 1.7/1.4/1.1/0.8s", b([1.9, 1.5, 1.1, 0.7], [1.7, 1.4, 1.1, 0.8], l=True, force_overall="buff")))
    W(ul_close())

    # Leshrac
    W(hero_header("Leshrac"))
    W(facet_header("leshrac_misanthropy"))
    W(ul_open())
    W(li("Diabolic Edict: Duration increased from 6s to 7.5s", b(6, 7.5)))
    W(ul_close())
    W(ul_open())
    W(li("Split Earth: Radius increased from 135/160/185/210 to 150/170/190/210", b([135, 160, 185, 210], [150, 170, 190, 210])))
    W(ul_close())

    # Lina
    W(hero_header("Lina"))
    W(ul_open())
    W(li("Intelligence gain increased from 3.8 to 4.0", b(3.8, 4)))
    W(ul_close())
    W(ability("Laguna Blade", slug="lina_laguna_blade"))
    W(ul_open())
    W(li("Cast Range increased from 600 to 750", b(600, 750)))
    W(ul_close())

    # Lion
    W(hero_header("Lion"))
    W(ability("Hex", slug="lion_voodoo"))
    W(ul_open())
    W(li("Mana Cost decreased from 125/150/175/200 to 110/140/170/200", b([125, 150, 175, 200], [110, 140, 170, 200], l=True)))
    W(ul_close())
    W(ability("Finger of Death", slug="lion_finger_of_death"))
    W(ul_open())
    W(li("Cooldown decreased from 130/85/40s to 120/80/40s", b([130, 85, 40], [120, 80, 40], l=True)))
    W(ul_close())

    # Lone Druid
    W(hero_header("Lone Druid"))
    W(ul_open())
    W(li("Base Movement Speed decreased from 325 to 295", b(325, 295)))
    W(li("Base Damage increased by 4", bstat_h("Lone Druid", "AttackDamageMin", "7.39e", 4), extra=note_box(hero="Lone Druid", field="AttackDamageMin", before_patch="7.39e")))
    W(li("Damage at level 1 increased from 38–42 to 42–46", br(38, 42, 42, 46)))
    W(ul_close())
    W(facet_header("lone_druid_bear_with_me"))
    W(ul_open())
    W(li("Bear with Me: Facet removed", t("DEL")))
    W(ul_close())
    W(facet_header("lone_druid_bear_necessities"))
    W(ul_open())
    W(li("Bear Necessities: Facet removed", t("DEL")))
    W(ul_close())
    W(ul_open())
    W(li("Gift Bearer: Innate ability removed. Its effect is now a part of Summon Spirit Bear ability", t("DEL")))
    W(ul_close())
    W(ul_open())
    W(li("Summon Spirit Bear: Moved to an innate ability. Cannot be leveled up", t("REWORK")))
    W(li("Ability is moved to the 4th ability slot", t("MISC"), extra=inline_note("D key by default")))
    W(li("Spirit Bear now counts as a melee hero for most spells", t("REWORK"), extra=inline_note("Since the bear is now a hero, all unit-related changes moved to a separate Spirit Bear section below. This section is for the summon ability changes only")))
    W(li("Cooldown decreased from 150/140/130/120s to 120s", b([150, 140, 130, 120], 120, l=True)))
    W(ul_close())
    W(ability_change(
        old=None,
        new=dict(
            name="Entangle",
            slug="lone_druid_entangle",
            desc=[
                "New Point Targeted basic ability. Pierces Debuff Immunity.",
                "Allows Lone Druid to Entangle enemies once they gain 5 stacks of this ability. Entangled enemies are unable to move for <b>1.2/1.6/2/2.4s</b> and take <b>60/70/80/90</b> damage per second. On cast, applies 2 stacks to each enemy hero and 5 stacks to enemy creeps in the area, and empowers Lone Druid for 10s (1 stack per attack on enemy heroes). Enemies are protected from gaining new stacks while already Entangled. Radius: 350. Stack Duration: 10s. Cast Range: 700. Mana Cost: 60. Cooldown: 24/22/20/18s.",
                "Spirit Bear's Entangling Claws now levels up with this ability and is permanently empowered."
                + inline_note("The Empowered Buff and the enemy stack-counter debuff are undispellable; the Entangled debuff is dispellable. Creeps gain stacks only on cast (not from attacks); Roshan is affected as a hero."),
                aghs_line("Increases radius to 450 and hero stacks on cast to 5, instantly Entangling them. Also removes stack protection from Entangled enemies."),
            ],
        ),
        summary="New ability.",
        tag="new",
    ))
    W(ability("Spirit Link", slug="lone_druid_spirit_link"))
    W(ul_open())
    W(li("No longer grants attack speed or shared armor", t("DEL")))
    W(li("Now also passively grants +10/20/30/40 movement speed to Lone Druid and +20/40/60/80 to his Spirit Bear", t("NEW")))
    W(li("Lone Druid's attacks now heal the Spirit Bear by default", t("NEW")))
    W(li("No longer upgraded with Aghanim's Scepter", t("DEL")))
    W(ul_close())
    W(ability("True Form", slug="lone_druid_true_form"))
    W(ul_open())
    W(li("Mana Cost decreased from 200 to 80", b(200, 80, l=True)))
    W(li("Duration decreased from 40s to 25s", b(40, 25)))
    W(li("Cooldown decreased from 100s to 60/55/50s", b(100, [60, 55, 50], l=True)))
    W(li("No longer grants Entangling Claws and Demolish to Lone Druid", t("DEL")))
    W(li("Now also provides 50/90/130 bonus attack damage", t("NEW")))
    W(li("Bonus Armor increased from 8/10/12 to 10/15/20", b([8, 10, 12], [10, 15, 20])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +30 Spirit Bear Movement Speed replaced with +15 Entangle Root Damage Per Second", t("REWORK")))
    W(li("Level 10 Talent +200 Health replaced with -25s Summon Spirit Bear Cooldown", t("REWORK")))
    W(li("Level 15 Talent +7 Spirit Bear Armor replaced with +12 Agility", t("REWORK")))
    W(li("Level 20 Talent +30 Entangling Claws DPS replaced with +55 Attack Speed", t("REWORK")))
    W(li("Level 25 Talent +45 Spirit Link Attack Speed replaced with +0.6s Entangle Root Duration (also affects Spirit Bear's Entangling Claws)", t("REWORK")))
    W(li("Level 25 Talent -50s True Form Cooldown replaced with True Form provides 60% Slow Resistance", t("REWORK")))
    W(ul_close())

    # Spirit Bear (Lone Druid pet)
    W(unit_header("Spirit Bear", "../icons/abilities/lone_druid_spirit_bear.png", kind="Creep-hero"))
    # One NEW headline row (stats rescale) → old/new stat panes right under it,
    # then ONE umbrella row whose show_list collapses every hero-status
    # consequence (deliberate exception to the "info, not show_list" rule —
    # 8 separate tagged rows here were pure noise).
    W(ul_open())
    W(li("Now a Universal melee hero instead of a creep — base stats rescaled accordingly", t("NEW")))
    W(ul_close())
    # Old creep-Bear stats (per Summon Spirit Bear rank 1-4) → new hero-Bear flat
    # stats, side by side with per-rank %-deltas. Row N of the old pane aligns
    # with row N of the new pane (properties_change subgrid).
    W(properties_change(
        old=[
            ("NERF", "Base Health: 1100/1400/1700/2000"),
            ("NERF", "Base Health Regen: 5/6/7/8"),
            ("BUFF", "Base Attack Time: 1.75/1.65/1.55/1.45s"),
            ("BUFF", "Base Attack Speed: 100"),
            ("NERF", "Base Armor: 0/2/4/6"),
            ("NERF", "Base Movement Speed: 300/330/360/390"),
            ("BUFF", "Base Magic Resistance: 0%"),
            ("BUFF", "Daytime Vision Range: 1400"),
            ("DEL",  "Gains 100 Health and 5 Damage per level"),
        ],
        new=[
            ("", "Base Health: 1500", b([1100, 1400, 1700, 2000], 1500)),
            ("", "Base Health Regen: 3", b([5, 6, 7, 8], 3)),
            ("", "Base Attack Time: 1.5s", b([1.75, 1.65, 1.55, 1.45], 1.5, l=True)),
            ("", "Base Attack Speed: 110", b(100, 110)),
            ("", "Base Armor: 0", b([0, 2, 4, 6], 0)),
            ("", "Base Movement Speed: 310", b([300, 330, 360, 390], 310)),
            ("", "Base Magic Resistance: 25%"
                 + inline_note("Demolish ability no longer passively grants 33% magic resistance")),
            ("", "Daytime Vision Range: 1800", b(1400, 1800)),
            ("NEW", "Gains 4.5 Strength, 4.5 Agility and 0.5 Intelligence per level"
                    + inline_note("Still has no base attributes, so they are all zeroes at level 1")),
        ],
    ))
    W(ul_open())
    W(li("Now interacts with other spells, mechanics and game systems as a hero", t("NEW"),
         extra=show_list(
             "Attacks now count as melee hero attacks against: Roshan's Banner, Clinkz' Skeleton Archers, Lich's Ice Spire, Phoenix's Supernova, Pugna's Nether Ward, Templar Assassin's Psionic Traps, and Undying's Tombstone (already did hero damage to Shadow Shaman's Mass Serpent Wards, Couriers, Observer Wards and Sentry Wards)",
             "Can now be targeted or affected as a hero by: Axe's Culling Blade, Bounty Hunter's Track, Earth Spirit's Petrify, Legion Commander's Duel, Lion's Finger of Death, Mars' Spear of Mars, Necrophos' Reaper's Scythe, Slark's Pounce, Terrorblade's Reflection, Terrorblade's Sunder (only if the Bear is not Debuff Immune), and Underlord's Atrophy Aura",
             "At the same time, Bounty Hunter will not steal Lone Druid's gold anymore by hitting Spirit Bear with Jinada or by using skills with Cutpurse facet on it",
             "Death will not provide charges for: Urn of Shadows and its upgrades, Pudge's permanent Strength from Flesh Heap, Silencer's permanent Int from Brain Drain, Slark's permanent Agility from Essence Shift, and Storm Spirit's stacks for Galvanized (temporary attribute losses from Silencer's, Slark's and other similar spells still work)",
             "Can now capture Watchers and Outposts",
             "Can now break enemy Smoke of Deceit",
             "Starts with a Town Portal Scroll on cooldown the first time it is summoned",
             "Receives a copy of Lone Druid's Neutral Item with an independent cooldown",
             "Has a separate Talent Tree",
             summary="Show all interactions")))
    # Ability order, old → new: bare square ability icons in a single flow row
    # (hover = name), arrow between the groups. NEW-in-7.40 Spirit Link gets the
    # purple ring; the hidden innate Demolish is dimmed.
    def _ao_icon(name, slug, new=False, dim=False, note=None):
        cls = "ao-icon" + (" is-new" if new else "") + (" is-dim" if dim else "")
        tip = name + (f" ({note})" if note else "")
        return (f'<span class="{cls}" data-tooltip="{_html.escape(tip, quote=True)}">'
                f'<img src="{ABIL_CDN}{slug}.png" alt="" loading="lazy"></span>')
    W(li("Ability order has been changed", t("MISC"), extra=(
        '<div class="ability-order-flow">'
        + '<div class="ao-group">'
        + _ao_icon("Return", "lone_druid_spirit_bear_return")
        + _ao_icon("Demolish", "lone_druid_spirit_bear_demolish")
        + _ao_icon("Savage Roar", "lone_druid_savage_roar")
        + _ao_icon("Entangling Claws", "lone_druid_spirit_bear_entangle")
        + _ao_icon("Fetch", "lone_druid_spirit_bear_fetch")
        + '</div>'
        + '<span class="ao-arrow">→</span>'
        + '<div class="ao-group">'
        + _ao_icon("Demolish", "lone_druid_spirit_bear_demolish", dim=True, note="innate, hidden")
        + _ao_icon("Return", "lone_druid_spirit_bear_return")
        + _ao_icon("Entangling Claws", "lone_druid_spirit_bear_entangle")
        + _ao_icon("Savage Roar", "lone_druid_savage_roar")
        + _ao_icon("Spirit Link", "lone_druid_spirit_link", new=True, note="new")
        + _ao_icon("Fetch", "lone_druid_spirit_bear_fetch")
        + '</div>'
        + '</div>')))
    W(ul_close())
    W(ability("Demolish", slug="lone_druid_spirit_bear_demolish"))
    W(ul_open())
    W(li("Ability is now Innate to Spirit Bear", t("NEW")))
    W(li("Bonus Building Damage rescaled from 10/20/30/40% to 30%", b([10, 20, 30, 40], 30)))
    W(li("No longer passively grants 33% magic resistance", t("DEL")))
    W(ul_close())
    W(ability("Return", slug="lone_druid_spirit_bear_return"))
    W(ul_open())
    W(li("Now considered a Teleport for the \"Teleport Requires Hold/Cancel to Stop\" option", t("QoL")))
    W(ul_close())
    W(ability_change(
        old=dict(
            name="Entangling Claws",
            slug="lone_druid_spirit_bear_entangle",
            desc=[
                "Passive.",
                "Spirit Bear's attacks have a chance to root the target (Entangle), preventing movement for <b>1/1.6/2.2/2.8s</b> and dealing damage over the duration.",
            ],
        ),
        new=dict(
            name="Entangling Claws",
            slug="lone_druid_spirit_bear_entangle",
            desc=[
                "Passive. Pierces Debuff Immunity. Levels up with Lone Druid's Entangle.",
                "Allows Spirit Bear to Entangle enemies once they gain 5 stacks of this ability. Entangled enemies are unable to move for <b>1.2/1.6/2/2.4s</b> and take <b>60/70/80/90</b> damage per second. Spirit Bear's attacks are permanently empowered, applying 1 stack with each attack on enemy heroes. Enemies are protected from gaining new stacks while already Entangled."
                + inline_note("Stacks are applied only to heroes, creep heroes and Roshan."),
            ],
        ),
        summary="Ability reworked.",
        tag="rework",
    ))
    W(ability("Fetch", slug="lone_druid_spirit_bear_fetch"))
    W(ul_open())
    W(li("After fetching an enemy, Spirit Bear will now have an attack command issued towards the target", t("MISC")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talents: +10% Magic Resistance OR +20 Movement Speed", t("NEW")))
    W(li("Level 15 Talents: +4 Armor OR Return Has No Cooldown and -0.5s Channel Time", t("NEW")))
    W(li("Level 20 Talents: +500 Health OR +30 Damage", t("NEW")))
    W(li("Level 25 Talents: +15% Damage to Entangled Units OR +20% Demolish Bonus Building Damage", t("NEW")))
    W(ul_close())

    # Luna
    W(hero_header("Luna"))
    W(ability("Lunar Orbit", slug="luna_lunar_orbit"))
    W(ul_open())
    W(li("Collision Damage increased from 22/28/34/40% to 28/32/36/40%", b([22, 28, 34, 40], [28, 32, 36, 40])))
    W(li("Formation time decreased from 1.2s to 0.9s", b(1.2, 0.9, l=True)))
    W(li("Rotation Radius decreased from 250 to 225", t("BUFF"),
         extra=inline_note("Not a nerf: combined with the Collision Radius increase, the outer reach is unchanged (250+175 = 225+200 = 425), while the dead zone right next to Luna shrinks from 75 to 25 — coverage shifts closer to her")))
    W(li("Collision Radius increased from 175 to 200", b(175, 200)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent -40s Eclipse Cooldown replaced with +80 Lucent Beam Damage", t("REWORK")))
    W(li("Level 20 Talent +110 Lucent Beam Damage replaced with -40s Eclipse Cooldown", t("REWORK")))
    W(li("Level 25 Talent +1 Lunar Blessing Damage per Level replaced with +30 Lunar Blessing Damage", t("REWORK")))
    W(ul_close())

    # Lycan
    W(hero_header("Lycan"))
    W(ability("Summon Wolves", slug="lycan_summon_wolves"))
    W(ul_open())
    W(li("Wolf Damage decreased from 23/29/35/41/47/53 to 22/28/34/40/46/52", b([23, 29, 35, 41, 47, 53], [22, 28, 34, 40, 46, 52])))
    W(ul_close())
    W(ability("Shapeshift", slug="lycan_shapeshift"))
    W(ul_open())
    W(li("Health Bonus decreased from 250/350/450 to 225/325/425", b([250, 350, 450], [225, 325, 425])))
    W(ul_close())

    # Magnus
    W(hero_header("Magnus"))
    W(ul_open())
    W(li("Base Damage increased by 1", bstat_h("Magnus", "AttackDamageMin", "7.39e", 1), extra=note_box(hero="Magnus", field="AttackDamageMin", before_patch="7.39e")))
    W(li("Damage at level 1 increased from 54–62 to 55–63", br(54, 62, 55, 63)))
    W(ul_close())
    W(facet_header("magnataur_diminishing_return"))
    W(ul_open())
    W(li("Diminishing Return: No longer has decreased number of +2 All Attributes bonuses", t("BUFF")))
    W(ul_close())
    W(ul_open())
    W(li("Reverse Polarity: Cooldown decreased from 120s to 115s", b(120, 115, l=True)))
    W(ul_close())

    # Marci
    W(hero_header("Marci"))
    W(facet_header("marci_fleeting_fury"))
    W(ul_open())
    W(li("Fleeting Fury: Facet removed", t("DEL")))
    W(ul_close())

    # Mars
    W(hero_header("Mars"))
    W(ability("God's Rebuke", slug="mars_gods_rebuke"))
    W(ul_open())
    W(li("Bonus Damage vs Heroes decreased from 10/15/20/25 to 5/10/15/20", b([10, 15, 20, 25], [5, 10, 15, 20])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Arena of Blood Cooldown Reduction decreased from 20s to 16s", b(20, 16)))
    W(ul_close())

    # Medusa
    W(hero_header("Medusa"))
    W(ability("Mana Shield", slug="medusa_mana_shield"))
    W(ul_open())
    W(li("No longer benefits from mana cost reduction effects", t("NERF")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent +1.5s Stone Gaze Duration replaced with +1 Gorgon's Grasp Volley", t("REWORK")))
    W(li("Level 25 Talent +1 Gorgon's Grasp Volley replaced with +2s Stone Gaze Duration", t("REWORK")))
    W(ul_close())

    # Meepo
    W(hero_header("Meepo"))
    W(facet_header("meepo_more_meepo"))
    W(ul_open())
    W(li("More Meepo: No longer has decreased number of +2 All Attributes bonuses", t("BUFF")))
    W(ul_close())

    # Mirana
    W(hero_header("Mirana"))
    W(facet_header("mirana_starstruck"))
    W(ul_open())
    W(li("Starstorm: Second meteor damage decreased from 100% to 70/80/90/100%", b(100, [70, 80, 90, 100])))
    W(ul_close())
    W(ul_open())
    W(li("Starstorm: Second Meteor Damage increased from 60% to 70%", b(60, 70)))
    W(ul_close())
    W(ul_open())
    W(li("Moonlight Shadow: Cooldown decreased from 140/120/100s to 120/110/100s", b([140, 120, 100], [120, 110, 100], l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent -20s Moonlight Shadow Cooldown replaced with +200 Starstorm Damage", t("REWORK")))
    W(li("Level 25 Talent +250 Starstorm Damage replaced with -30s Moonlight Shadow Cooldown", t("REWORK")))
    W(ul_close())

    # Monkey King
    W(hero_header("Monkey King"))
    W(ul_open())
    W(li("Base Armor decreased by 1", bstat_h("Monkey King", "ArmorPhysical", "7.39e", -1), extra=note_box(hero="Monkey King", field="ArmorPhysical", before_patch="7.39e")))
    W(li("Base Attack Time improved from 1.7s to 1.6s", b(1.7, 1.6, l=True)))
    W(li("Base Attack Speed decreased from 100 to 95", b(100, 95)))
    W(ul_close())
    W(facet_header("monkey_king_simian_stride"))
    W(ul_open())
    W(li("Simian Stride: No longer has decreased number of +2 All Attributes bonuses", t("BUFF")))
    W(ul_close())
    W(ul_open())
    W(li("Tree Dance: Stun duration from falling off the cut tree decreased from 4s to 3s", b(4, 3)))
    W(ul_close())

    # Morphling
    W(hero_header("Morphling"))
    W(facet_header("morphling_str"))
    W(ul_open())
    W(li("Adaptive Strike: Stun is no longer exclusive to this facet", t("MISC")))
    W(ul_close())
    W(ul_open())
    W(li("Adaptive Strike: Cast Range decreased from 600/700/800/900 to 600/675/750/825", b([600, 700, 800, 900], [600, 675, 750, 825])))
    W(li("Now stuns the target for 0.5s and up to 1.2/1.6/2.0/2.4s when Morphling's Strength is 50% higher than his Agility", t("NEW")))
    W(ul_close())

    # Muerta
    W(hero_header("Muerta"))
    W(ul_open())
    W(li("Intelligence gain increased from 3.4 to 3.6", b(3.4, 3.6)))
    W(ul_close())
    W(ability("The Calling", slug="muerta_the_calling"))
    W(ul_open())
    W(li("Mana Cost decreased from 140/155/170/185 to 135/150/165/180", b([140, 155, 170, 185], [135, 150, 165, 180], l=True)))
    W(li("Cast Range increased from 580 to 600", b(580, 600)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +150 Health replaced with +20 Attack Speed", t("REWORK")))
    W(ul_close())

    # Naga Siren
    W(hero_header("Naga Siren"))
    W(ul_open())
    W(li("Base Intelligence decreased from 20 to 19", b(20, 19)))
    W(li("Agility gain increased from 3.3 to 3.4", b(3.3, 3.4)))
    W(ul_close())
    W(facet_header("naga_siren_passive_riptide"))
    W(ul_open())
    W(li("Damage increased from 25/35/45/55 to 30/40/50/60", b([25, 35, 45, 55], [30, 40, 50, 60])))
    W(ul_close())
    W(facet_header("naga_siren_active_riptide"))
    W(ul_open())
    W(li("Rip Tide: Cooldown increased from 10/9/8/7s to 13/11/9/7s", b([10, 9, 8, 7], [13, 11, 9, 7], l=True)))
    W(ul_close())
    W(ul_open())
    W(li("Ensnare: Can no longer target invulnerable units unless this invulnerability is provided by Song of the Siren", t("REWORK")))
    W(ul_close())
    W(ul_open())
    W(li("Song of the Siren: Max HP Regen per second decreased from 2/3/4% to 1/2/3%", b([2, 3, 4], [1, 2, 3])))
    W(li("Aghanim's Shard Max HP Regen per second bonus decreased from 2% to 1%", b(2, 1), extra=inline_note("Total Max HP Regen per second with Aghanim's Shard decreased from 4/5/6% to 2/3/4%")))
    W(ul_close())

    # Nature's Prophet
    W(hero_header("Nature's Prophet"))
    W(ul_open())
    W(li("Agility gain decreased from 3 to 2.6", b(3, 2.6)))
    W(li("Damage gain per level decreased from 4.1 to 3.9", b(4.1, 3.9)))
    W(ul_close())
    W(ability("Spirit of the Forest", slug="furion_spirit_of_the_forest"))
    W(ul_open())
    W(li("Bonus damage per tree decreased from 3% to 2%", b(3, 2)))
    W(ul_close())
    W(ability("Nature's Call", slug="furion_force_of_nature"))
    W(ul_open())
    W(li("Mana Cost decreased from 120 to 100", b(120, 100, l=True)))
    W(li("Treant attack range increased from 100 to 125", b(100, 125)))
    W(li("Treant damage increased from 15/23/31/39 to 16/24/32/40", b([15, 23, 31, 39], [16, 24, 32, 40]), extra=inline_note("From 13–17/21–25/29–33/37–41 to 14–18/22–26/30–34/38–42")))
    W(li("Treant movement speed increased from 300 to 305/310/315/320", b(300, [305, 310, 315, 320])))
    W(ul_close())
    W(ability("Curse of the Oldgrowth", slug="furion_curse_of_the_forest"))
    W(ul_open())
    W(li("Curse radius decreased from 1200 to 900", b(1200, 900)))
    W(ul_close())

    # Necrophos
    W(hero_header("Necrophos"))
    W(facet_header("necrolyte_profane_potency"))
    W(ul_open())
    W(li("Sadist: AOE per Kill reduced from 40 to 35", b(40, 35)))
    W(ul_close())
    W(ul_open())
    W(li("Reaper's Scythe: HP Regen per kill decreased from 2/4/6 to 1/2/3", b([2, 4, 6], [1, 2, 3])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Death Pulse Heal increased from +50 to +60", b(50, 60)))
    W(li("Level 15 Talent Ghost Shroud Slow decreased from +20% to +15%", b(20, 15)))
    W(li("Level 20 Talent Heartstopper Regen Reduction decreased from +25% to +20%", b(25, 20)))
    W(ul_close())

    # Night Stalker
    W(hero_header("Night Stalker"))
    W(ability("Heart of Darkness", slug="night_stalker_heart_of_darkness"))  # innate
    W(ul_open())
    W(li("No longer reduces Night Stalker's health regeneration by 20% during the day", t("BUFF")))
    W(ul_close())
    W(facet_header("night_stalker_voidbringer"))
    W(ul_open())
    W(li("Voidbringer: No longer has decreased number of +2 All Attributes bonuses", t("BUFF")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Crippling Fear DPS increased from +20 to +40", b(20, 40)))
    W(ul_close())

    # Nyx Assassin
    W(hero_header("Nyx Assassin"))
    W(ability("Mind Flare", slug="nyx_assassin_jolt"))
    W(ul_open())
    W(li("Bonus Damage decreased from 20% to 15%", b(20, 15)))
    W(ul_close())
    W(ability("Spiked Carapace", slug="nyx_assassin_spiked_carapace"))
    W(ul_open())
    W(li("Stun Duration increased from 0.4/0.8/1.2/1.6s to 0.7/1.0/1.3/1.6s", b([0.4, 0.8, 1.2, 1.6], [0.7, 1.0, 1.3, 1.6])))
    W(ul_close())

    # Ogre Magi
    W(hero_header("Ogre Magi"))
    W(ul_open())
    W(li("Base Damage increased by 1", bstat_h("Ogre Magi", "AttackDamageMin", "7.39e", 1), extra=note_box(hero="Ogre Magi", field="AttackDamageMin", before_patch="7.39e")))
    W(li("Damage at level 1 increased from 69–75 to 70–76", br(69, 75, 70, 76)))
    W(ul_close())
    W(ability("Bloodlust", slug="ogre_magi_bloodlust"))
    W(ul_open())
    W(li("Cast range increased from 600 to 650", b(600, 650)))
    W(li("Can no longer target invulnerable units", t("DEL"), extra=inline_note("Can still target invulnerable buildings (i.e. Tier 2-4 towers when the previous ones are not destroyed)")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Bloodlust Attack Speed increased from +30 to +35", b(30, 35)))
    W(ul_close())

    # Omniknight
    W(hero_header("Omniknight"))
    W(ul_open())
    W(li("Base Armor increased by 1", bstat_h("Omniknight", "ArmorPhysical", "7.39e", 1), extra=note_box(hero="Omniknight", field="ArmorPhysical", before_patch="7.39e")))
    W(ul_close())
    W(ability("Repel", slug="omniknight_martyr"))
    W(ul_open())
    W(li("Cooldown decreased from 55/50/45/40s to 50/45/40/35s", b([55, 50, 45, 40], [50, 45, 40, 35], l=True)))
    W(ul_close())
    W(ability("Hammer of Purity", slug="omniknight_hammer_of_purity"))
    W(ul_open())
    W(li("No longer disabled by Silence", t("MISC")))
    W(ul_close())
    W(ability("Guardian Angel", slug="omniknight_guardian_angel"))
    W(ul_open())
    W(li("Cooldown decreased from 110/100/90s to 100/90/80s", b([110, 100, 90], [100, 90, 80], l=True)))
    W(ul_close())

    # Oracle
    W(hero_header("Oracle"))
    W(ability("Fortune's End", slug="oracle_fortunes_end"))
    W(ul_open())
    W(li("Can no longer target invulnerable units, but does affect invulnerable units in the AoE", t("MISC")))
    W(ul_close())
    W(ability("Fate's Edict", slug="oracle_fates_edict"))
    W(ul_open())
    W(li("No longer has separate effects for allies and enemies", t("REWORK"), extra=inline_note("Always disarms the target and grants them 100% magic damage resistance")))
    W(li("Mana Cost decreased from 95/100/105/110 to 70", b([95, 100, 105, 110], 70, l=True)))
    W(li("Cooldown decreased from 20/17/14/11s to 17/14/11/8s", b([20, 17, 14, 11], [17, 14, 11, 8], l=True)))
    W(ul_close())

    # Pangolier
    W(hero_header("Pangolier"))
    W(facet_header("pangolier_double_jump"))
    W(ul_open())
    W(li("Double Jump: Facet removed", t("DEL")))
    W(ul_close())
    W(facet_header("pangolier_thunderbolt"))
    W(ul_open())
    W(li("Thunderbolt: Facet removed", t("DEL")))
    W(ul_close())
    W(ul_open())
    W(li("Swashbuckle: Cooldown decreased from 21/18/15/12s to 20/17/14/11s", b([21, 18, 15, 12], [20, 17, 14, 11], l=True)))
    W(li("Now briefly slows enemies movespeed on hit by 100% for 0.4s", t("NEW")))
    W(ul_close())
    W(ul_open())
    W(li("Shield Crash: Cooldown decreased from 18/16/14/12s to 16/13/10/7s", b([18, 16, 14, 12], [16, 13, 10, 7], l=True)))
    W(li("Mana Cost rescaled from 70/80/90/100 to 75", b([70, 80, 90, 100], 75, l=True)))
    W(li("Barrier changed from 50/100/150/200 per enemy hero hit to 60/120/180/240 if any enemy hero is hit", t("REWORK"), extra=inline_note("If no enemy hero was hit, barrier is not provided")))
    W(li("Barrier Duration decreased from 10s to 6s", b(10, 6)))
    W(li("Damage decreased from 70/130/190/250 to 50/100/150/200", b([70, 130, 190, 250], [50, 100, 150, 200])))
    W(li("No longer slows enemies", t("DEL")))
    W(li("Aghanim's Scepter Swashbuckle damage decreased from 100% to 75%", b(100, 75)))
    W(ul_close())
    W(ul_open())
    W(li("Rolling Thunder: Duration rescaled from 10s to 9/10/11s", b(10, [9, 10, 11])))
    W(li("No longer decreases the cooldown of Shield Crash", t("DEL")))
    W(li("Now takes 1 second to reach full Roll Speed", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +90 Shield Crash Barrier Per Hero replaced with +125 Shield Crash Barrier", t("REWORK")))
    W(li("Level 15 Talent +15% Attack Damage as Swashbuckle Damage replaced with -2s Swashbuckle Cooldown", t("REWORK")))
    W(li("Level 20 Talent +125 Shield Crash Radius and Damage replaced with -1.5s Shield Crash Cooldown", t("REWORK")))
    W(li("Level 25 Talent -4s Swashbuckle Cooldown replaced with +20% Attack Damage as Swashbuckle Damage", t("REWORK")))
    W(ul_close())

    # Phantom Assassin
    W(hero_header("Phantom Assassin"))
    W(ability("Blur", slug="phantom_assassin_blur"))
    W(ul_open())
    W(li("Active Movement Speed increased from 3/6/9/12% to 6/9/12/15%", b([3, 6, 9, 12], [6, 9, 12, 15])))
    W(ul_close())
    W(ability("Phantom Strike", slug="phantom_assassin_phantom_strike"))
    W(ul_open())
    W(li("11/9/7/5s cooldown replaced with 2 charges with 21/18/15/12s base charge restore time",
         t("REWORK") + b([11, 9, 7, 5], [21, 18, 15, 12], l=True),
         extra=inline_note("% compares time between uses; in exchange Phantom Strike gains a second charge (two casts back-to-back)")))
    W(ul_close())

    # Phantom Lancer
    W(hero_header("Phantom Lancer"))
    W(ul_open())
    W(li("Agility gain increased from 2.8 to 3.4", b(2.8, 3.4)))
    W(ul_close())
    W(facet_header("phantom_lancer_divergence"))
    W(ul_open())
    W(li("Divergence: Facet removed", t("DEL")))
    W(ul_close())
    W(facet_header("phantom_lancer_lancelot"))
    W(ul_open())
    W(li("Lancelot: Facet removed", t("DEL")))
    W(ul_close())
    _ia_pill, _ia_table = scale_pill("18% + 2% per 3 level ups",
                                     lambda L: 18 + 2 * ((L - 1) // 3),
                                     value_fmt="{:.0f}%")
    W(ability_change(
        old=dict(
            name="Illusory Armaments",
            slug="phantom_lancer_illusory_armaments",
            innate=True,
            desc=[
                "Passive.",
                "Bonus attack damage from items is converted into base damage — <b>100%</b> for Phantom Lancer and <b>65%</b> for his illusions — so his illusions benefit from his damage items.",
            ],
        ),
        new=dict(
            name="Illusory Armaments",
            slug="phantom_lancer_illusory_armaments",
            innate=True,
            desc=[
                "Passive.",
                "Whenever an illusion of Phantom Lancer is created, it can't have less than " + _ia_pill + " of Phantom Lancer's damage for 3s.",
            ],
            tables=[_ia_table],
        ),
        summary="Innate reworked.",
        tag="rework",
    ))
    W(ability("Phantom Rush", slug="phantom_lancer_phantom_edge"))
    W(ul_open())
    W(li("No Longer provides bonus Agility while active", t("DEL")))
    W(li("Cooldown rescaled from 13/10/7/4s to 15/11/7/3s", b([13, 10, 7, 4], [15, 11, 7, 3], l=True)))
    W(li("Now provides 20/30/40/50% evasion while rushing", t("NEW")))
    W(li("No longer has a 2s linger effect", t("DEL"), extra=inline_note("Evasion bonus is lost once the target is reached or the rush is cancelled")))
    W(ul_close())
    W(ability("Juxtapose", slug="phantom_lancer_juxtapose"))
    W(ul_open())
    W(li("Illusion Damage decreased from 15/17/19% to 15%", b([15, 17, 19], 15)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +10 Phantom Rush Agility replaced with +3% Juxtapose Illusion Trigger Chance", t("REWORK")))
    W(li("Level 15 Talent -1s Spirit Lance Cooldown replaced with +125 Doppelganger Cast Range", t("REWORK")))
    W(li("Level 15 Talent +2.5s Phantom Rush Bonus Agility Duration replaced with 50% Illusion Spirit Lance Damage", t("REWORK"), extra=inline_note("Spirit Lances fired from illusions deal 50% of the regular damage, which is then further reduced by the illusion's outgoing damage multiplier")))
    W(li("Level 20 Talent +6% Juxtapose Damage replaced with -70% Juxtapose Illusion Damage Taken", t("REWORK")))
    W(li("Level 20 Talent +15% Spirit Lance Illusion Damage replaced with +100 Spirit Lance Damage", t("REWORK")))
    W(li("Level 25 Talent +20% Illusory Armaments Damage replaced with +2s Illusory Armaments Duration", t("REWORK")))
    W(ul_close())

    # Phoenix
    W(hero_header("Phoenix"))
    W(ability("Sun Ray", slug="phoenix_sun_ray"))
    W(ul_open())
    W(li("Health Cost per second decreased from 6% to 5%", b(6, 5, l=True)))
    W(li("Base Damage per second rescaled from 14/20/26/32 to 15/20/25/30", b([14, 20, 26, 32], [15, 20, 25, 30])))
    W(li("Max Damage rescaled from 1.25/2.75/4.5/6.75% to 1.5/3/4.5/6%", b([1.25, 2.75, 4.5, 6.75], [1.5, 3, 4.5, 6])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Health Regen increased from +20 to +25", b(20, 25)))
    W(ul_close())

    # Primal Beast
    W(hero_header("Primal Beast"))
    W(facet_header("primal_beast_ferocity"))
    W(ul_open())
    W(li("Pulverize: AoE bonus per slam decreased from 25% to 20%", b(25, 20)))
    W(ul_close())

    # Puck
    W(hero_header("Puck"))
    W(ability("Puckish", slug="puck_puckish"))
    W(ul_open())
    W(li("No longer applies when disjointing attacks from buildings", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Waning Rift Cooldown Reduction decreased from 3s to 2.5s", b(3, 2.5)))
    W(ul_close())

    # Pugna
    W(hero_header("Pugna"))
    W(facet_header("pugna_siphoning_ward"))
    W(ul_open())
    W(li("Nether Ward: Damage to Heal decreased from 25% to 20%", b(25, 20)))
    W(li("Nether Ward: Damage to Mana decreased from 30% to 20%", b(30, 20)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Health decreased from +350 to +300", b(350, 300)))
    W(li("Level 20 Talent Life Drain Heal decreased from +20% to +15%", b(20, 15)))
    W(li("Level 25 Talent Nether Blast Damage increased from +180 to +200", b(180, 200)))
    W(ul_close())

    # Queen of Pain
    W(hero_header("Queen of Pain"))
    W(facet_header("queenofpain_facet_bondage"))
    W(ul_open())
    W(li("Bondage: Returning Spell Damage decreased from 20% to 16%", b(20, 16)))
    W(ul_close())

    # Razor
    W(hero_header("Razor"))
    W(facet_header("razor_thunderhead"))
    W(ul_open())
    W(li("Eye of the Storm: Storm Surge cooldown reduction decreased from 2.5s to 2s", b(2.5, 2)))
    W(ul_close())
    W(ul_open())
    W(li("Storm Surge: Chance to Strike increased from 18% to 20%", b(18, 20)))
    W(li("Strike Cooldown decreased from 3s to 2.5s", b(3, 2.5, l=True)))
    W(ul_close())

    # Riki
    W(hero_header("Riki"))
    W(facet_header("riki_contract_killer"))
    W(ul_open())
    W(li("Contract Killer: Facet removed", t("DEL")))
    W(ul_close())
    W(facet_header("riki_exterminator"))
    W(ul_open())
    W(li("Exterminator: Facet removed", t("DEL")))
    W(ul_close())
    W(ul_open())
    W(li("Backstab: No longer levels with Cloak and Dagger", t("REWORK")))
    W(li_formula("Agility Damage Multiplier rescaled",
                 "0.55/0.9/1.25/1.6", "0.6 + 0.05 per Riki's level up",
                 lambda L: 1.6, lambda L: 0.6 + 0.05 * L,
                 value_fmt="{:g}"))
    W(li("Now works on allied units at 25% effectiveness", t("NEW")))
    W(li("Damage is now done as a separate instance of damage instead of a part of the attack damage", t("REWORK")))
    W(ul_close())
    W(ul_open())
    W(li("Blink Strike: 2 charges with 25/21/17/13s base restore time replaced with 13/10/7/4s cooldown",
         t("REWORK") + b([25, 21, 17, 13], [13, 10, 7, 4], l=True),
         extra=inline_note("% compares time between uses; note the second charge (burst potential) is gone")))
    W(li("Bonus 40/55/70/85 magic damage replaced with 15/30/45/60 bonus physical damage on attack",
         t("REWORK") + b([40, 55, 70, 85], [15, 30, 45, 60]),
         extra=inline_note("% compares raw numbers; physical damage scales differently (reduced by armor instead of magic resistance)")))
    W(ul_close())
    W(ul_open())
    W(li("Tricks of the Trade: Mana Cost rescaled from 45/55/65/75 to 65", b([45, 55, 65, 75], 65, l=True)))
    W(li("Cooldown increased from 18/16/14/12s to 21/18/15/12s", b([18, 16, 14, 12], [21, 18, 15, 12], l=True)))
    W(li("Radius decreased from 450 to 425", b(450, 425)))
    W(li("40% Attack Damage replaced with 30/50/70/90 flat damage", t("REWORK"), extra=inline_note("Still applies bonus damage from Backstab, but as a separate instance of damage now")))
    W(li("No longer provides bonus Agility", t("DEL")))
    W(li("Now attacks 2 random targets by default", t("NEW")))
    W(li("Aghanim's Scepter slightly reworked", t("REWORK"), extra=inline_note("No longer increases the number of targets attacked")))
    W(li("Now also allows to hide within allied creeps", t("NEW")))
    W(li("Now increases ability duration by 1s and attack count by 2, but only when Riki hides within an ally", t("NEW"), extra=inline_note("No longer increases attack count on non-ally casts")))
    W(li("Now provides 15% bonus movement speed to the ally Riki's hiding in", t("NEW")))
    W(ul_close())
    W(ul_open())
    W(li("Cloak and Dagger: Now grants 130/260/390 experience when getting a hero kill and 100 experience when getting a hero assist", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +50 Tricks of the Trade Agility replaced with 15% of Riki's Base damage added to Tricks of the Trade", t("REWORK")))
    W(li("Level 20 Talent -4s Blink Strike Replenish Time replaced with -1s Blink Strike Cooldown", t("REWORK")))
    W(li("Level 25 Talent Tricks of the Trade Applies a Basic Dispel replaced with +500 Blink Strike Cast Range", t("REWORK")))
    W(ul_close())

    # Ringmaster
    W(hero_header("Ringmaster"))
    W(ability("Wheel of Wonder", slug="ringmaster_wheel"))
    W(ul_open())
    W(li("Mana Cost decreased from 175/275/375 to 150/225/300", b([175, 275, 375], [150, 225, 300], l=True)))
    W(ul_close())

    # Rubick
    W(hero_header("Rubick"))
    W(ul_open())
    W(li("Base damage increased by 1", bstat_h("Rubick", "AttackDamageMin", "7.39e", 1), extra=note_box(hero="Rubick", field="AttackDamageMin", before_patch="7.39e")))
    W(li("Damage at level 1 increased from 49–55 to 50–56", br(49, 55, 50, 56)))
    W(ul_close())
    W(ability("Telekinesis", slug="rubick_telekinesis"))
    W(ul_open())
    W(li("Land sub-ability no longer cancels channeling or interrupts movement", t("MISC")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +0.5s Telekinesis Lift/Stun Duration replaced with +20% Fade Bolt Damage Reduction", t("REWORK")))
    W(ul_close())

    # Sand King
    W(hero_header("Sand King"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Burrowstrike Cooldown Reduction increased from 2s to 3s", b(2, 3)))
    W(li("Level 25 Talent Epicenter Pulses decreased from +10 to +8", b(10, 8)))
    W(ul_close())

    # Shadow Demon
    W(hero_header("Shadow Demon"))
    W(ability("Disruption", slug="shadow_demon_disruption"))
    W(ul_open())
    W(li("Bonus Base Damage decreased from 25/40/55/70 to 20/35/50/65", b([25, 40, 55, 70], [20, 35, 50, 65])))
    W(ul_close())
    W(ability("Demonic Purge", slug="shadow_demon_demonic_purge"))
    W(ul_open())
    W(li("Can no longer target invulnerable units", t("DEL")))
    W(ul_close())
    W(ability("Demonic Cleanse", slug="shadow_demon_demonic_cleanse"))
    W(ul_open())
    W(li("Can no longer target invulnerable units", t("DEL")))
    W(ul_close())

    # Shadow Fiend
    W(hero_header("Shadow Fiend"))
    W(ul_open())
    W(li("Agility gain increased from 3.5 to 3.6", b(3.5, 3.6)))
    W(ul_close())
    W(ability("Necromastery", slug="nevermore_necromastery"))
    W(ul_open())
    W(li("Souls on hero kills increased from 3 to 4", b(3, 4)))
    W(ul_close())

    # Shadow Shaman
    W(hero_header("Shadow Shaman"))
    W(facet_header("shadow_shaman_massive_serpent_ward"))
    W(ul_open())
    W(li("Mass Serpent Ward: Health and bounty multiplier decreased from 10x to 9x", b(10, 9), extra=inline_note("Hits to destroy decreased from 20 to 18, Gold Bounty decreased from 220–300 to 198–270, XP Bounty decreased from 310 to 279")))
    W(ul_close())
    W(ul_open())
    W(li("Shackles: Total Damage/Heal increased from 70/140/210/280 to 100/160/220/280", b([70, 140, 210, 280], [100, 160, 220, 280])))
    W(ul_close())
    W(ul_open())
    W(li("Mass Serpent Ward: Cooldown decreased from 110s to 110/105/100s", b(110, [110, 105, 100], l=True)))
    W(ul_close())

    # Silencer
    W(hero_header("Silencer"))
    W(facet_header("silencer_spread_the_knowledge"))
    W(ul_open())
    W(li("Synaptic Split: No longer has decreased number of +2 All Attributes bonuses", t("BUFF")))
    W(ul_close())
    W(ul_open())
    W(li("Arcane Curse: Silenced Multiplier decreased from 1.5 to 1.25", b(1.5, 1.25)))
    W(ul_close())
    W(ul_open())
    W(li("Glaives of Wisdom: Int Steal increased from 1/2/3/4 to 2/3/4/5", b([1, 2, 3, 4], [2, 3, 4, 5])))
    W(li("Int Steal Duration rescaled from 20/25/30/35s to 10/20/30/40s", b([20, 25, 30, 35], [10, 20, 30, 40])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Arcane Curse Penalty Multiplier decreased from +0.5 to +0.25", b(0.5, 0.25)))
    W(ul_close())

    # Skywrath Mage
    W(hero_header("Skywrath Mage"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Ancient Seal Cooldown Reduction decreased from 7s to 6s", b(7, 6)))
    W(li("Level 15 Talent Concussive Shot Slow increased from +15% to +20%", b(15, 20)))
    W(ul_close())

    # Slardar
    W(hero_header("Slardar"))
    W(ability("Slithereen Crush", slug="slardar_slithereen_crush"))
    W(ul_open())
    W(li("Puddle radius increased from 250 to 325", b(250, 325)))
    W(li("Aghanim's Scepter Crush puddle radius decreased from 450 to 400", b(450, 400)))
    W(ul_close())
    W(ability("Bash of the Deep", slug="slardar_bash"))
    W(ul_open())
    W(li("Bash Duration decreased from 1.1s to 1s", b(1.1, 1)))
    W(li("Bonus Damage decreased from 50/100/150/200 to 35/90/145/200", b([50, 100, 150, 200], [35, 90, 145, 200])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Seaborn Sentinel Bonus Damage increased from +12 to +14", b(12, 14)))
    W(ul_close())

    # Slark
    W(hero_header("Slark"))
    W(facet_header("slark_leeching_leash"))
    W(ul_open())
    W(li("Leeching Leash: Facet removed", t("DEL")))
    W(ul_close())
    W(facet_header("slark_dark_reef_renegade"))
    W(ul_open())
    W(li("Dark Reef Renegade: Facet removed", t("DEL")))
    W(ul_close())
    W(ul_open())
    W(li("Barracuda: Innate ability removed", t("DEL"), extra=inline_note("Effect moved to the Ultimate")))
    W(ul_close())
    W(ul_open())
    W(li("Essence Shift: Now an innate ability. Passive, improves with Slark's level", t("NEW")))
    W(li_formula("Duration rescaled",
                 "15/35/55/75s", "15s + 2.5s each time Slark levels up",
                 lambda L: 75, lambda L: 15 + 2.5 * (L - 1),
                 value_fmt="{:g}s"))
    W(ul_close())
    W(ul_open())
    W(li("Pounce: Now applies 1/2/3/4 Essence Shift stacks when leashing an enemy hero", t("NEW")))
    W(ul_close())
    W(ability_change(
        old=None,
        new=dict(
            name="Saltwater Shiv",
            slug="slark_saltwater_shiv",
            desc=[
                "New basic ability — passive, auto-cast attack modifier.",
                "Slark slices the target with his salty shiv, stealing <b>3 Movement Speed</b>, <b>3 Health Regen</b> and <b>3/4/5/6% Health Restoration</b> from them with each attack. Subsequent uses refresh the duration of all shiv stacks. Steal duration: 6/8/10/12s. Mana Cost: 20. Cooldown: 10/8/6/4s."
                + inline_note("Not Breakable. Disabled by Silence. Has no stack limit. Ignores attack backswing. Enemies with Health Restoration below −100% will not lose health from health-restoration sources."),
            ],
        ),
        summary="New ability.",
        tag="new",
    ))
    W(ability("Shadow Dance", slug="slark_shadow_dance"))
    W(ul_open())
    W(li("Now passively grants 24/36/48% movement speed and 60/90/120 health regen when unseen", t("NEW"), extra=inline_note("Previous Barracuda rules and mechanics unchanged")))
    W(ul_close())
    W(ability("Depth Shroud", slug="slark_depth_shroud"))
    W(ul_open())
    W(li("Duration decreased from 3s to 2s", b(3, 2)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Dark Pact Cooldown Reduction increased from 0.5s to 0.75s", b(0.5, 0.75)))
    W(li("Level 15 Talent +50 Barracuda Regen replaced with +30 Shadow Dance Regen", t("REWORK")))
    W(li("Level 25 Talent Shadow Dance Duration increased from +1.25s to +1.5s", b(1.25, 1.5)))
    W(ul_close())

    # Snapfire
    W(hero_header("Snapfire"))
    W(ability("Buckshot", innate=True))
    W(ul_open())
    W(li("Now affects only attacks made on enemy heroes", t("MISC"), extra=inline_note("Attacks on non-heroes can still ricochet on miss, but they won't have extra damage or glance chance")))
    W(ul_close())
    W(ability("Firesnap Cookie", slug="snapfire_firesnap_cookie"))
    W(ul_open())
    W(li("Mana Cost increased from 85/90/95/100 to 105", b([85, 90, 95, 100], 105, l=True)))
    W(li("Aghanim's Shard Mortimer Kiss damage decreased from 50% to 40%", b(50, 40)))
    W(ul_close())
    W(ability("Lil' Shredder", slug="snapfire_lil_shredder"))
    W(ul_open())
    W(li("Base Damage per shot decreased from 25/40/55/70 to 20/35/50/65", b([25, 40, 55, 70], [20, 35, 50, 65])))
    W(ul_close())

    # Sniper
    W(hero_header("Sniper"))
    W(ability("Assassinate", slug="sniper_assassinate"))
    W(ul_open())
    W(li("Can no longer target invulnerable units", t("DEL")))
    W(li("Attack Damage increased from 100% to 100/110/120%", b(100, [100, 110, 120])))
    W(ul_close())

    # Spectre
    W(hero_header("Spectre"))
    W(ul_open())
    W(li("Now an Agility Hero", t("NEW"), extra=inline_note("Base attributes and attribute gains are unchanged")))
    W(li("Base Damage increased by 2", t("MISC") + bstat_h("Spectre", "AttackDamageMin", "7.39e", 2), extra=note_box(hero="Spectre", field="AttackDamageMin", before_patch="7.39e", extra_note="Damage at level 1 unchanged (48–52)")))
    W(li("Damage gain per level decreased from +2.8 to +2.1", b(2.8, 2.1)))
    W(li("Damage at level 30 decreased by 27 (from 149–153 to 122–126)", br(149, 153, 122, 126)))
    W(li("Base Attack Time worsened from 1.7s to 1.8s", b(1.7, 1.8, l=True)))
    W(li("Base Attack Speed increased from 90 to 110", b(90, 110)))
    W(ul_close())
    W(facet_header("spectre_forsaken"))
    W(ul_open())
    W(li("Forsaken: Facet removed", t("DEL")))
    W(ul_close())
    W(facet_header("spectre_twist_the_knife"))
    W(ul_open())
    W(li("Twist the Knife: Facet removed", t("DEL")))
    W(ul_close())
    W(ul_open())
    W(li("Spectral: Innate ability removed", t("DEL")))
    W(ul_close())
    W(ul_open())
    W(li("Desolate: Now an innate ability. Passive, improves with Spectre's level", t("NEW")))
    W(li_formula("Damage rescaled",
                 "25/40/55/70", "25 + 2 every time Spectre levels up",
                 lambda L: 70, lambda L: 25 + 2 * (L - 1),
                 value_fmt="{:g}"))
    W(ul_close())
    W(ul_open())
    W(li("Spectral Dagger: Mana Cost decreased from 110/120/130/140 to 100/110/120/130", b([110, 120, 130, 140], [100, 110, 120, 130], l=True)))
    W(li("Spectre's illusions now also benefit from the Shadow Path", t("NEW")))
    W(ul_close())
    W(ability_change(
        old=dict(
            name="Shadow Step",
            slug="spectre_shadow_step",
            desc=[
                "Ultimate.",
                "Spectre performs a single-target Haunt, creating an uncontrollable illusion that attacks the target for <b>40/60/80%</b> of her damage and takes 200% damage. Duration: 5/6/7s. Mana Cost: 150. Cooldown: 80/60/40s.",
                "The Reality sub-ability teleports Spectre to the illusion.",
            ],
        ),
        new=dict(
            name="Shadow Step",
            slug="spectre_shadow_step",
            desc=[
                "Basic ability.",
                "Thrusts an uncontrollable illusion that follows the target and attacks it for <b>20/30/40/50%</b> of Spectre's damage. The illusion exists for <b>3.5/4/4.5/5s</b> and takes 200% damage. On cast it moves at 900 speed, then at 135% of Spectre's movement speed after reaching the target. Cast Range: 700/850/1000/1150. Mana Cost: 60/65/70/75. Cooldown: 32/28/24/20s.",
                "The Reality sub-ability may be used to teleport to the illusion, destroying it.",
            ],
        ),
        summary="Ability reworked.",
        tag="rework",
    ))
    W(ability("Dispersion", slug="spectre_dispersion"))
    W(ul_open())
    W(li("Min Radius increased from 300 to 350", b(300, 350)))
    W(ul_close())
    W(ability("Reality", slug="spectre_reality"))
    W(ul_open())
    W(li("Can no longer be cast to no effect", t("QoL")))
    W(li("Now has a distinct sound between casts on Shadow Step and Haunt illusions", t("QoL")))
    W(li("Mana Cost decreased from 40 to 25", b(40, 25, l=True)))
    W(li("Now has a 0.2s travel time to reach the target. The illusion and Spectre are invulnerable during this time", t("NEW")))
    W(li("Now disabled by roots", t("NEW")))
    W(li("Now always destroys the target illusion", t("NEW")))
    W(ul_close())
    W(ability("Haunt", slug="spectre_haunt"))
    W(ul_open())
    W(li("Now Spectre's ultimate ability", t("NEW")))
    W(li("Mana Cost rescaled from 150 to 125/150/175", b(150, [125, 150, 175], l=True, force_overall="buff")))
    W(li("Duration rescaled from 6s to 5/6/7s", b(6, [5, 6, 7])))
    W(li("Cooldown rescaled from 160s to 180/160/140s", b(160, [180, 160, 140], l=True)))
    W(li("Haunt Outgoing Damage decreased from 80% to 30/55/80%", b(80, [30, 55, 80])))
    W(li("Each illusion now spawns from the direction closest to Spectre", t("MISC")))
    W(li("Aghanim's Scepter: Reduces Haunt cooldown by 20s. When Reality is used on Haunt illusion for the first time per Haunt cast, enemies are Feared away from Spectre for 1.5s with 50% reduced move speed in a 400 AoE around the targeted illusion", t("NEW")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +5 Health Regen replaced with +10 Desolate Damage", t("REWORK")))
    W(li("Level 15 Talent +15 Desolate Damage replaced with +1s Shadow Step Duration", t("REWORK")))
    W(li("Level 20 Talent Spectral Dagger Slow/Bonus increased from +12% to +15%", b(12, 15)))
    W(li("Level 25 Talent All Spectre Illusion Damage decreased from +25% to +20%", b(25, 20)))
    W(ul_close())

    # Spirit Breaker
    W(hero_header("Spirit Breaker"))
    W(ability("Charge of Darkness", slug="spirit_breaker_charge_of_darkness"))
    W(ul_open())
    W(li("Stun Duration increased from 1.2/1.5/1.8/2.1s to 1.3/1.6/1.9/2.2s", b([1.2, 1.5, 1.8, 2.1], [1.3, 1.6, 1.9, 2.2])))
    W(li("Aghanim's Shard bonus speed decreased from +100 to +85", b(100, 85)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Bulldoze barrier decreased from 400 to 375", b(400, 375)))
    W(ul_close())

    # Storm Spirit
    W(hero_header("Storm Spirit"))
    W(ability("Galvanized", slug="storm_spirit_galvanized"))
    W(ul_open())
    W(li("Charge loss on death decreased from 3 to 2", b(3, 2, l=True)))
    W(ul_close())
    W(ability("Overload", slug="storm_spirit_overload"))
    W(ul_open())
    W(li("Attack Speed Slow increased from 80 to 90", b(80, 90)))
    W(ul_close())

    # Sven
    W(hero_header("Sven"))
    W(ability("Storm Hammer", slug="sven_storm_bolt"))
    W(ul_open())
    W(li("Aghanim's Scepter no longer allows targeting invulnerable units, but still affects invulnerable units in the radius", t("DEL")))
    W(li("Aghanim's Scepter cast range bonus changed from +350 to +25%", b(350, 150), extra=inline_note("Decreased from +350 to +150")))
    W(li("Aghanim's Scepter now also increases projectile speed by 25%", b(1000, 1250), extra=inline_note("From 1000 to 1250")))
    W(ul_close())
    W(ability("Great Cleave", slug="sven_great_cleave"))
    W(ul_open())
    W(li("Cleave damage rescaled from 50/65/80/95% to 60/70/80/90%", b([50, 65, 80, 95], [60, 70, 80, 90])))
    W(ul_close())
    W(ability("Warcry", slug="sven_warcry"))
    W(ul_open())
    W(li("Cooldown decreased from 40/35/30/25 to 36/32/28/24", b([40, 35, 30, 25], [36, 32, 28, 24], l=True)))
    W(ul_close())

    # Techies
    W(hero_header("Techies"))
    W(ul_open())
    W(li("Base Agility increased from 14 to 16", b(14, 16)))
    W(li("Damage at level 1 increased by 1 (from 46–48 to 47–49)", br(46, 48, 47, 49)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent +125 Sticky Bomb Latch/Explosion Radius replaced with +160 Sticky Bomb Damage", t("REWORK")))
    W(ul_close())

    # Templar Assassin
    W(hero_header("Templar Assassin"))
    W(ability("Meld", slug="templar_assassin_meld"))
    W(ul_open())
    W(li("Armor Reduction decreased from 3.5/5/6.5/8 to 2/4/6/8", b([3.5, 5, 6.5, 8], [2, 4, 6, 8])))
    W(li("Damage decreased from 55/105/155/205 to 50/100/150/200", b([55, 105, 155, 205], [50, 100, 150, 200])))
    W(ul_close())
    W(ability("Psionic Trap", slug="templar_assassin_psionic_trap"))
    W(ul_open())
    W(li("Damage rescaled from 225/300/375 to 200/300/400", b([225, 300, 375], [200, 300, 400])))
    W(ul_close())
    W(ability("Psionic Projection", slug="templar_assassin_trap_teleport"))
    W(ul_open())
    W(li("Damage increased from 375 to 400", b(375, 400)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Meld Debuff Duration decreased from +2s to +1.5s", b(2, 1.5)))
    W(li("Level 10 Talent Psionic Trap Slow increased from +5% to +10%", b(5, 10)))
    W(ul_close())

    # Terrorblade
    W(hero_header("Terrorblade"))
    W(ability("Dark Unity", slug="terrorblade_dark_unity"))
    W(ul_open())
    W(li("Illusions that are outside 1200 radius no longer have a damage penalty", t("NEW")))
    W(li("Damage increase for illusions within 1200 radius increased from 25% to 60%", b(25, 60)))
    W(ul_close())
    W(ability("Reflection", slug="terrorblade_reflection"))
    W(ul_open())
    W(li("Reflection Damage decreased from 40/60/80/100% to 30/45/60/75%", b([40, 60, 80, 100], [30, 45, 60, 75])))
    W(ul_close())
    W(ability("Conjure Image", slug="terrorblade_conjure_image"))
    W(ul_open())
    W(li("Illusion Damage decreased from 30/40/50/60% to 20/25/30/35%", b([30, 40, 50, 60], [20, 25, 30, 35])))
    W(ul_close())

    # Tidehunter
    W(hero_header("Tidehunter"))
    W(ability("Gush", slug="tidehunter_gush"))
    W(ul_open())
    W(li("Damage rescaled from 110/160/210/260 to 100/160/220/280", b([110, 160, 210, 260], [100, 160, 220, 280])))
    W(ul_close())
    W(ability("Anchor Smash", slug="tidehunter_anchor_smash"))
    W(ul_open())
    W(li("Attack Bonus Damage increased from 45/90/135/180 to 50/100/150/200", b([45, 90, 135, 180], [50, 100, 150, 200])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Gush Slow increased from +15% to +20%", b(15, 20)))
    W(li("Level 10 Talent +40 Anchor Smash Damage replaced with +20% Anchor Smash Damage Reduction", t("REWORK")))
    W(li("Level 15 Talent +30% Anchor Smash Damage Reduction replaced with -15s Ravage Cooldown", t("REWORK")))
    W(li("Level 20 Talent Anchor Smash affects buildings replaced with Blubber effect triggers Anchor Smash", t("REWORK")))
    W(li("Level 25 Talent 50% chance of Anchor Smash on attack replaced with Anchor Smash affects buildings", t("REWORK")))
    W(li("Level 25 Talent Ravage Stun Duration increased from +0.8s to +1s", b(0.8, 1)))
    W(ul_close())

    # Timbersaw
    W(hero_header("Timbersaw"))
    W(ul_open())
    W(li("Base Movement Speed decreased from 285 to 280", b(285, 280)))
    W(ul_close())
    W(ability("Whirling Death", slug="shredder_whirling_death"))
    W(ul_open())
    W(li("Tree Bonus Damage decreased from 11/18/25/32 to 9/16/23/30", b([11, 18, 25, 32], [9, 16, 23, 30])))
    W(ul_close())
    W(ability("Reactive Armor", slug="shredder_reactive_armor"))
    W(ul_open())
    W(li("Max Stacks decreased from 12/22/32/42 to 10/20/30/40", b([12, 22, 32, 42], [10, 20, 30, 40])))
    W(li("Aghanim's Scepter base barrier decreased from 200 to 150", b(200, 150)))
    W(ul_close())

    # Tinker
    W(hero_header("Tinker"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Manacost/Manaloss Reduction increased from +8% to +10%", b(8, 10, l=True)))
    W(li("Level 25 Talent +10s Defense Matrix Duration replaced with +40 Intelligence", t("REWORK")))
    W(ul_close())

    # Tiny
    W(hero_header("Tiny"))
    W(ul_open())
    W(li("Strength gain increased from 4.0 to 4.2", b(4, 4.2)))
    W(ul_close())
    W(ability("Avalanche", slug="tiny_avalanche"))
    W(ul_open())
    W(li("Stun duration now applies its stun as an aura in the area", t("REWORK"), extra=inline_note("As a result, no longer affected by status resistance")))
    W(ul_close())
    W(ability("Tree Throw", slug="tiny_toss_tree"))
    W(ul_open())
    W(li("No longer has separate damage bonus, uses Tree Grab's value instead", t("BUFF"), extra=inline_note("Bonus damage rescaled from 20 to 10/20/30/40 " + b(20, [10, 20, 30, 40]))))
    W(ul_close())
    W(ability("Grow", slug="tiny_grow"))
    W(ul_open())
    W(li("Movement Speed Bonus rescaled from 15 to 10/15/20", b(15, [10, 15, 20])))
    W(ul_close())

    # Treant Protector
    W(hero_header("Treant Protector"))
    W(facet_header("treant_primeval_power"))
    W(ul_open())
    W(li("Primeval Power: Facet removed", t("DEL")))
    W(ul_close())
    W(facet_header("treant_sapling"))
    W(ul_open())
    W(li("Sapling: Facet removed", t("DEL")))
    W(ul_close())
    W(ul_open())
    W(li("Nature's Guise: No longer upgraded with Aghanim's Shard", t("DEL")))
    W(li("Now can be activated while tree walking to make Treant Protector invisible until he attacks or loses the Nature's Guise buff", t("NEW"), extra=inline_note("Linger time: 2s. No Mana Cost. Cooldown: 50s. Cooldown is reduced by 3s per 2 Treant Protector's level ups<br>Cooldown starts when the invisibility ends")))
    W(ul_close())
    W(ul_open())
    W(li("Nature's Grasp: No longer does 50% more damage and slow when touching a tree", t("DEL")))
    W(li("Damage per second increased from 30/40/50/60 to 35/50/65/80", b([30, 40, 50, 60], [35, 50, 65, 80])))
    W(li("Movement Slow increased from 20/25/30/35% to 25/30/35/40%", b([20, 25, 30, 35], [25, 30, 35, 40])))
    W(li("Creep penalty decreased from 50% to 35%", b(50, 35)))
    W(ul_close())
    W(ability_change(
        old=dict(
            name="Leech Seed",
            slug="treant_leech_seed",
            desc=[
                "Active.",
                "Plants a leeching seed in an enemy unit, slowing it (decaying over the duration) and dealing <b>15/30/45/60</b> damage per second for 6 seconds. The leeched life heals nearby allied units (50% effectiveness on creeps).",
            ],
        ),
        new=dict(
            name="Leech Seed",
            slug="treant_leech_seed",
            desc=[
                "Passive, auto-cast attack modifier.",
                "Treant Protector's attack plants a life-sapping seed in an enemy unit, dealing an extra <b>20/40/60/80</b> magic damage. The enemy is bound for <b>0.9/1.1/1.3/1.5s</b> and emits two healing pulses — one upon application and one upon expiration — healing up to 5 allies within 650 units for <b>15/25/35/45</b> + 20% of the damage dealt by the attack. No Mana Cost. Cooldown: 15/12/9/6s. Breakable."
                + inline_note("Now only sends out a maximum of 5 heals per pulse, prioritizing heroes."),
            ],
        ),
        summary="Ability reworked.",
        tag="rework",
    ))
    W(ul_open())
    W(li("No longer has a creep penalty for healing", t("BUFF")))
    W(ul_close())
    W(ability("Living Armor", slug="treant_living_armor"))
    W(ul_open())
    W(li("No longer grants bonus armor", t("DEL")))
    W(li("Now grants 100 damage block from player-controlled sources. Each time this spell blocks damage the effect is decreased by 35/30/25/20", t("NEW"), extra=inline_note("Damage block affects any types of damage<br>The heal ends earlier if the damage block is reduced to 0<br>Instances of less than 20 damage are ignored by Living Armor. They are neither blocked nor counted towards block decrease")))
    W(li("Duration decreased from 18/22/26/30s to 12s", b([18, 22, 26, 30], 12)))
    W(li("Heal per second increased from 3/4/5/6 to 4/7/10/13", b([3, 4, 5, 6], [4, 7, 10, 13])))
    W(ul_close())
    W(ability("Overgrowth", slug="treant_overgrowth"))
    W(ul_open())
    W(li("Aghanim's Scepter: Decreases cooldown from 110/100/90 to 80/70/60s. When casting Overgrowth, Treant Protector draws power from the earth, becoming massive for 16 seconds, gaining +100% Strength, Phased Movement, and a Splashing Attack that deals 60% of attack damage in a 300 unit radius. While large, he has a fixed movement speed of 345. Buff is undispellable", t("NEW")))
    W(ul_close())
    W(ability("Eyes In The Forest", slug="treant_eyes_in_the_forest"))
    W(ul_open())
    W(li("Now granted by Aghanim's Shard", t("NEW")))
    W(li("Mana Cost decreased from 100 to 30", b(100, 30, l=True)))
    W(li("Cast Range increased from 160 to 350", b(160, 350)))
    W(li("Overgrowth is no longer applied around enchanted trees", t("DEL")))
    W(li("Enchanted trees now have the same health as Observer Wards, and they expire after 5 minutes", t("REWORK"), extra=inline_note("Trees can be attacked when revealed by True Sight. Attacks will remove the ability effect from the tree without destroying the tree itself")))
    W(li("Charge Restore Time increased from 40s to 55s", b(40, 55, l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +2.5% Nature's Guise Movement Speed replaced with +50 Base Damage", t("REWORK")))
    W(li("Level 10 Talent Living Armor Heal Per Second increased from +2 to +4", b(2, 4)))
    W(li("Level 15 Talent +18% Leech Seed Movement Slow replaced with +10% Leech Seed Damage to Healing", t("REWORK")))
    W(li("Level 20 Talent Leech Seed Bonus Damage increased from +45 to +80", b(45, 80)))
    W(li("Level 20 Talent +8 Living Armor Bonus Armor replaced with +20 Living Armor Damage Block", t("REWORK")))
    W(li("Level 25 Talent -35s Overgrowth Cooldown replaced with -3s Leech Seed Cooldown", t("REWORK")))
    W(ul_close())

    # Troll Warlord
    W(hero_header("Troll Warlord"))
    W(ability("Berserker's Rage", slug="troll_warlord_berserkers_rage"))
    W(ul_open())
    W(li("Bonus Armor increased from 2/3/4/5 to 3/4/5/6", b([2, 3, 4, 5], [3, 4, 5, 6])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Whirling Axes damage increased from +100 to +115", b(100, 115)))
    W(li("Level 20 Talent Berserker's Rage Armor increased from +9 to +10", b(9, 10)))
    W(ul_close())

    # Tusk
    W(hero_header("Tusk"))
    W(ability("Snowball", slug="tusk_snowball"))
    W(ul_open())
    W(li("Gather Radius decreased from 350 to 325", b(350, 325)))
    W(ul_close())
    W(ability("Walrus PUNCH!", slug="tusk_walrus_punch"))
    W(ul_open())
    W(li("Bonus Damage increased from 50/75/100 to 60/90/120", b([50, 75, 100], [60, 90, 120])))
    W(ul_close())

    # Underlord
    W(hero_header("Underlord"))
    W(ul_open())
    W(li("Strength gain increased from 3.0 to 3.2", b(3, 3.2)))
    W(li("Base Intelligence increased from 17 to 18", b(17, 18)))
    W(ul_close())
    W(ability("Firestorm", slug="abyssal_underlord_firestorm"))
    W(ul_open())
    W(li("Cast Range increased from 600/625/650/675 to 675", b([600, 625, 650, 675], 675)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Pit of Malice Slow decreased from +25% to +20%", b(25, 20)))
    W(li("Level 25 Talent Fiend's Gate DPS increased from 100 to 125", b(100, 125)))
    W(ul_close())

    # Undying
    W(hero_header("Undying"))
    W(ability("Soul Rip", slug="undying_soul_rip"))
    W(ul_open())
    W(li("Cooldown decreased from 18/14/10/6s to 15/12/9/6s", b([18, 14, 10, 6], [15, 12, 9, 6], l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Soul Rip Damage/Heal increased from +10 to +12", b(10, 12)))
    W(ul_close())

    # Ursa
    W(hero_header("Ursa"))
    W(ability("Earthshock", slug="ursa_earthshock"))
    W(ul_open())
    W(li("Aghanim's Shard reworked: Applies 3 Fury Swipe stacks to each affected enemy", t("REWORK")))
    W(ul_close())
    W(ability("Enrage", slug="ursa_enrage"))
    W(ul_open())
    W(li("Cooldown decreased from 70/50/30s to 60/45/30s", b([70, 50, 30], [60, 45, 30], l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Earthshock applies 2 Fury Swipes replaced with +0.5% Maul Health as Damage", t("REWORK")))
    W(ul_close())

    # Vengeful Spirit
    W(hero_header("Vengeful Spirit"))
    W(ability("Magic Missile", slug="vengefulspirit_magic_missile"))
    W(ul_open())
    W(li("Cooldown rescaled from 16/14/12/10s to 14/13/12/11s", b([16, 14, 12, 10], [14, 13, 12, 11], l=True)))
    W(ul_close())
    W(ability("Nether Swap", slug="vengefulspirit_nether_swap"))
    W(ul_open())
    W(li("Can no longer target invulnerable units", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Wave of Terror Armor Reduction decreased from +4 to +3", b(4, 3)))
    W(ul_close())

    # Venomancer
    W(hero_header("Venomancer"))
    W(facet_header("venomancer_plague_carrier"))
    W(ul_open())
    W(li("Venomous Gale: Plague Wards created by Venomous Gale have 75% health and damage", t("REWORK")))
    W(ul_close())
    W(ul_open())
    W(li("Septic Shock: Base Damage per Debuff decreased from 10% to 8%", b(10, 8)))
    W(ul_close())

    # Viper
    W(hero_header("Viper"))
    W(facet_header("viper_caustic_bath"))
    W(ul_open())
    W(li("Corrosive Skin: Time to max effect increased from 4s to 5s", b(4, 5, l=True)))
    W(ul_close())
    W(ul_open())
    W(li("Poison Attack: Mana Cost decreased from 22 to 20", b(22, 20, l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Predator Damage Per Missing Health increased from +0.2 to +0.25", b(0.2, 0.25)))
    W(ul_close())

    # Visage
    W(hero_header("Visage"))
    W(ability("Grave Chill", slug="visage_grave_chill"))
    W(ul_open())
    W(li("Move Speed Drain increased from 12/16/20/24% to 12/18/24/30%", b([12, 16, 20, 24], [12, 18, 24, 30])))
    W(ul_close())
    W(ability("Gravekeeper's Cloak", slug="visage_gravekeepers_cloak"))
    W(ul_open())
    W(li("Familiars now have their own copy of Gravekeeper's Cloak ability (visual change only)", t("QoL")))
    W(ul_close())
    W(ability("Summon Familiars", slug="visage_summon_familiars"))
    W(ul_open())
    W(li("Familiars now have their own ability to independently recall it to Visage", t("MISC"), extra=inline_note("The alt cast behavior on Visage is unchanged")))
    W(li("The 3rd Familiar gained by Level 25 Talent is now automatically added to an existing control group when created", t("QoL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent +15 Gravekeeper's Cloak Armor replaced with -2s Gravekeeper's Cloak Recovery Time", t("REWORK")))
    W(ul_close())

    # Void Spirit
    W(hero_header("Void Spirit"))
    W(ability("Resonant Pulse", slug="void_spirit_resonant_pulse"))
    W(ul_open())
    W(li("Aghanim's Scepter Silence duration decreased from 2.0 to 1.75s", b(2, 1.75)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Aether Remnant damage increased from +60 to +65", b(60, 65)))
    W(ul_close())

    # Warlock
    W(hero_header("Warlock"))
    W(ability("Chaotic Offering", slug="warlock_rain_of_chaos"))
    W(ul_open())
    W(li("Cooldown increased from 160s to 165s", b(160, 165, l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Upheaval Attack Speed per second on Allies decreased from +10 to +8", b(10, 8)))
    W(li("Level 20 Talent Summons a Golem on Death replaced with +25% Damage Resistance for Chaotic Offering Golems", t("REWORK")))
    W(li("Level 25 Talent +80% Golem Magic Resistance replaced with +3 Fatal Bonds targets", t("REWORK")))
    W(li("Level 25 Talent +20 Chaotic Offering Golems Armor replaced with Summons a Golem on Death", t("REWORK")))
    W(ul_close())

    # Weaver
    W(hero_header("Weaver"))
    W(ability("The Swarm", slug="weaver_the_swarm"))
    W(ul_open())
    W(li("Attack Damage increased from 18/22/26/30 to 18/23/28/33", b([18, 22, 26, 30], [18, 23, 28, 33])))
    W(ul_close())
    W(ability("Time Lapse", slug="weaver_time_lapse"))
    W(ul_open())
    W(li("Aghanim's Scepter now also reduces Cooldown by 10s", t("NEW")))
    W(ul_close())

    # Windranger
    W(hero_header("Windranger"))
    W(ul_open())
    W(li("Agility gain increased from 1.9 to 2.1", b(1.9, 2.1)))
    W(li("Damage gain per level increased from 3.5 to 3.6", b(3.5, 3.6)))
    W(ul_close())
    W(ability("Gale Force", slug="windrunner_gale_force"))
    W(ul_open())
    W(li("Duration decreased from 3.5s to 3s", b(3.5, 3)))
    W(ul_close())

    # Winter Wyvern
    W(hero_header("Winter Wyvern"))
    W(ul_open())
    W(li("Base damage increased by 1", bstat_h("Winter Wyvern", "AttackDamageMin", "7.39e", 1), extra=note_box(hero="Winter Wyvern", field="AttackDamageMin", before_patch="7.39e")))
    W(li("Damage at level 1 increased from 41–48 to 42–49", br(41, 48, 42, 49)))
    W(li("Base Attack Range increased from 425 to 450", b(425, 450)))
    W(ul_close())
    W(ability("Arctic Burn", slug="winter_wyvern_arctic_burn"))
    W(ul_open())
    W(li("Bonus Attack Range decreased from 275/300/325/350 to 250/275/300/325", b([275, 300, 325, 350], [250, 275, 300, 325])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Winter's Curse Attack Speed increased from +55 to +60", b(55, 60)))
    W(ul_close())

    # Witch Doctor
    W(hero_header("Witch Doctor"))
    W(facet_header("witch_doctor_malpractice"))
    W(ul_open())
    W(li("Maledict: Burst damage does not apply from non-hero units", t("NERF")))
    W(ul_close())
    W(ul_open())
    W(li("Voodoo Restoration: Activation mana cost decreased from 35/40/45/50 to 25", b([35, 40, 45, 50], 25, l=True)))
    W(li("Mana per second rescaled from 8/12/16/20 to 9/12/15/18", b([8, 12, 16, 20], [9, 12, 15, 18])))
    W(ul_close())
    W(ul_open())
    W(li("Maledict: Now also affects player-controlled creeps", t("NEW")))
    W(ul_close())
    W(ul_open())
    W(li("Death Ward: Aghanim's Scepter bounce radius decreased from 650 to 575", b(650, 575)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent +125 Maledict AoE replaced with +4s Maledict Duration", t("REWORK")))
    W(li("Level 25 Talent +8s Maledict Duration replaced with -6s Paralyzing Cask Cooldown", t("REWORK")))
    W(ul_close())

    # Wraith King
    W(hero_header("Wraith King"))
    W(ability("Wraithfire Blast", slug="skeleton_king_hellfire_blast"))
    W(ul_open())
    W(li("Impact Damage increased from 75/90/105/120 to 80/100/120/140", b([75, 90, 105, 120], [80, 100, 120, 140])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Health decreased from +400 to +350", b(400, 350)))
    W(li("Level 20 Talent Attack Speed decreased from +60 to +50", b(60, 50)))
    W(ul_close())

    # Zeus
    W(hero_header("Zeus"))
    W(ability("Arc Lightning", slug="zuus_arc_lightning"))
    W(ul_open())
    W(li("Jumps decreased from 5/7/9/15 to 5/7/9/11", b([5, 7, 9, 15], [5, 7, 9, 11])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Static Field Damage increased from +1.5% to +2%", b(1.5, 2)))
    W(ul_close())

    write_footer()
    save_html('patches/7.40.html')

