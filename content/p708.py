from patch.api import *

def build():
    write_head("7.08", "01.02.2018")

    # ===== GENERAL UPDATES =====
    W(section("General Updates"))

    W(plain_header("General"))
    W(ul_open())
    W(li("Observer Wards and Sentry Wards now require a constant 2 hits to kill", t("REWORK")))
    W(li("Tier 1 Tower armor aura increased from 1 to 2", b(1, 2)))
    W(li("Bounty Runes base XP reduced from 25 to 0", b(25, 0)))
    W(li_formula(
        "Bounty Runes Gold Growth increased",
        "2/min", "4/min",
        lambda T: 2 * T, lambda T: 4 * T,
        levels=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60],
        level_fmt=lambda T: f'{T}:00',
        jump_at=15,
        rework_badge=False,
        value_fmt="{:g}g",
    ))
    W(li("Roshan now has 25% Status Resistance", t("NEW")))
    W(li("All Pick drafting time per hero selection reduced from 30s to 25s", b(30, 25)))
    W(ul_close())

    # ===== ITEM UPDATES =====
    W(section("Item Updates"))

    W(item_header("Aeon Disk"))
    W(ul_open())
    W(li("Health threshold reduced from 80% to 70%", b(80, 70)))
    W(ul_close())

    W(item_header("Battle Fury"))
    W(ul_open())
    W(li("Creep Bonus damage reduced from 60% to 50%", b(60, 50)))
    W(li("Creep Bonus no longer works with illusions", t("DEL")))
    W(ul_close())

    W(item_header("Black King Bar"))
    W(ul_open())
    W(li("Cooldown rescaled from 80/75/70/65/60/55 to 70", b([80, 75, 70, 65, 60, 55], 70, l=True)))
    W(ul_close())

    W(item_header("Blink Dagger"))
    W(ul_open())
    W(li("Cooldown increased from 12s to 14s", b(12, 14, l=True)))
    W(ul_close())

    W(item_header("Enchanted Mango"))
    W(ul_open())
    W(li("Mana restore increased from 150 to 175", b(150, 175)))
    W(ul_close())

    W(item_header("Faerie Fire"))
    W(ul_open())
    W(li("Heal increased from 75 to 85", b(75, 85)))
    W(ul_close())

    W(item_header("Force Staff"))
    W(ul_open())
    W(li("Time it takes for the full distance to be traveled increased from 0.4s to 0.5s", b(0.4, 0.5, l=True)))
    W(ul_close())

    W(item_header("Hurricane Pike"))
    W(ul_open())
    W(li("Time it takes for the full distance to be traveled increased from 0.4s to 0.5s", b(0.4, 0.5, l=True)))
    W(li("Cooldown increased from 18s to 23s", b(18, 23, l=True)))
    W(ul_close())

    W(item_header("Meteor Hammer"))
    W(ul_open())
    W(li("Cooldown reduced from 40s to 28s", b(40, 28, l=True)))
    W(ul_close())

    W(item_header("Soul Ring"))
    W(ul_open())
    W(li("Recipe cost increased from 185 to 200", b(185, 200, l=True)))
    W(ul_close())

    W(item_header("Spirit Vessel"))
    W(ul_open())
    W(li("Recipe cost increased from 600 to 750", b(600, 750, l=True)))
    W(ul_close())

    # ===== HERO UPDATES =====
    W(section("Hero Updates"))

    # Alchemist
    W(hero_header("Alchemist"))
    W(ability("Chemical Rage", innate=False))
    W(ul_open())
    W(li("Base attack time improved from 1.4/1.2/1.0 to 1.3/1.15/1.0", b([1.4, 1.2, 1.0], [1.3, 1.15, 1.0], l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent increased from -5s Unstable Concoction Cooldown to -8s", b(5, 8)))
    W(li("Level 15 Talent increased from +350 Health to +400", b(350, 400)))
    W(li("Level 20 Talent increased from +360 Unstable Concoction Damage to +400", b(360, 400)))
    W(ul_close())

    # Ember Spirit
    W(hero_header("Ember Spirit"))
    W(ability("Sleight of Fist", innate=False))
    W(ul_open())
    W(li("Hero Damage increased from 20/40/60/80 to 25/50/75/100", b([20, 40, 60, 80], [25, 50, 75, 100])))
    W(ul_close())

    # Enchantress
    W(hero_header("Enchantress"))
    W(ul_open())
    W(li("Base damage reduced by 3", t("NERF")))
    W(ul_close())

    # Jakiro
    W(hero_header("Jakiro"))
    W(ul_open())
    W(li("Attack backswing reduced from 0.5 to 0.3", b(0.5, 0.3, l=True)))
    W(ul_close())

    # Juggernaut
    W(hero_header("Juggernaut"))
    W(ability("Blade Dance", innate=False))
    W(ul_open())
    W(li("Damage reduced from 200% to 180%", b(200, 180)))
    W(ul_close())

    # Leshrac
    W(hero_header("Leshrac"))
    W(ability("Split Earth", innate=False))
    W(ul_open())
    W(li("Manacost reduced from 100/125/140/160 to 80/100/120/140", b([100, 125, 140, 160], [80, 100, 120, 140], l=True)))
    W(ul_close())

    # Lina
    W(hero_header("Lina"))
    W(ul_open())
    W(li("Base intelligence increased by 3", t("BUFF")))
    W(li("Base damage random variance reduced from 18 to 12", t("BUFF"),
         extra=inline_note("Auto-attack damage rolls in a narrower min/max range (spread 12 instead of 18). Average damage is unchanged — only the swing between hits is smaller, so attacks are more consistent")))
    W(ul_close())

    # Lion
    W(hero_header("Lion"))
    W(ability("Mana Drain", innate=False))
    W(ul_open())
    W(li("Now slows the target by 14/16/18/20%", t("NEW")))
    W(ul_close())

    # Lycan
    W(hero_header("Lycan"))
    W(ul_open())
    W(li("Base armor reduced by 1", t("NERF")))
    W(ul_close())
    W(ability("Shapeshift", innate=False))
    W(ul_open())
    W(li("Cooldown increased from 120/90/60 to 130/105/80", b([120, 90, 60], [130, 105, 80], l=True)))
    W(ul_close())

    # Medusa
    W(hero_header("Medusa"))
    W(ability("Mystic Snake", innate=False))
    W(ul_open())
    W(li("Cast range reduced from 800 to 700", b(800, 700)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 10 Talent increased from 12% Evasion to 15%", b(12, 15)))
    W(li("Level 15 Talent increased from +15% Mystic Snake Mana Steal to +20%", b(15, 20)))
    W(li("Level 20 Talent reduced from +800 Mana to +700", b(800, 700)))
    W(ul_close())

    # Morphling
    W(hero_header("Morphling"))
    W(ability("Morph", slug="morphling_replicate", innate=False))
    W(ul_open())
    W(li("Cast range increased from 600 to 1000", b(600, 1000)))
    W(li("Manacost reduced from 75/100/125 to 50", b([75, 100, 125], 50, l=True)))
    W(ul_close())
    W(ability("Morph Replicate", innate=False))
    W(ul_open())
    W(li("Cast point removed", t("NEW")))
    W(ul_close())

    # Nature's Prophet
    W(hero_header("Nature's Prophet"))
    W(ability("Wrath of Nature", innate=False))
    W(ul_open())
    W(li("Cooldown reduced from 90/75/60 to 70/65/60", b([90, 75, 60], [70, 65, 60], l=True)))
    W(ul_close())

    # Omniknight
    W(hero_header("Omniknight"))
    W(ability("Purification", innate=False))
    W(ul_open())
    W(li("Cast range reduced from 450 to 400", b(450, 400)))
    W(ul_close())
    W(ability("Degen Aura", innate=False))
    W(ul_open())
    W(li("Range reduced from 300 to 275", b(300, 275)))
    W(ul_close())

    # Oracle
    W(hero_header("Oracle"))
    W(ability("Fortune's End", innate=False))
    W(ul_open())
    W(li("Manacost reduced from 110 to 75", b(110, 75, l=True)))
    W(ul_close())

    # Pangolier
    W(hero_header("Pangolier"))
    W(ability("Rolling Thunder", slug="pangolier_gyroshell", innate=False))
    W(ul_open())
    W(li("Cooldown increased from 50/45/40 to 70/65/60", b([50, 45, 40], [70, 65, 60], l=True)))
    W(ul_close())

    # Pudge
    W(hero_header("Pudge"))
    W(ability("Rot", innate=False))
    W(ul_open())
    W(li("Slow rescaled from 30% to 20/24/28/32%", b(30, [20, 24, 28, 32]),
         extra=inline_note("Effectively a nerf at levels 1–2 (20%, 24%) and a buff only at level 4 (32%)")))
    W(ul_close())

    # Pugna
    W(hero_header("Pugna"))
    W(ability("Life Drain", innate=False))
    W(ul_open())
    W(li("Damage increased from 150/200/250 to 150/225/300", b([150, 200, 250], [150, 225, 300])))
    W(li("Aghanim's Scepter no longer increases Life Drain damage. Now it only removes the cooldown", t("DEL")))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 15 Talent increased from +1 Nether Ward Health to +2", b(1, 2)))
    W(ul_close())

    # Shadow Fiend
    W(hero_header("Shadow Fiend"))
    W(ability("Necromastery", innate=False))
    W(ul_open())
    W(li("Max souls reduced from 18/24/30/36 to 12/20/28/36", b([18, 24, 30, 36], [12, 20, 28, 36])))
    W(ul_close())

    # Shadow Shaman
    W(hero_header("Shadow Shaman"))
    W(ability("Ether Shock", innate=False))
    W(ul_open())
    W(li("Cooldown increased from 8s to 14/12/10/8s", b(8, [14, 12, 10, 8], l=True)))
    W(ul_close())
    W(ability("Shackles", innate=False))
    W(ul_open())
    W(li("Total damage reduced from 120/200/280/360 to 60/160/260/360", b([120, 200, 280, 360], [60, 160, 260, 360])))
    W(ul_close())

    # Tinker
    W(hero_header("Tinker"))
    W(ul_open())
    W(li("Base movement speed reduced from 305 to 290", b(305, 290)))
    W(ul_close())

    # Tiny
    W(hero_header("Tiny"))
    W(ability("Toss", innate=False))
    W(ul_open())
    W(li("Cooldown increased from 8s to 11s", b(8, 11, l=True)))
    W(ul_close())

    # Tusk
    W(hero_header("Tusk"))
    W(ability("Snowball", innate=False))
    W(ul_open())
    W(li("Can no longer be cast while rooted", t("DEL")))
    W(ul_close())

    # Windranger
    W(hero_header("Windranger"))
    W(ability("Windrun", innate=False))
    W(ul_open())
    W(li("Manacost reduced from 60 to 50", b(60, 50, l=True)))
    W(ul_close())
    W(subgroup("Talents"))
    W(ul_open())
    W(li("Level 20 Talent changed from +1 Shackleshot Target to +0.5s Shackleshot Duration", t("REWORK")))
    W(li("Level 25 Talent increased from +30% Ministun Focus Fire to +35%", b(30, 35)))
    W(ul_close())

    write_footer()
    save_html('patches/7.08.html')

