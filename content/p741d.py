from patch.api import *

def build():
    write_head("7.41d", "04.06.2026")

    # 7.41d — auto-generated from data/7.41d_datafeed.json (generate_patch_code_v2.py)
    # then hand-reviewed: cooldown/timer rows promoted from MISC to numeric badges
    # with l=True, base-stat "by N" rows resolved via bstat_h against 7.41c, Spirit
    # Bear folded into a Lone Druid section, per-level formula rows on li_formula.

    # ===== GENERAL UPDATES =====
    W(section("General Updates"))

    W(plain_header("Mechanics"))
    W(ul_open())
    W(li("Dire Fountain: Rejuvenation Aura radius has been slightly increased", t("MISC")))
    W(li("Self-Cast on Town Portal Scroll's Teleport and other similar abilities now place the hero slightly closer to the Ancient", t("QoL")))
    W(li("Town Portal Scroll's Teleport and other similar ability effects now partially follow the channeling unit even if they move after starting their teleport", t("QoL"),
         extra=inline_note(
             "This makes it possible to track the real spot a hero teleported from while using a movement ability during the channel (e.g. Ball Lightning, Pounce, Sun Ray, etc.). "
             "Previously the teleport animation stayed in one place while the displaced hero actually landed somewhere else. "
             "Now the circle animation plays where the Town Portal Scroll was used, but the full animation and effects appear where the hero lands."
         )))
    W(ul_close())

    # ===== ITEM UPDATES =====
    W(section("Item Updates"))
    W(item_header("Dagon"))
    W(ul_open())
    W(li("Recipe cost decreased from 1150 to 1100", b(1150, 1100, l=True), extra=inline_note("Total cost decreased from 3050/4200/5350/6500/7650g to 3000/4100/5200/6300/" + '<span class="li-tail">7400g — ' + b([3050, 4200, 5350, 6500, 7650], [3000, 4100, 5200, 6300, 7400], l=True) + '</span>')))
    W(ul_close())
    W(item_header("Mage Slayer"))
    W(ul_open())
    W(li("Damage bonus decreased from +15 to +12", b(15, 12)))
    W(ul_close())
    W(item_header("Smoke of Deceit"))
    W(ul_open())
    W(li("Using Smoke of Deceit now broadcasts a chat message in allied chat", t("QoL")))
    W(ul_close())

    # ===== NEUTRAL ITEM UPDATES =====
    W(section("Neutral Item Updates"))

    W(plain_header("Artifacts", dynamics=False))
    W(item_header("Flayer's Bota"))
    W(ul_open())
    W(li("Bloodrush range increased from 1200 to 1500", b(1200, 1500)))
    W(ul_close())
    W(item_header("Idol of Scree'auk"))
    W(ul_open())
    W(li("False Flight bonus evasion increased from 25% to 35%", b(25, 35)))
    W(ul_close())
    W(item_header("Prophet's Pendulum"))
    W(ul_open())
    W(li("Linger delayed damage is now non-lethal if the incoming damage source was non-lethal", t("MISC"), extra=inline_note("Fixes a bug where a hero could kill themselves with their own non-lethal damage (Huskar, Soul Ring, Rot etc.)")))
    W(ul_close())
    W(item_header("Dezun Bloodrite"))
    W(ul_open())
    W(li("Blood Invocation bonus AoE increased from 16% to 20%", b(16, 20)))
    W(ul_close())
    W(item_header("Fallen Sky"))
    W(ul_open())
    W(li("Fallen Sky building impact damage increased from 75 to 110", b(75, 110)))
    W(ul_close())
    W(item_header("Harmonizer"))
    W(ul_open())
    W(li("Balance mana cost reduction per ability off cooldown increased from 5% to 7%", b(5, 7)))
    W(ul_close())
    W(item_header("Riftshadow Prism"))
    W(ul_open())
    W(li("Refract illusion's outgoing damage increased from 50% to 60%", b(50, 60)))
    W(ul_close())
    W(item_header("Spider Legs"))
    W(ul_open())
    W(li("Skitter cooldown decreased from 20s to 15s", b(20, 15, l=True)))
    W(li("Skitter duration decreased from 14s to 12s", b(14, 12)))
    W(ul_close())
    W(item_header("Witchbane"))
    W(ul_open())
    W(li("Cleanse cast range increased from 500 to 700", b(500, 700)))
    W(li("Cleanse: Mana Cost decreased from 150 to 50", b(150, 50, l=True)))
    W(ul_close())

    W(plain_header("Enchantments", dynamics=False))
    W(enchant_header("Alert"))
    W(ul_open())
    W(li("Night Vision bonus decreased from +0/150/225/300 to +0/125/175/225", b([0, 150, 225, 300], [0, 125, 175, 225])))
    W(li("Attack Range bonus decreased from +0/0/0/100 to +0/0/0/80", b([0, 0, 0, 100], [0, 0, 0, 80])))
    W(ul_close())
    W(enchant_header("Timeless"))
    W(ul_open())
    W(li("Spell Amplification bonus decreased from +6/16% to +5/12%", b([6, 16], [5, 12])))
    W(ul_close())
    W(enchant_header("Titanic"))
    W(ul_open())
    W(li("Attack Speed penalty decreased from 10/12/14% to 9%", b([10, 12, 14], 9, l=True)))
    W(ul_close())
    W(enchant_header("Vital"))
    W(ul_open())
    W(li("Health Regen bonus increased from +2 to +2.25", b(2, 2.25)))
    W(ul_close())

    # ===== HERO UPDATES =====
    W(section("Hero Updates"))

    # Abaddon
    W(hero_header("Abaddon"))
    W(ul_open())
    W(li("Base Attack Speed increased from 95 to 100", b(95, 100)))
    W(ul_close())
    W(ability("Withering Mist", slug="abaddon_withering_mist"))
    W(ul_open())
    W(li_formula("Heal Reduction increased",
                 "24.5% + 0.5% per level", "29.5% + 0.5% per level",
                 lambda L: 24.5 + 0.5 * L, lambda L: 29.5 + 0.5 * L,
                 value_fmt="{:g}%"))
    W(ul_close())

    # Ancient Apparition
    W(hero_header("Ancient Apparition"))
    W(ability("Cold Feet", slug="ancient_apparition_cold_feet"))
    W(ul_open())
    W(li("Damage per second increased from 20/40/60/80 to 25/45/65/85", b([20, 40, 60, 80], [25, 45, 65, 85])))
    W(ul_close())
    W(ability("Chilling Touch", slug="ancient_apparition_chilling_touch"))
    W(ul_open())
    W(li("Cooldown decreased from 12/9/6/3s to 10/7.5/5/2.5s", b([12, 9, 6, 3], [10, 7.5, 5, 2.5], l=True)))
    W(li("Damage increased from 30/60/90/120 to 35/65/95/125", b([30, 60, 90, 120], [35, 65, 95, 125])))
    W(ul_close())

    # Anti-Mage
    W(hero_header("Anti-Mage"))
    W(ul_open())
    W(li("Base Agility increased from 24 to 25", b(24, 25)))
    W(li("Damage at level 1 increased by 1 (from 53-57 to 54-58)", br(53, 57, 54, 58)))
    W(ul_close())
    W(ability("Blink", slug="antimage_blink"))
    W(ul_open())
    W(li("Mana Cost decreased from 65/60/55/50 to 60/55/50/45", b([65, 60, 55, 50], [60, 55, 50, 45], l=True)))
    W(ul_close())

    # Arc Warden
    W(hero_header("Arc Warden"))
    W(ability("Flux", slug="arc_warden_flux"))
    W(ul_open())
    W(li("Cast Range increased from 500/600/700/800 to 625/700/775/850", b([500, 600, 700, 800], [625, 700, 775, 850])))
    W(li("Movement Speed Slow increased from 14/21/28/35% to 20/25/30/35%", b([14, 21, 28, 35], [20, 25, 30, 35])))
    W(ul_close())

    # Axe
    W(hero_header("Axe"))
    W(ul_open())
    W(li("Base Health Regen decreased by 0.5", bstat_h("Axe", "StatusHealthRegen", "7.41c", -0.5), extra=inline_note("Valve also lists \"Sense of Foreboding increased from 0 to 0.5\", but no such ability exists anywhere in the game files (likely a Valve leftover) — the only real change is the base Health Regen reduction")))
    W(ul_close())
    W(ability("Battle Hunger", slug="axe_battle_hunger"))
    W(ul_open())
    W(li("Cast Range decreased from 700/775/850/925 to 600/700/800/900", b([700, 775, 850, 925], [600, 700, 800, 900])))
    W(ul_close())

    # Bloodseeker
    W(hero_header("Bloodseeker"))
    W(ability("Bloodrage", slug="bloodseeker_bloodrage"))
    W(ul_open())
    W(li("No longer procs Magic Stick or its upgrades", t("BUFF")))
    W(ul_close())
    W(ability("Rupture", slug="bloodseeker_rupture"))
    W(ul_open())
    W(li("Aghanim's Scepter health damage increased from 13% to 15%", b(13, 15)))
    W(ul_close())

    # Bounty Hunter
    W(hero_header("Bounty Hunter"))
    W(ability("Big Game Hunter", slug="bounty_hunter_big_game_hunter"))
    W(ul_open())
    W(li("Bonus gold increased from 15% to 20%", b(15, 20)))
    W(ul_close())

    # Brewmaster
    W(hero_header("Brewmaster"))
    W(ability("Thunder Clap", slug="brewmaster_thunder_clap"))
    W(ul_open())
    W(li("Slow duration increased from 4s to 4/4.25/4.5/4.75s", b(4, [4, 4.25, 4.5, 4.75])))
    W(ul_close())
    W(ability("Liquid Courage", slug="brewmaster_liquid_courage"))
    W(ul_open())
    W(li("Aghanim's Shard max HP regen per second increased from 2.5% to 3%", b(2.5, 3)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Brewlings Base Damage decreased from +14 to +13", b(14, 13)))
    W(li("Level 20 Talent Primal Split Cooldown Reduction decreased from 15s to 12s", b(15, 12)))
    W(ul_close())

    # Broodmother
    W(hero_header("Broodmother"))
    W(ability("Spawn Spiderlings", slug="broodmother_spawn_spiderlings"))
    W(ul_open())
    W(li("Spiderlings HP increased from 300 to 325", b(300, 325)))
    W(ul_close())

    # Chaos Knight
    W(hero_header("Chaos Knight"))
    W(ability("Phantasm", slug="chaos_knight_phantasm"))
    W(ul_open())
    W(li("Phantasm Damage increased from 50/75/100% to 60/80/100%", b([50, 75, 100], [60, 80, 100])))
    W(ul_close())

    # Clinkz
    W(hero_header("Clinkz"))
    W(ability("Death Pact", slug="clinkz_death_pact"))
    W(ul_open())
    W(li("Mana Cost decreased from 60 to 50", b(60, 50, l=True)))
    W(ul_close())

    # Clockwerk
    W(hero_header("Clockwerk"))
    W(ability("Power Cogs", slug="rattletrap_power_cogs"))
    W(ul_open())
    W(li("Pushback and damage now apply against heroes with no mana", t("BUFF"), extra=inline_note("Targets Huskar in particular — previously Power Cogs had no effect on him at all, as he has no mana to drain.")))
    W(li("Mana Cost increased from 60/65/70/75 to 75", b([60, 65, 70, 75], 75, l=True)))
    W(li("Damage rescaled from 50/125/200/275 to 55/110/165/220", b([50, 125, 200, 275], [55, 110, 165, 220])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Hookshot Cooldown Reduction decreased from 10s to 8s", b(10, 8)))
    W(ul_close())

    # Dark Seer
    W(hero_header("Dark Seer"))
    W(ul_open())
    W(li("Base Health Regen increased by 0.5", bstat_h("Dark Seer", "StatusHealthRegen", "7.41c", 0.5), extra=note_box(hero="Dark Seer", field="StatusHealthRegen", before_patch="7.41c")))
    W(ul_close())

    # Dark Willow
    W(hero_header("Dark Willow"))
    W(ul_open())
    W(li("Base Intelligence increased from 21 to 22", b(21, 22)))
    W(li("Damage at level 1 increased by 1 (from 48-56 to 49-57)", br(48, 56, 49, 57)))
    W(ul_close())
    W(ability("Cursed Crown", slug="dark_willow_cursed_crown"))
    W(ul_open())
    W(li("Cast Range increased from 600/625/650/675 to 700", b([600, 625, 650, 675], 700)))
    W(ul_close())

    # Dawnbreaker
    W(hero_header("Dawnbreaker"))
    W(ability("Starbreaker", slug="dawnbreaker_fire_wreath"))
    W(ul_open())
    W(li("Mana Cost increased from 100 to 110", b(100, 110, l=True)))
    W(ul_close())

    # Dazzle
    W(hero_header("Dazzle"))
    W(ability("Poison Touch", slug="dazzle_poison_touch"))
    W(ul_open())
    W(li("Bonus Slow Per Hit increased from 2/2.5/3/3.5% to 2.5/3/3.5/4%", b([2, 2.5, 3, 3.5], [2.5, 3, 3.5, 4])))
    W(ul_close())

    # Disruptor
    W(hero_header("Disruptor"))
    W(ul_open())
    W(li("Base Movement Speed increased from 295 to 300", b(295, 300)))
    W(ul_close())
    W(ability("Thunder Strike", slug="disruptor_thunder_strike"))
    W(ul_open())
    W(li("Mana Cost decreased from 125/130/135/140 to 115/120/125/130", b([125, 130, 135, 140], [115, 120, 125, 130], l=True)))
    W(ul_close())

    # Doom
    W(hero_header("Doom"))
    W(ul_open())
    W(li("Intelligence gain increased from 1.9 to 2.1", b(1.9, 2.1)))
    W(ul_close())
    W(ability("Devour", slug="doom_bringer_devour"))
    W(ul_open())
    W(li("Aghanim's Shard bonus AoE decreased from 20% to 15%", b(20, 15)))
    W(ul_close())

    # Dragon Knight
    W(hero_header("Dragon Knight"))
    W(ability("Dragon Tail", slug="dragon_knight_dragon_tail"))
    W(ul_open())
    W(li("AoE increased from 25 to 50", b(25, 50)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Breathe Fire Damage increased from +200 to +220", b(200, 220)))
    W(ul_close())

    # Earth Spirit
    W(hero_header("Earth Spirit"))
    W(ability("Stone Remnant", slug="earth_spirit_stone_caller"))
    W(ul_open())
    W(li("Passive bonus damage per unused charge increased from 2.5% to 3%", b(2.5, 3)))
    W(ul_close())

    # Earthshaker
    W(hero_header("Earthshaker"))
    W(ul_open())
    W(li("Base Mana Regen increased by 0.25", bstat_h("Earthshaker", "StatusManaRegen", "7.41c", 0.25), extra=note_box(hero="Earthshaker", field="StatusManaRegen", before_patch="7.41c")))
    W(ul_close())

    # Elder Titan
    W(hero_header("Elder Titan"))
    W(ability("Natural Order", slug="elder_titan_natural_order"))
    W(ul_open())
    W(li("Radius increased from 350 to 375", b(350, 375)))
    W(ul_close())
    W(ability("Earth Splitter", slug="elder_titan_earth_splitter"))
    W(ul_open())
    W(li("Movement Slow increased from 30/40/50% to 40/45/50%", b([30, 40, 50], [40, 45, 50])))
    W(ul_close())

    # Ember Spirit
    W(hero_header("Ember Spirit"))
    W(ability("Sleight of Fist", slug="ember_spirit_sleight_of_fist"))
    W(ul_open())
    W(li("Bonus Hero Damage decreased from 50/90/130/170 to 40/80/120/160", b([50, 90, 130, 170], [40, 80, 120, 160])))
    W(ul_close())

    # Enigma
    W(hero_header("Enigma"))
    W(ability("Demonic Summoning", slug="enigma_demonic_conversion"))
    W(ul_open())
    W(li("Cooldown rescaled from 40/38/36/34s to 45/40/35/30s", b([40, 38, 36, 34], [45, 40, 35, 30], l=True)))
    W(ul_close())

    # Faceless Void
    W(hero_header("Faceless Void"))
    W(ability("Time Walk", slug="faceless_void_time_walk"))
    W(ul_open())
    W(li("Aghanim's Scepter Time Lock radius decreased from 400 to 325", b(400, 325)))
    W(ul_close())
    W(ability("Time Dilation", slug="faceless_void_time_dilation"))
    W(ul_open())
    W(li("Radius decreased from 775 to 700", b(775, 700)))
    W(ul_close())

    # Grimstroke
    W(hero_header("Grimstroke"))
    W(ability("Dark Portrait", slug="grimstroke_dark_portrait"))
    W(ul_open())
    W(li("Magic Resistance decreased from 95% to 90%", b(95, 90)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Attacks to Destroy Phantom decreased from +3 to +2", b(3, 2)))
    W(ul_close())

    # Gyrocopter
    W(hero_header("Gyrocopter"))
    W(ul_open())
    W(li("Night Vision increased from 800 to 1000", b(800, 1000)))
    W(ul_close())
    W(ability("Flak Cannon", slug="gyrocopter_flak_cannon"))
    W(ul_open())
    W(li("No longer provides 200 Bonus Night Vision", t("DEL")))
    W(ul_close())
    W(ability("Call Down", slug="gyrocopter_call_down"))
    W(ul_open())
    W(li("Missile Slow increased from 50% to 60%", b(50, 60)))
    W(ul_close())
    W(ability("Side Gunner", slug="gyrocopter_side_gunner_spawn_ability"))
    W(ul_open())
    W(li("No longer attacks 2 units at a time while Flak Cannon is active", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Flak Cannon Cooldown Reduction increased from 4s to 6s", b(4, 6)))
    W(ul_close())

    # Hoodwink
    W(hero_header("Hoodwink"))
    W(ability("Acorn Shot", slug="hoodwink_acorn_shot"))
    W(ul_open())
    W(li("Cooldown increased from 16/14/12/10s to 19/16/13/10s", b([16, 14, 12, 10], [19, 16, 13, 10], l=True)))
    W(ul_close())
    W(ability("Scurry", slug="hoodwink_scurry"))
    W(ul_open())
    W(li("Bonus Movement Speed decreased from 20/25/30/35% to 15/20/25/30%", b([20, 25, 30, 35], [15, 20, 25, 30])))
    W(ul_close())

    # Huskar
    W(hero_header("Huskar"))
    W(ability("Burning Spear", slug="huskar_burning_spear"))
    W(ul_open())
    W(li("Burn Damage decreased from 5/10/15/20 to 4/8/12/16", b([5, 10, 15, 20], [4, 8, 12, 16])))
    W(ul_close())

    # Invoker
    W(hero_header("Invoker"))
    W(ability("Ghost Walk", slug="invoker_ghost_walk"))
    W(ul_open())
    W(li("Cooldown increased from 32s to 40s", b(32, 40, l=True)))
    W(ul_close())
    W(ability("Chaos Meteor", slug="invoker_chaos_meteor"))
    W(ul_open())
    W(li("Contact Damage decreased from 55/80/105/130/155/180/205/220/235 to 55/75/95/115/135/155/175/195/215", b([55, 80, 105, 130, 155, 180, 205, 220, 235], [55, 75, 95, 115, 135, 155, 175, 195, 215])))
    W(ul_close())
    W(ability("Ice Wall", slug="invoker_ice_wall"))
    W(ul_open())
    W(li("Movement Slow rescaled from 20/40/60/80/100/120/140/160/180% to 30/45/60/75/90/105/120/135/150%", b([20, 40, 60, 80, 100, 120, 140, 160, 180], [30, 45, 60, 75, 90, 105, 120, 135, 150])))
    W(ul_close())

    # Jakiro
    W(hero_header("Jakiro"))
    W(ul_open())
    W(li("Base Intelligence increased from 25 to 26", b(25, 26)))
    W(li("Damage at level 1 increased by 1 (from 52-60 to 53-61)", br(52, 60, 53, 61)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Ice Path Damage increased from +75 to +100", b(75, 100)))
    W(li("Level 25 Talent Liquid Frost and Fire Max Health Damage increased from +3% to +3.5%", b(3, 3.5)))
    W(ul_close())

    # Juggernaut
    W(hero_header("Juggernaut"))
    W(ability("Blade Fury", slug="juggernaut_blade_fury"))
    W(ul_open())
    W(li("Mana Cost decreased from 120 to 110", b(120, 110, l=True)))
    W(ul_close())

    # Kez
    W(hero_header("Kez"))
    W(ability("Switch Discipline", slug="kez_switch_weapons"))
    W(ul_open())
    W(li("Katana Bonus Agility Base Damage decreased from 16% to 12%", b(16, 12)))
    W(ul_close())
    W(ability("Kazurai Katana", slug="kez_kazurai_katana"))
    W(ul_open())
    W(li("Cooldown increased from 20/15/10/5s to 24/18/12/6s", b([20, 15, 10, 5], [24, 18, 12, 6], l=True)))
    W(ul_close())
    W(ability("Shodo Sai", slug="kez_shodo_sai"))
    W(ul_open())
    W(li("Cooldown increased from 20/15/10/5s to 24/18/12/6s", b([20, 15, 10, 5], [24, 18, 12, 6], l=True)))
    W(li("Parry Duration decreased from 2s to 1.5s", b(2, 1.5)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent +12% Magic Resistance replaced with +6% Switch Discipline Swap Bonuses", t("REWORK"), extra=inline_note("Katana Swap Bonus Damage from 12% to 18%. Sai Swap Movement Speed from 12% to 18%")))
    W(ul_close())

    # Largo
    W(hero_header("Largo"))
    W(ability("Encore", slug="largo_encore"))
    W(ul_open())
    W(li_formula("Bonus Duration increased",
                 "10% + 1% per level", "15% + 1% per level",
                 lambda L: 10 + 1 * L, lambda L: 15 + 1 * L))
    W(ul_close())
    W(ability("Amphibian Rhapsody", slug="largo_amphibian_rhapsody"))
    W(ul_open())
    W(li("Song Mana Costs increased from 20/32/44 to 25/35/45", b([20, 32, 44], [25, 35, 45], l=True)))
    W(ul_close())

    # Legion Commander
    W(hero_header("Legion Commander"))
    W(ability("Duel", slug="legion_commander_duel"))
    W(ul_open())
    W(li("Mana Cost increased from 75 to 80/100/120", b(75, [80, 100, 120], l=True)))
    W(ul_close())

    # Leshrac
    W(hero_header("Leshrac"))
    W(ability("Pulse Nova", slug="leshrac_pulse_nova"))
    W(ul_open())
    W(li("Mana/Sec decreased from 25/45/65 to 20/40/60", b([25, 45, 65], [20, 40, 60], l=True)))
    W(ul_close())
    W(ability("Nihilism", slug="leshrac_greater_lightning_storm"))
    W(ul_open())
    W(li("Slow increased from 30% to 40%", b(30, 40)))
    W(ul_close())

    # Lina
    W(hero_header("Lina"))
    W(ability("Dragon Slave", slug="lina_dragon_slave"))
    W(ul_open())
    W(li("Mana Cost decreased from 100/110/120/130 to 90/100/110/120", b([100, 110, 120, 130], [90, 100, 110, 120], l=True)))
    W(ul_close())

    # Lion
    W(hero_header("Lion"))
    W(ability("Finger of Death", slug="lion_finger_of_death"))
    W(ul_open())
    W(li("Damage per kill decreased from 30 to 25", b(30, 25)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Hex Cooldown Reduction decreased from 2.5s to 2s", b(2.5, 2)))
    W(ul_close())

    # Lone Druid (Spirit Bear changes — id 1961 — folded into Lone Druid)
    W(hero_header("Lone Druid"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Movement Speed decreased from +20 to +15", b(20, 15)))
    W(ul_close())
    W(unit_header("Spirit Bear", "../icons/abilities/lone_druid_spirit_bear.png", kind="Creep-hero"))
    W(ul_open())
    W(li("Base Health Regen decreased by 1.5", b(3, 1.5), extra=note_box(prev_val=3, new_val=1.5, prev_patch="7.40")))
    W(ul_close())

    # Marci
    W(hero_header("Marci"))
    W(ability("Special Delivery", slug="marci_special_delivery"))
    W(ul_open())
    W(li_formula("Cooldown decreased",
                 "245s − 5s per level", "215s − 5s per level",
                 lambda L: 245 - 5 * L, lambda L: 215 - 5 * L, l=True))
    W(ul_close())
    W(ability("Bodyguard", slug="marci_bodyguard"))
    W(ul_open())
    W(li("Mana Cost decreased from 60/65/70/75 to 60", b([60, 65, 70, 75], 60, l=True)))
    W(ul_close())

    # Mars
    W(hero_header("Mars"))
    W(ability("Dauntless", slug="mars_dauntless"))
    W(ul_open())
    W(li("Radius increased from 700 to 900", b(700, 900)))
    W(ul_close())
    W(ability("God's Rebuke", slug="mars_gods_rebuke"))
    W(ul_open())
    W(li("Now turns Mars in the cast direction when cast with Bulwark toggled on", t("QoL")))
    W(ul_close())
    W(ability("Arena Of Blood", slug="mars_arena_of_blood"))
    W(ul_open())
    W(li("Spear Damage increased from 80/160/240 to 80/170/260", b([80, 160, 240], [80, 170, 260])))
    W(ul_close())

    # Mirana
    W(hero_header("Mirana"))
    W(ability("Celestial Quiver", slug="mirana_celestial_quiver"))
    W(ul_open())
    W(li_formula("Max Charges increased",
                 "2 + 1 per 7 levels", "2 + 1 per 6 levels",
                 lambda L: 2 + L // 7, lambda L: 2 + L // 6,
                 levels=[1, 6, 7, 12, 14, 18, 21, 24, 28, 30]))
    W(ul_close())
    W(ability("Starstorm", slug="mirana_starfall"))
    W(ul_open())
    W(li("Second Meteor Damage increased from 70% to 80%", b(70, 80)))
    W(ul_close())

    # Morphling
    W(hero_header("Morphling"))
    W(ul_open())
    W(li("Base Strength decreased from 23 to 16", b(23, 16)))
    W(li("Base Agility increased from 24 to 33", b(24, 33)))
    W(li("Damage at level 1 increased by 9 (from 36-45 to 45-54)", br(36, 45, 45, 54)))
    W(ul_close())
    W(ability("Ebb and Flow", slug="morphling_ebb_and_flow"))
    W(ul_open())
    W(li("Agility to Attack Range increased from 20% to 25%", b(20, 25)))
    W(li("Strength to Cast Range increased from 20% to 25%", b(20, 25)))
    W(li("Strength to Slow Resistance increased from 20% to 25%", b(20, 25)))
    W(ul_close())
    W(ability("Morph", slug="morphling_replicate"))
    W(ul_open())
    W(li("Aghanim's Scepter illusion incoming damage decreased from 300% to 200%", b(300, 200, l=True)))
    W(ul_close())

    # Nature's Prophet
    W(hero_header("Nature's Prophet"))
    W(ability("Spirit of the Forest", slug="furion_spirit_of_the_forest"))
    W(ul_open())
    W(li("Treants that are alive now always contribute to the bonus damage, even if they are out of range", t("BUFF")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Sprout Damage increased from +220 to +240", b(220, 240)))
    W(ul_close())

    # Night Stalker
    W(hero_header("Night Stalker"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Dark Ascension Cooldown Reduction decreased from 40s to 35s", b(40, 35)))
    W(ul_close())

    # Ogre Magi
    W(hero_header("Ogre Magi"))
    W(ul_open())
    W(li("Base Strength increased from 25 to 26", b(25, 26)))
    W(li("Damage at level 1 increased by 1 (from 70-76 to 71-77)", br(70, 76, 71, 77)))
    W(ul_close())

    # Omniknight
    W(hero_header("Omniknight"))
    W(ul_open())
    W(li("Base Intelligence increased from 16 to 18", b(16, 18)))
    W(ul_close())

    # Outworld Destroyer
    W(hero_header("Outworld Destroyer"))
    W(ul_open())
    W(li("Min Base damage increased by 4", bstat_h("Outworld Destroyer", "AttackDamageMin", "7.41c", 4)))
    W(li("Max Base damage increased by 1", bstat_h("Outworld Destroyer", "AttackDamageMax", "7.41c", 1)))
    W(li("Damage at level 1 increased from 49-61 to 53-62", br(49, 61, 53, 62), extra=inline_note("Damage spread decreased from 12 to 9")))
    W(ul_close())

    # Pangolier
    W(hero_header("Pangolier"))
    W(ul_open())
    W(li("Base Agility decreased from 18 to 17", b(18, 17)))
    W(li("Damage at level 1 decreased from 50-56 to 49-55", br(50, 56, 49, 55)))
    W(li("Base Armor decreased by 1", bstat_h("Pangolier", "ArmorPhysical", "7.41c", -1), extra=note_box(hero="Pangolier", field="ArmorPhysical", before_patch="7.41c")))
    W(ul_close())

    # Phoenix
    W(hero_header("Phoenix"))
    W(ability("Fire Spirits", slug="phoenix_fire_spirits"))
    W(ul_open())
    W(li("Attack Speed Slow decreased from 50/80/110/140 to 35/70/105/140", b([50, 80, 110, 140], [35, 70, 105, 140])))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Max Health Sun Ray Damage decreased from +1.5% to +1.25%", b(1.5, 1.25)))
    W(ul_close())

    # Puck
    W(hero_header("Puck"))
    W(ul_open())
    W(li("Agility gain decreased from 2.3 to 2.1", b(2.3, 2.1)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Illusory Orb Damage decreased from +40 to +35", b(40, 35)))
    W(ul_close())

    # Pudge
    W(hero_header("Pudge"))
    W(ul_open())
    W(li("Base Agility increased from 11 to 13", b(11, 13)))
    W(ul_close())

    # Pugna
    W(hero_header("Pugna"))
    W(ul_open())
    W(li("Base Mana Regen increased by 0.25", bstat_h("Pugna", "StatusManaRegen", "7.41c", 0.25), extra=note_box(hero="Pugna", field="StatusManaRegen", before_patch="7.41c")))
    W(ul_close())
    W(ability("Nether Ward", slug="pugna_nether_ward"))
    W(ul_open())
    W(li("Cast Range increased from 150 to 175", b(150, 175)))
    W(ul_close())

    # Razor
    W(hero_header("Razor"))
    W(ul_open())
    W(li("Base Attack Speed increased from 100 to 110", b(100, 110)))
    W(ul_close())

    # Riki
    W(hero_header("Riki"))
    W(ability("Backstab", slug="riki_innate_backstab"))
    W(ul_open())
    W(li("Effectiveness on allies increased from 25% to 30%", b(25, 30)))
    W(ul_close())
    W(ability("Smoke Screen", slug="riki_smoke_screen"))
    W(ul_open())
    W(li("Cooldown rescaled from 17/15/13/11s to 15/14/13/12s", b([17, 15, 13, 11], [15, 14, 13, 12], l=True)))
    W(ul_close())
    W(ability("Blink Strike", slug="riki_blink_strike"))
    W(ul_open())
    W(li("Bonus Damage rescaled from 15/30/45/60 to 25/35/45/55", b([15, 30, 45, 60], [25, 35, 45, 55])))
    W(ul_close())

    # Ringmaster
    W(hero_header("Ringmaster"))
    W(ability("Funhouse Mirror", slug="ringmaster_funhouse_mirror"))
    W(ul_open())
    W(li("Proportion Distortion Illusion damage increased from 28% to 100%", b(28, 100)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Wheel of Wonder Radius and Range increased from +100 to +150", b(100, 150)))
    W(ul_close())

    # Rubick
    W(hero_header("Rubick"))
    W(ability("Fade Bolt", slug="rubick_fade_bolt"))
    W(ul_open())
    W(li("Damage decreased from 100/175/250/325 to 85/165/245/325", b([100, 175, 250, 325], [85, 165, 245, 325])))
    W(li("Debuff Duration decreased from 10s to 9s", b(10, 9)))
    W(ul_close())

    # Sand King
    W(hero_header("Sand King"))
    W(ul_open())
    W(li("Strength gain increased from 2.3 to 2.5", b(2.3, 2.5)))
    W(li("Damage gain per level increased from 2.8 to 2.9", b(2.8, 2.9)))
    W(ul_close())

    # Shadow Demon
    W(hero_header("Shadow Demon"))
    W(ability("Shadow Poison", slug="shadow_demon_shadow_poison"))
    W(ul_open())
    W(li("Mana Cost decreased from 45 to 40", b(45, 40, l=True)))
    W(li("Damage per additional stack over 5 stacks increased from 50 to 60", b(50, 60)))
    W(ul_close())

    # Shadow Shaman
    W(hero_header("Shadow Shaman"))
    W(ability("Mass Serpent Ward", slug="shadow_shaman_mass_serpent_ward"))
    W(ul_open())
    W(li("Gold Bounty decreased from 22-30 to 20-26", br(22, 30, 20, 26, l=True)))
    W(ul_close())
    W(ability("Urnaconda", slug="shadow_shaman_urnaconda"))
    W(ul_open())
    W(li("Mana Cost increased from 115 to 140", b(115, 140, l=True)))
    W(ul_close())

    # Skywrath Mage
    W(hero_header("Skywrath Mage"))
    W(ul_open())
    W(li("Base Strength increased from 21 to 22", b(21, 22)))
    W(ul_close())

    # Slardar
    W(hero_header("Slardar"))
    W(ability("Corrosive Haze", slug="slardar_amplify_damage"))
    W(ul_open())
    W(li("Armor Reduction decreased from 10/15/20 to 8/14/20", b([10, 15, 20], [8, 14, 20])))
    W(ul_close())

    # Slark
    W(hero_header("Slark"))
    W(ability("Saltwater Shiv", slug="slark_saltwater_shiv"))
    W(ul_open())
    W(li("Cooldown decreased from 14/12/10/8s to 12/10.5/9/7.5s", b([14, 12, 10, 8], [12, 10.5, 9, 7.5], l=True)))
    W(ul_close())

    # Snapfire
    W(hero_header("Snapfire"))
    W(ability("Boomstick", slug="snapfire_boomstick"))
    W(ul_open())
    W(li("No longer applies on denies or buildings", t("DEL")))
    W(ul_close())
    W(ability("Firesnap Cookie", slug="snapfire_firesnap_cookie"))
    W(ul_open())
    W(li("Aghanim's Shard heal amount decreased from 200 to 175", b(200, 175)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent Firesnap Cookie Cooldown Reduction decreased from 4s to 3s", b(4, 3)))
    W(ul_close())

    # Sniper
    W(hero_header("Sniper"))
    W(ability("Keen Scope", slug="sniper_keen_scope"))
    W(ul_open())
    W(li("No longer applies on denies or buildings", t("DEL")))
    W(ul_close())

    # Spectre
    W(hero_header("Spectre"))
    W(ul_open())
    W(li("Base Strength increased from 21 to 22", b(21, 22)))
    W(li("Agility gain decreased from 2.4 to 2.3", b(2.4, 2.3)))
    W(ul_close())
    W(ability("Spectral Dagger", slug="spectre_spectral_dagger"))
    W(ul_open())
    W(li("Movement Speed Change rescaled from 10/14/18/22% to 14/16/18/20%", b([10, 14, 18, 22], [14, 16, 18, 20])))
    W(ul_close())
    W(ability("Shadow Step", slug="spectre_shadow_step"))
    W(ul_open())
    W(li("Illusion Damage Taken rescaled from 200/185/170/155% to 175%", b([200, 185, 170, 155], 175, l=True)))
    W(li("Cast Range rescaled from 825/950/1075/1200 to 1000", b([825, 950, 1075, 1200], 1000)))
    W(ul_close())
    W(ability("Haunt", slug="spectre_haunt"))
    W(ul_open())
    W(li("Mana Cost increased from 125/150/175 to 125/175/225", b([125, 150, 175], [125, 175, 225], l=True)))
    W(li("Aghanim's Scepter fear duration increased from 1.5s to 2s", b(1.5, 2)))
    W(ul_close())

    # Spirit Breaker
    W(hero_header("Spirit Breaker"))
    W(ability("Charge of Darkness", slug="spirit_breaker_charge_of_darkness"))
    W(ul_open())
    W(li("Mana Cost decreased from 90/100/110/120 to 80/90/100/110", b([90, 100, 110, 120], [80, 90, 100, 110], l=True)))
    W(ul_close())
    W(ability("Greater Bash", slug="spirit_breaker_greater_bash"))
    W(ul_open())
    W(li("Aghanim's Scepter creep damage decreased from 25% to 20%", b(25, 20)))
    W(ul_close())

    # Storm Spirit
    W(hero_header("Storm Spirit"))
    W(ul_open())
    W(li("Base Attack Speed decreased from 115 to 110", b(115, 110)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent 2x Overload Attack Bounce damage decreased from 65% to 50%", b(65, 50)))
    W(ul_close())

    # Sven
    W(hero_header("Sven"))
    W(ability("Storm Hammer", slug="sven_storm_bolt"))
    W(ul_open())
    W(li("Stun Duration increased from 1/1.2/1.4/1.6s to 1/1.25/1.5/1.75s", b([1, 1.2, 1.4, 1.6], [1, 1.25, 1.5, 1.75])))
    W(ul_close())
    W(ability("God's Strength", slug="sven_gods_strength"))
    W(ul_open())
    W(li("Slow Resistance increased from 30% to 40%", b(30, 40)))
    W(ul_close())

    # Techies
    W(hero_header("Techies"))
    W(ability("Reactive Tazer", slug="techies_reactive_tazer"))
    W(ul_open())
    W(li("Disarm duration decreased from 2.4/2.7/3/3.3s to 2.25/2.5/2.75/3s", b([2.4, 2.7, 3, 3.3], [2.25, 2.5, 2.75, 3])))
    W(ul_close())
    W(ability("Proximity Mines", slug="techies_land_mines"))
    W(ul_open())
    W(li("Debuff Duration decreased from 5s to 4s", b(5, 4)))
    W(ul_close())

    # Templar Assassin
    W(hero_header("Templar Assassin"))
    W(ability("Inner Peace", slug="templar_assassin_inner_peace"))
    W(ul_open())
    W(li("Time until meditation starts decreased from 0.25s to 0.2s", b(0.25, 0.2, l=True)))
    W(li_formula("Meditation Time Until Max Bonus decreased",
                 "2.05s − 0.05s per level", "1.85s − 0.05s per level",
                 lambda L: 2.05 - 0.05 * L, lambda L: 1.85 - 0.05 * L, l=True))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Psionic Trap Slow increased from +10% to +15%", b(10, 15)))
    W(ul_close())

    # Timbersaw
    W(hero_header("Timbersaw"))
    W(ul_open())
    W(li("Base Attack Speed decreased from 100 to 90", b(100, 90)))
    W(ul_close())
    W(ability("Whirling Death", slug="shredder_whirling_death"))
    W(ul_open())
    W(li("Stat Loss Duration decreased from 11/12/13/14s to 7/9/11/13s", b([11, 12, 13, 14], [7, 9, 11, 13])))
    W(ul_close())
    W(ability("Flamethrower", slug="shredder_flamethrower"))
    W(ul_open())
    W(li("Move Slow increased from 30% to 40%", b(30, 40)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent Chakram Slow increased from +5% to +6%", b(5, 6)))
    W(li("Level 20 Talent Exposure Therapy Heals Per Tree Destroyed increased from 10 to 12", b(10, 12)))
    W(ul_close())

    # Tiny
    W(hero_header("Tiny"))
    W(ability("Insurmountable", slug="tiny_insurmountable"))
    W(ul_open())
    W(li("Strength to Slow Resist decreased from 20% to 15%", b(20, 15)))
    W(ul_close())
    W(ability("Toss", slug="tiny_toss"))
    W(ul_open())
    W(li("Flight time decreased from 1.25s to 1.1s", b(1.25, 1.1)))
    W(ul_close())
    W(ability("Tree Grab", slug="tiny_tree_grab"))
    W(ul_open())
    W(li("Cooldown increased from 15/12/9/6s to 16/13/10/7s", b([15, 12, 9, 6], [16, 13, 10, 7], l=True)))
    W(ul_close())
    W(ability("Tree Throw", slug="tiny_toss_tree"))
    W(ul_open())
    W(li("Cast Range decreased from 1200 to 1000", b(1200, 1000)))
    W(ul_close())
    W(ability("Grow", slug="tiny_grow"))
    W(ul_open())
    W(li("Aghanim's Shard movement slow increased from 25% to 35%", b(25, 35)))
    W(li("Aghanim's Shard slow duration increased from 2.5s to 3s", b(2.5, 3)))
    W(ul_close())
    W(ability("Tree Volley", slug="tiny_tree_channel"))
    W(ul_open())
    W(li("Mana Cost decreased from 200 to 150", b(200, 150, l=True)))
    W(ul_close())

    # Troll Warlord
    W(hero_header("Troll Warlord"))
    W(ability("Battle Trance", slug="troll_warlord_battle_trance"))
    W(ul_open())
    W(li("Movement Speed increased from 25/30/35% to 35%", b([25, 30, 35], 35)))
    W(ul_close())

    # Undying
    W(hero_header("Undying"))
    W(ul_open())
    W(li("Base Mana Regen increased by 0.25", bstat_h("Undying", "StatusManaRegen", "7.41c", 0.25), extra=note_box(hero="Undying", field="StatusManaRegen", before_patch="7.41c")))
    W(ul_close())

    # Vengeful Spirit
    W(hero_header("Vengeful Spirit"))
    W(ul_open())
    W(li("Base Health Regen increased by 0.5", bstat_h("Vengeful Spirit", "StatusHealthRegen", "7.41c", 0.5), extra=note_box(hero="Vengeful Spirit", field="StatusHealthRegen", before_patch="7.41c")))
    W(ul_close())
    W(ability("Magic Missile", slug="vengefulspirit_magic_missile"))
    W(ul_open())
    W(li("Damage increased from 85/170/255/340 to 100/180/260/340", b([85, 170, 255, 340], [100, 180, 260, 340])))
    W(ul_close())

    # Venomancer
    W(hero_header("Venomancer"))
    W(ul_open())
    W(li("Intelligence gain increased from 1.8 to 1.9", b(1.8, 1.9)))
    W(li("Damage gain per level increased from 3.0 to 3.1", b(3.0, 3.1)))
    W(ul_close())

    # Visage
    W(hero_header("Visage"))
    W(ability("Grave Chill", slug="visage_grave_chill"))
    W(ul_open())
    W(li("Attack Speed Drain rescaled from 25/40/55/70 to 35/45/55/65", b([25, 40, 55, 70], [35, 45, 55, 65])))
    W(ul_close())

    # Warlock
    W(hero_header("Warlock"))
    W(ability("Upheaval", slug="warlock_upheaval"))
    W(ul_open())
    W(li("Cooldown decreased from 60/50/40/30s to 45/40/35/30s", b([60, 50, 40, 30], [45, 40, 35, 30], l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 25 Talent Fatal Bonds Targets increased from +4 to +5", b(4, 5)))
    W(ul_close())

    # Weaver
    W(hero_header("Weaver"))
    W(ability("Threads of Fate", slug="weaver_threads_of_fate"))
    W(ul_open())
    W(li("Slow Duration increased from 0.2s to 0.4s", b(0.2, 0.4)))
    W(ul_close())

    # Winter Wyvern
    W(hero_header("Winter Wyvern"))
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Damage decreased from +35 to +30", b(35, 30)))
    W(li("Level 20 Talent Arctic Burn Slow decreased from +15% to +10%", b(15, 10)))
    W(ul_close())

    # Wraith King
    W(hero_header("Wraith King"))
    W(ul_open())
    W(li("Base Damage increased by 2", bstat_h("Wraith King", "AttackDamageMin", "7.41c", 2)))
    W(li("Damage at level 1 increased from 60-62 to 62-64", br(60, 62, 62, 64)))
    W(ul_close())
    W(ability("Vampiric Spirit", slug="skeleton_king_vampiric_spirit"))
    W(ul_open())
    W(li_formula("Lifesteal rescaled",
                 "14% + 1% per level", "20% + 0.5% per level",
                 lambda L: 14 + 1 * L, lambda L: 20 + 0.5 * L))
    W(ul_close())
    W(ability("Reincarnation", slug="skeleton_king_reincarnation"))
    W(ul_open())
    W(li("Aghanim's Scepter cooldown increased from 165/135/105s to 170/140/110s", b([165, 135, 105], [170, 140, 110], l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent Vampiric Spirit Lifesteal decreased from +10% to +8%", b(10, 8)))
    W(ul_close())

    write_footer()
    save_html('patches/7.41d.html')

