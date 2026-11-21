"""Which tag a patch note gets: the canonical phrases, Valve's own errors, the owner's decisions."""
import json
import re
from pathlib import Path

from .data import _strip_html

# Phrases that LOCK the tag regardless of other signals (Sloppy memory rules).
# Order: longer / more specific patterns first.
# IMPORTANT: BUFF-override patterns must come BEFORE DEL patterns since
# 'no longer has a penalty' should NOT be DEL.
CANONICAL_TAGS = [
    # Crimson Guard's Guard (owner 2026-10-17, 7.41: "nerf, the values got smaller" — 70 -> 45 on ranged heroes); the
    # row starts with the ability, so "Vanguard base damage block …" isn't caught
    (re.compile(r'^\s*Guard base damage block rescaled\b'), 'NERF'),
    # SWAP (owner 2026-09-26): a talent replaced by another in the same slot — its own tag, not REWORK
    # ("Level 15 Talent +110 Rolling Boulder Damage replaced with +80 Boulder Smash Damage")
    (re.compile(r'^\s*Level \d+(?: Talent)?:?\s.*\breplaced with\b', re.I), 'SWAP'),
    # …and a facet's own talent swap, prefixed by the facet ("Old Blood: Level 10 Talent … replaced with …")
    (re.compile(r"^\s*[A-Z][\w' ]{0,40}: Level \d+(?: Talent)?:?\s.*\breplaced with\b"), 'SWAP'),
    # ── 2026-10-05 audit: checked on the generator itself, the content rows were already right ──
    (re.compile(r'^\s*Now costs \d+(?:\.\d+)?%?\s+(?:mana|health)\b', re.I), 'NERF'),   # a new cost (7.41f Treant; was NEW)
    (re.compile(r"^\s*Now can(?:'t| ?not| no longer) (?:use|have|store|hold|stack|exceed)\b[^.]*\bmore than\b", re.I),
     'NERF'),                                                       # a new cap (7.41 Shadow Fiend souls; was NEW)
    # a game-clock timing ("First Spawn Time increased from 15:00 to 20:00", "siege creep timing 35:00 to 30:00"):
    # when an object appears is REWORK (rule "Где и когда появляется объект"), and a % of a clock time means nothing
    # ... except an extra lane creep coming earlier / later: more of that creep sooner is its buff (owner 2026-10-16:
    # "First +1 siege creep timing decreased from 35:00 to 30:00 — а не buff ли это? на 5 минут раньше"), still no %
    (re.compile(r'\+\d+ [\w ]*creeps? timing decreased from \d{1,2}:\d{2} to \d{1,2}:\d{2}\b', re.I), 'BUFF'),
    (re.compile(r'\+\d+ [\w ]*creeps? timing increased from \d{1,2}:\d{2} to \d{1,2}:\d{2}\b', re.I), 'NERF'),
    (re.compile(r'\bfrom \d{1,2}:\d{2} to \d{1,2}:\d{2}\b'), 'REWORK'),
    # a timing that now happens at a clock time where there was none ("Second +1 siege creep timing now occurs at
    # 60:00", 7.41): a new property of the unit — NEW, its own row (owner 2026-10-16, after trying REWORK and one
    # merged row with the first timing)
    (re.compile(r'\btiming\b[^.]*\bnow (?:occurs|happens|starts) at \d{1,2}:\d{2}\b', re.I), 'NEW'),
    # "X is no longer affected / increased by AoE bonuses": one tag for the class, DEL ("No longer …" → DEL);
    # 7.38 had two NERF and three later patches DEL, the scaffold said BUFF or MISC
    (re.compile(r'\bno longer (?:affected|increased|modified) by (?:\w+ )?(?:AoE|Area of Effect) (?:bonus(?:es)?|increase)'
                r'|\bno longer (?:affected|increased) by bonuses to (?:AoE|Area of Effect)\b', re.I), 'DEL'),
    # the mirror: "Radius is now affected by Area of Effect bonuses" is a new property — NEW (owner 2026-10-16, 7.41
    # Congregations of the Deep / Water Bubble (Large); were BUFF)
    (re.compile(r'\bnow (?:also )?(?:affected|increased|modified) by (?:\w+ )?(?:AoE|Area of Effect) (?:bonus(?:es)?|increase)'
                r'|\bnow (?:also )?(?:affected|increased) by (?:bonuses|changes) to (?:AoE|Area of Effect)\b', re.I), 'NEW'),
    # the shop an item is bought in ("Item moved back to Secret Shop from Miscellaneous Shop", 7.41 Ring of Health /
    # Void Stone): where it is sold, a structural move like "Moved from Tier 4 to Tier 2" — REWORK (owner 2026-10-17;
    # were NERF)
    (re.compile(r'\bmoved (?:back )?(?:to|from) (?:the )?(?:Secret|Side|Base|Miscellaneous|Home) Shop\b', re.I), 'REWORK'),
    # ── 2026-10-03 second audit (7.38b-7.41e): classes the scaffold got wrong ──
    (re.compile(r'\bno longer gets? knocked off\b', re.I),           'BUFF'),   # own mount restriction lifted
    # "Buff is now undispellable" alone (7.42 Alchemist Berserk Potion, owner 2026-11-20: "new"): a property the buff
    # gained — before the canon BUFF of an undispellable effect below
    (re.compile(r'^\s*(?:Buff|Debuff|Effect) is now undispellable\.?\s*$', re.I), 'NEW'),
    (re.compile(r'\b(?:is now|now) undispellable\b|^\s*Now cannot be dispelled\b', re.I), 'BUFF'),
    (re.compile(r'^\s*Now (?:dispelled|dispellable)\b', re.I),       'NERF'),   # a new way to lose an own buff
    (re.compile(r'\bnow affected by negative\b', re.I),              'NERF'),   # enemy heal cuts now apply to it
    (re.compile(r'\bnow counts? as hero hits\b', re.I),              'NERF'),   # own summons die faster
    (re.compile(r'\bnow has an? \d+(?:\.\d+)?s initial cooldown\b', re.I), 'NERF'),
    (re.compile(r'\b(?:illusions?|creep-heroes?)\b[^.]*\bwill not (?:deal|apply|trigger|affect)\b', re.I), 'DEL'),
    (re.compile(r"^\s*Now granted by Aghanim's (?:Scepter|Shard)\b", re.I), 'REWORK'),   # moved between upgrades
    # BUFF first — removing a penalty / restriction is positive (memory rule
    # sloppy_no_longer_penalty_is_buff). Tightly anchored so legitimate DEL
    # phrasings don't accidentally match.
    # 7.42: a cooldown reset on an event is a benefit taken away (Glyph); an ENEMY stat debuff taken away (Requiem)
    (re.compile(r'\bno longer resets (?:its |the )?cooldown\b', re.I), 'DEL'),
    (re.compile(r"\bno longer (?:reduces|decreases) (?:enemy|enemies'?) (?:\w+ ){0,3}resistance\b", re.I), 'DEL'),
    # "No longer has reduced damage taken from allies on the first pip of health" (7.42 wards): allies deny a ward with
    # fewer hits — comfort, QoL (owner 2026-11-19; it read BUFF by the penalty rule below, then DEL)
    (re.compile(r'\bno longer has reduced damage taken from allies\b', re.I), 'QoL'),
    # "(?:[\w%.]+ )": 7.42 "No longer has a 35% damage penalty", "No longer has 50% reduced proc chance"
    (re.compile(r'\bno longer has (?:an? |the )?(?:[\w%.]+ ){0,5}(?:penalt(?:y|ies)|restrictions?|drawbacks?|downsides?|debuff slow)\b', re.I), 'BUFF'),
    # ── 2026-09-22 generator-vs-proofread diff (7.38): confident direction flips ──
    (re.compile(r"\bno longer (?:reduces|decreases) (?:enemy |enemies'? |their |the target'?s? )?vision\b", re.I), 'DEL'),  # enemy vision debuff removed (NS Void)
    (re.compile(r'\bno longer reduces health restoration\b', re.I), 'DEL'),   # an ENEMY heal debuff taken away (Freezing Aura, 7.41)
    (re.compile(r'\bno longer freezes enem', re.I), 'DEL'),                              # freezing ENEMY cooldowns = a benefit removed
    (re.compile(r"\b(?:isn't|is not|no longer|won't be|will not be) (?:be )?removed\b", re.I), 'BUFF'),  # own effect now persists
    (re.compile(r'\bloss\b[^.]*?\b(?:reduced|decreased|lowered)\b(?![^.]*\bfrom\s+[-+]?\d)', re.I), 'BUFF'),  # "Gold loss on death is reduced"
    (re.compile(r'\bloss\b[^.]*?\bincreased\b(?![^.]*\bfrom\s+[-+]?\d)', re.I), 'NERF'),
    (re.compile(r'\b(?:makes|causes) enem(?:y|ies)\b[^.]*\b(?:decreased|reduced|lowered)\b', re.I), 'BUFF'),  # a debuff put on enemies
    (re.compile(r'\baffected (?:units|enemies|targets) no longer (?:take|receive|suffer|have)\b', re.I), 'NERF'),  # enemy debuff lifted
    (re.compile(r"^Added (?:an? |the )?(?:[\w']+ ){0,4}(?:icon|indicator|marker)\b", re.I), 'QoL'),  # user rule: new icon = QoL
    (re.compile(r'^\s*Now is (?:an? )?innate ability\.?\s*$', re.I), 'REWORK'),   # bare conversion only; "…that improves with X" is judged per case
    (re.compile(r'\bnow levels with\b', re.I), 'REWORK'),
    # an illusion of another kind — how it works, not a number (owner 2026-11-19, 7.42 Riftshadow Prism "Refract now
    # creates a strong illusion": "цвет REWORK, а не MISC")
    (re.compile(r'\bnow creates? an? strong illusions?\b', re.I), 'REWORK'),
    # what an effect can now reach — NEW, as "no longer affects buildings" is DEL (owner 2026-11-19, 7.42 Parasma Magic
    # Corruption: "тегом new надо, у тебя misc")
    (re.compile(r'\bnow (?:also )?affects? buildings\b', re.I), 'NEW'),
    # Fable audit of 7.42 (2026-11-19): what the interface shows — QoL; a protection a unit lost, a restriction of its
    # own, a cooldown added to a passive — NERF; an effect moved into another ability, a cost of another kind — REWORK
    (re.compile(r'\bcan now be seen by selecting\b|\bon-screen effect\b|\bfor clarity\b|\bnow displays a number\b'
                r'|\bis now reflected on the health regen bar\b', re.I), 'QoL'),
    # owner 2026-11-20 (was NERF by the Fable audit): a unit that loses its immunity to some damage (Pip Health
    # standardization), a hero disarmed during his spell, a dispel of another strength, bounces that became attacks —
    # how it works, REWORK; an Aghanim's upgrade that now also does more — NEW
    (re.compile(r'\bis no longer immune to damage from\b|\bis now fully disarmed during\b'
                r'|\bdispel at the end of the spell instead of\b|\binstead of a (?:strong|basic) one\b'
                r'|\bare now full attacks\b', re.I), 'REWORK'),
    # … a new effect ("now also fires two cannons"); a number it now also moves ("now also decreases cooldown by 10s")
    # is a BUFF / NERF as ever
    (re.compile(r"^\s*Aghanim's (?:Scepter|Shard) now also (?!(?:increases|decreases|reduces|lowers|raises)\b)", re.I),
     'NEW'),
    # a unit put under the Pip Health standardization ("Now Nimbus has fragile pip health") — MISC, as its other pip
    # rows (owner 2026-11-20: "в других случаях подобных мы misc ставили")
    (re.compile(r'\bfragile pip health\b', re.I), 'MISC'),
    (re.compile(r'\bnow has an internal \d+(?:\.\d+)?s cooldown\b', re.I), 'NERF'),
    (re.compile(r'\bmoved into a separate ability\b|\bhas been replaced with a health cost\b'
                r'|\bmin(?:imum)? health is now set by\b|\bnow has a "home jungle"', re.I), 'REWORK'),
    (re.compile(r'\bcreated illusions now apply\b|\bmay now target (?:himself|herself|itself)\b', re.I), 'NEW'),
    # owner 2026-11-20, 7.42 Wraith King Wraithfire / Alchemist: which damage triggers it now — how it works, REWORK; a
    # threshold the effect no longer has — DEL (the undispellable buff: NEW, above the canon BUFF near the top)
    (re.compile(r'\bnow applies only from (?:\w+ ){0,3}damage\b', re.I), 'REWORK'),
    (re.compile(r'\bno longer has a separate (?:\w+ ){0,3}threshold\b', re.I), 'DEL'),
    # an Aghanim's upgrade that stops giving its benefit = DEL, wind-up included ("Aghanim's Scepter no longer
    # decreases max wind-up time": the 7.37e tooltip "Decreases wind-up time …", audit 2026-10-03)
    (re.compile(r"^\s*Aghanim's (?:Scepter|Shard) no longer (?:decreases|reduces)\b", re.I), 'DEL'),
    # a new creep penalty on an own effect ("Kraken Shell: Now has 50% block value against creeps", 7.38)
    (re.compile(r'\bnow has (?:a |an )?\d+(?:\.\d+)?% [\w ]{0,25}against creeps\b', re.I), 'NERF'),
    # removing an Aghs upgrade / benefit ("no longer decreases cooldown / stun delay") = DEL, not BUFF
    (re.compile(r'\bno longer (?:decreases|reduces)\b(?:(?!wind[- ]?up).)*?\b(?:cooldown|stun delay)\b', re.I), 'DEL'),
    (re.compile(r'\bno longer (?:reduces|decreases) ', re.I),       'BUFF'),
    (re.compile(r'\bno longer requires (?:a |an )?(?:skill point|mana|charge)', re.I), 'BUFF'),
    # Owner 2026-09-27: what a TOGGLE may be switched under (silence, invisibility) doesn't change the
    # gameplay of such an ability → MISC. (Damage type rows stay as they were: "Damage type changed" and, owner
    # 2026-11-02, "classified as reflection damage" REWORK.)
    (re.compile(r'\btoggl(?:e|es|ed|ing)\b[^.]*?\b(?:no longer (?:be )?(?:disabled|breaks?|stops?)|while silenced)', re.I), 'MISC'),
    (re.compile(r'\b(?:can now|now can) be toggled while\b', re.I), 'MISC'),
    # Owner 2026-09-27: an effect that stops working on a class of targets → DEL (as "is not applied if");
    # an indicator / timer added to the HUD is interface → QoL; an ability that starts leveling with
    # another one → REWORK (mirror of "No longer levels with").
    (re.compile(r"\bdo(?:es)?(?:n't| not) affect (?:\w+ )?(?:debuff immune|spell immune|magic immune|invulnerable|illusions?)\b", re.I), 'DEL'),
    (re.compile(r'\b(?:now has an?|added an?) (?:\w+ )?(?:indicator|timer)\b', re.I), 'QoL'),
    (re.compile(r'\bnear the minimap\b', re.I),                     'QoL'),
    (re.compile(r'^\s*now (?:levels(?: up)?|scales|upgrades) with\b', re.I), 'REWORK'),
    # ── classes from the 2026-09-18 datafeed proofread (memory: sloppy-datafeed-proofread-method) ──
    # a restriction / self-penalty on the OWNER is lifted → BUFF
    # an ability that can now be pressed under silence is NEW, as "can now be cast while silenced" (owner 2026-11-05);
    # toggles stay MISC above (owner 2026-09-27)
    (re.compile(r'^\s*(?:Can )?no longer (?:be )?disabled by Silence\b', re.I), 'NEW'),   # 7.40b Kez's switch: MISC by hand
    (re.compile(r'\bno longer (?:be )?(?:disabled|interrupted|cancell?ed|blocked|prevented|stopped) by\b', re.I), 'BUFF'),
    (re.compile(r'\bno longer (?:interrupts?|cancels?) (?:movement|channel)', re.I), 'BUFF'),
    # ... but keeping invisibility while toggling is comfort, QoL (owner 2026-11-19, 7.42 Unholy Strength)
    (re.compile(r'\bwithout (?:cancelling|canceling|breaking) invisibility\b', re.I), 'QoL'),
    (re.compile(r'\b(?:can now|now can) be (?:cast|used|toggled|activated) without\b', re.I), 'BUFF'),
    # a new way to use it, not a bigger number (owner 2026-11-05, 7.38 Death Pact "Now can be cast while rooted or leashed",
    # 7.41e Sniper): NEW. "can now be toggled while" is MISC above
    (re.compile(r'\b(?:can now|now can) be (?:cast|used|activated) while\b', re.I), 'NEW'),
    # ── owner's decisions on the 7.38 rows, 2026-11-05 ──
    (re.compile(r'\bAdded alt-cast mode\b', re.I), 'QoL'),                 # "all it is is a convenience" (Death Pact)
    # how a neutral creep's AI casts it, not the ability (owner 2026-11-06: "misc всё же, т.к это просто в нейтральном
    # состоянии такая механика"; NERF on 2026-11-05 for Petrify's "only if")
    (re.compile(r'\bNeutrals will (?:auto)?cast\b', re.I), 'MISC'),
    # an aura for the team now for the hero alone changes what the ability is (owner 2026-11-06, 7.38 Dauntless)
    (re.compile(r'^Now affects only \w+ (?:himself|herself|itself)\b', re.I), 'REWORK'),
    (re.compile(r'^\s*Now is a (?:point[- ]targeted|no-target|unit[- ]targeted) ability\b', re.I), 'REWORK'),  # Magnetic Field
    # the base value stands: the upgrade got a new property, as "no longer decreases cooldown" lost one (Hawk, Marci)
    (re.compile(r"\bAghanim's (?:Shard|Scepter) now increases\b[^.]*\(from\b", re.I), 'NEW'),
    (re.compile(r'\bNow provides \d+% of the bonuses to all allies\b', re.I), 'NEW'),      # Mars's Arena Of Blood
    (re.compile(r'\bAllied Tangos provide double\b', re.I), 'NEW'),                        # Soothing Saplings
    (re.compile(r'\bspirit is now added to both\b', re.I), 'NEW'),                         # Exorcism
    (re.compile(r'\bno longer has (?:a |an )?(?:[\d.]+%? )?(?:reduced|decreased|lower|fixed|illusion vision)\b', re.I), 'BUFF'),
    (re.compile(r'\bno longer (?:freezes|loses|pauses|resets|delays)\b', re.I), 'BUFF'),
    (re.compile(r'\bis no longer (?:decreased|reduced|lowered) on \w+ from (?:his|her|their|its) own\b', re.I), 'BUFF'),
    (re.compile(r'\brequirement\b.*\b(?:is |was )?removed\b', re.I), 'BUFF'),
    (re.compile(r'\bno longer dispellable\b', re.I),                'BUFF'),   # own (de)buff can't be removed any more
    # a restriction / limit / delay is ADDED → NERF
    (re.compile(r'\bis now dispellable\b', re.I),                   'NERF'),   # own buff can now be removed
    (re.compile(r'\bis now disjointable\b', re.I),                  'NERF'),   # own projectile can now be dodged
    # … but an item's on-hit effect that now works on heroes only changes when it works — REWORK (owner 2026-11-19,
    # 7.42 Orb of Venom "Poison Attack now only triggers when attacking heroes")
    (re.compile(r'\bnow only triggers when attacking\b', re.I), 'REWORK'),
    # ... the same for an aura narrowed to some units: "Regeneration Aura now only applies to player controlled units"
    # (7.42, by Poison Attack's decision); an item effect that now also does a new thing to its target — NEW (owner
    # 2026-11-19, Nullify "now also makes the target … less susceptible to forced movement")
    (re.compile(r'\bnow only applies to\b', re.I), 'REWORK'),
    # owner 2026-11-19 (7.42): a ramp over game time that is gone — DEL, as Bracer's "No longer doubles its bonuses at
    # 25 minutes" (first REWORK, the owner asked to weigh DEL); a passive income heroes never had — NEW; a creep that
    # no longer switches aggro (you pulled the catapult off the tower) — REWORK
    (re.compile(r'\bno longer scales over (?:game )?time\b', re.I), 'DEL'),
    (re.compile(r'\bnow passively receives?\b', re.I), 'NEW'),
    (re.compile(r'\bno longer switch(?:es)? aggro\b', re.I), 'REWORK'),
    # a map objective that can now be used while silenced (7.42 Outposts): comfort, QoL (owner 2026-11-19)
    (re.compile(r'\bcan now be captured while silenced\b', re.I), 'QoL'),
    (re.compile(r'\bnow also makes the target\b', re.I), 'NEW'),
    (re.compile(r'\bnow (?:only|solely) (?:affects?|available|appl(?:ies|ied)|works|triggers?|targets?|hits?)\b', re.I), 'NERF'),
    (re.compile(r'\bnow (?:affects?|applies|works) only\b', re.I),  'NERF'),
    # a whole cooldown where there was none (7.38 "Poison Attack now has a 9s cooldown") -> REWORK: the
    # ability now works differently (owner 2026-09-28; it was NEW); longer sentences ("…cooldown before it
    # can be applied…") keep the NERF rule below
    (re.compile(r"^[A-Z][\w' ]* now has an? \d+(?:\.\d+)?s cooldown$"), 'REWORK'),
    (re.compile(r'\bnow has (?:a |an )?\d[\d./]*\s?(?:s|seconds?)? ?(?:cast point|cast time|internal cooldown|break distance|cooldown|mana cost|delay|health cost)\b', re.I), 'NERF'),
    (re.compile(r'\bnow (?:ends|expires|dies?|breaks?|is (?:cancell?ed|interrupted|removed)) (?:if|when|once|after)\b', re.I), 'NERF'),
    (re.compile(r'\b(?:may|can) only (?:trigger|proc|be cast|be used|target|affect|stack)\b', re.I), 'NERF'),
    (re.compile(r'\bnow disabled by\b', re.I),                      'NERF'),
    (re.compile(r'\bdoes not affect .* in (?:the )?fountain\b', re.I), 'NERF'),
    # ── 2026-10-03 audit of 7.40 / 7.41 (7 reviewers vs the datafeeds): more "a limit is added" phrasings ──
    (re.compile(r'\bnow only (?:starts?|begins?|deals?|activates?)\b', re.I), 'NERF'),   # Tormentor "only when attacked"
    (re.compile(r'\bnow takes \d+(?:\.\d+)?\s*(?:s|seconds?) to\b', re.I), 'NERF'),     # Pangolier roll ramp-up
    (re.compile(r'\bnow heals? (?:for )?half\b', re.I),            'NERF'),            # Salve / shared Tango
    (re.compile(r'\b(?:can now|now can) be reflected\b', re.I), 'NERF'),
    # reflected damage taken out of reflecting: an effect removed, DEL (owner 2026-10-28, 7.41)
    (re.compile(r'\bcannot be reflected back\b', re.I),             'DEL'),
    (re.compile(r'\b(?:can now|now can) miss\b', re.I),            'NERF'),            # free-movement units uphill
    (re.compile(r'^Now also provides -\d', re.I),                   'NERF'),            # a penalty added (Titanic)
    (re.compile(r'\balso goes on cooldown when\b', re.I),           'NERF'),            # Tranquil Boots' break on disassembly
    (re.compile(r"\bdo(?:es)?(?:n't| not) apply to\b", re.I),       'DEL'),             # lifesteal vs reflected damage
    # a rename / rework / loss-with-a-catch reads REWORK before any "no longer" DEL rule below
    (re.compile(r"^Aghanim's (?:Scepter|Shard) (?:slightly )?reworked\b", re.I), 'REWORK'),
    (re.compile(r'\brenamed to\b.*\b(?:no longer|now)\b', re.I),     'REWORK'),
    (re.compile(r'\bno longer\b[^.]*\bbut (?:may|can|will) still\b', re.I), 'REWORK'),  # Kez echoes "but may still create"
    # Terrain (the owner 2026-10-03: the terrain rows were "all under one tag, mush"): a map object or a piece of ground
    # that moved / was reshaped is a REWORK of the map, like "where an object appears" (7.38 rule) — not MISC. An
    # ability moved to another key slot is not this ("…moved to the 4th ability slot" stays MISC).
    (re.compile(r'\bdemoted to\b|\bcan now only evolve once\b', re.I), 'NERF'),        # a camp worth less now
    (re.compile(r'\bcan now evolve twice\b|\bpromoted to\b', re.I), 'BUFF'),
    (re.compile(r'^(?:Fixed(?!\s+(?:item\s+|ability\s+|spell\s+)?(?:description|tooltip|text))|Touched up)\b|'
                r'\bdead spot\b|\bincorrect vision\b|\bblocks preventing\b|'
                r'\bunnecessary pathing blockers?\b|\bvisually looked pathable\b', re.I), 'MISC'),   # map fixes
    (re.compile(r'\b(?:trees?|a ramp|a path|a juke path)\b[^.]*\b(?:has|have) been added\b(?![^.]*\badjusted\b)|'
                r'^(?:A|An) (?:ramp|path|juke path|bridge)\b[^.]*\bhas been added\b', re.I), 'NEW'),
    (re.compile(r'^(?:Moved|Extended|Changed the|Lowered|Cleared up)\b(?![^.]*\bslot\b)|'
                r'\b(?:expanded|reduced in size|extended slightly|added and adjusted)\b', re.I), 'REWORK'),
    (re.compile(r'\b(?:has|have) been (?:slightly |very slightly )?(?:moved|repositioned|adjusted|positioned|relocated|'
                r'shifted|reduced to|decreased in width|reworked)\b(?![^.]*\bslot\b)', re.I), 'REWORK'),
    (re.compile(r'^Very slightly adjusted\b|\btrigger area moved\b|^Adjusted an? \w|\bslightly rotated\b|'
                r'\bhave had their pull timers\b|\btree positions adjusted\b', re.I), 'REWORK'),
    (re.compile(r"\bcapture time decreased\b", re.I), 'BUFF'),                     # a watcher taken faster
    (re.compile(r"\bnow can't be activated before\b", re.I), 'NERF'),
    (re.compile(r'\b(?:slightly )?moved (?:slightly )?(?:closer|away|towards?|north|south|east|west|farther|further)\b'
                r'(?![^.]*\bslot\b)', re.I), 'REWORK'),
    (re.compile(r'\bspawn ?box(?:es)? (?:has|have) been (?:moved|enlarged|increased|decreased|reduced|resized)\b', re.I), 'REWORK'),
    # 7.42 proofread (2026-11-18): a neutral item's tier is where it sits, not a number that grew — "Tier changed from
    # 5 to 4" (27 rows) came out as b(5, 4), a red "-20%"; as "Moved from Tier 5 to Tier 3" it is REWORK. So is the
    # number of tiers itself
    (re.compile(r'^Tiers? changed from \d+(?:[-/]\d+)? to \d+(?:[-/]\d+)?\b|^Number of item tiers (?:decreased|increased|changed) from \d+ to \d+\b',
                re.I), 'REWORK'),
    # … an item's own effect that enemies can no longer dispel got stronger (canon "Now cannot be dispelled" = BUFF;
    # "Force's push now cannot be dispelled" came out MISC), an effect that now also reaches illusions or goes
    # through debuff immunity is a new property (7.38–7.41 "Now pierces Debuff Immunity" = NEW; "Frost now pierces
    # debuff immunity" came out MISC)
    (re.compile(r"\bnow (?:cannot|can't|can not) be dispelled\b", re.I), 'BUFF'),
    (re.compile(r'\bnow pierces debuff immunity\b|\bnow works? (?:with|on) illusions\b', re.I), 'NEW'),
    (re.compile(r'\bnow (?:has|have) fragile pip health\b', re.I), 'NEW'),
    # an innate Break could not touch can now be switched off by it — a new weakness, as "is now dispellable" (the
    # files: IsBreakable absent in 7.41f, "1" in 7.42, for all 19 rows of the patch; they stood NEW)
    (re.compile(r'^Now (?:fully|partially) disabled by Break\b', re.I), 'NERF'),
    # plain gains worded "now also …" that came out MISC: an upgrade that also cuts the cooldown / raises a value, a
    # heal that also applies in one more case, missed attacks that now count for the hero's counter
    (re.compile(r"^Aghanim's (?:Scepter|Shard) now also (?:decreases|reduces) (?:the )?cooldown\b|"
                r"^Aghanim's (?:Scepter|Shard) now also increases\b|\bheal now also applies\b|"
                r"\bnow count towards the\b", re.I), 'BUFF'),
    (re.compile(r'^[A-Z]\w+ now has [A-Z][\w\' ]+ ability$'), 'NEW'),            # "Fire now has Cinder Dash ability"
    # a flat number traded for one that grows with an attribute ("Damage rescaled from 325 to 300 + 1x Primal
    # Beast's Strength", 7.42): no single %, the row is a change of form
    (re.compile(r"\bfrom \d+(?:\.\d+)? to \d+(?:\.\d+)? \+ [\d.]+x [\w' ]+?(?:Strength|Agility|Intelligence)\b"), 'REWORK'),
    # Valve's wink at a coming event — a line in the Old Ones' tongue (7.42 "Y'ai 'ng'ngah, Shuggoth h'ee. Shuggoth
    # fhtagn") — TEASER, its own chip, outside filters and cells (owner 2026-11-19)
    (re.compile(r"\b(?:fhtagn|ftaghu|Shuggoth|ng'ngah|Cthulhu|R'lyeh)\b", re.I), 'TEASER'),
    # 7.42 Ringmaster (owner 2026-11-19: "это пасхалка, тизер"): a "Resentment" no game file has, daggers "being
    # sharpened", Spotlight "burning brighter" — a wink, no change
    (re.compile(r"^Resentment (?:increased|decreased) from\b|\bare being sharpened\b|^Now burning brighter\b"
                r"|^Chickens are now more duplicitous\b", re.I),        # Shadow Shaman's Fowl Play (owner 2026-11-19)
     'TEASER'),
    # owner 2026-11-19 (7.42): an effect now scaled by Item Potency is a new property of it, as "now affected by AoE
    # bonuses" — NEW; "now only triggers when attacking heroes" changes when it works — REWORK; using an item from the
    # backpack, a health bar's regen number, a ward's ally damage — interface / comfort — QoL
    (re.compile(r'\b(?:is|are) now (?:modified|affected|scaled) by item potency\b', re.I), 'NEW'),
    (re.compile(r'\bnow only triggers when attacking\b', re.I), 'REWORK'),
    (re.compile(r'\bcan now be used (?:out of|from) the backpack\b|\bnow affects the health regen value on the '
                r'healthbar\b|\bno longer has reduced damage taken from allies\b', re.I), 'QoL'),
    # a new property of units: "Illusions created by Illusion Rune now have 40% Item Potency" (7.42, owner 2026-11-19:
    # NEW); a rule lane creeps never had: "Lane creeps now move up to 25% slower if they are pulled out of lane" — REWORK
    (re.compile(r'\bnow (?:have|has) \d+% item potency\b', re.I), 'NEW'),
    # ... and without "now": item potency is new in 7.42, so an illusion's or a replica's own value is NEW too (owner
    # 2026-11-19: "Proportion Distortion illusion has 25% item potency - new")
    (re.compile(r'\b(?:have|has) \d+% item potency\b', re.I), 'NEW'),
    # ... and "Attack now has +20% bonus Item Potency" (Mirana, Sniper, Void Spirit, Weaver, Riki 7.42 — Fable audit
    # 2026-11-19: BUFF, as the Evolved enchantment's "+20% Item Potency" is NEW)
    (re.compile(r'\bnow (?:also )?ha(?:s|ve) (?:\+?[\d/]+% )?bonus item potency\b', re.I), 'NEW'),
    (re.compile(r'\bnow move up to \d+% slower if\b', re.I), 'REWORK'),
    # when a boss comes back is how the objective works, not a number of it: "Base respawn timer now decreases by 1
    # minute every time Roshan is defeated" (7.42) changes the respawn rule — REWORK, as "where and when an object
    # appears" (owner 2026-11-19); the timer that shows the Aegis and its holder is interface — QoL
    (re.compile(r'\brespawn timer now (?:decreases|increases|scales|grows)\b|\brespawn time now (?:decreases|increases)\b',
                re.I), 'REWORK'),
    (re.compile(r'^Timer now (?:visualizes|shows|displays)\b', re.I), 'QoL'),
    # a self-cast that gave nothing now gives half ("Shine now provides all bonuses on self-cast, but they will be
    # reduced by 50%"): a gain, not a new ability
    (re.compile(r'\bnow provides all bonuses on self-cast\b', re.I), 'BUFF'),
    # 7.42 proofread (2026-11-18): the same canon in other words — "Twin Gates moved to the top and bottom rim",
    # "tower moved ever so slightly to the south", "Dire fountain moved ~300 units closer", "Slightly rearranged the
    # trees", "Slightly increased the amount of highground", "Spawn boxes of the … camps have been decreased" came out
    # MISC / BUFF / NERF
    (re.compile(r'\bmoved to the (?:top|bottom|north|south|east|west|highground|lowground|high ground|low ground)\b'
                r'(?![^.]*\bslot\b)|\bmoved (?:ever so )?slightly to the\b|\bmoved ~?\d+ units\b|'
                r'^(?:Slightly )?rearranged\b|\bthe amount of (?:high|low) ?ground\b|'
                r'\bspawn ?box(?:es)?\b[^.]*\b(?:has|have) been (?:moved|enlarged|increased|decreased|reduced|resized)\b',
                re.I), 'REWORK'),
    # interface, not gameplay
    (re.compile(r'\bfor the "[^"]+" option\b', re.I),               'QoL'),
    (re.compile(r'\bnow has a distinct sound\b', re.I),             'QoL'),
    (re.compile(r'^Added a tooltip\b|^Now the default cast\b|\bicon is shown\b', re.I), 'QoL'),
    # targeting / classification rules with no real gain or loss
    (re.compile(r'\bfor prioritization\b|\bself damage before\b|\btreats creep heroes as creeps\b', re.I), 'MISC'),
    # 7.41 classes the linter kept flagging (the generator's bare "^Now " → NEW was wrong for them)
    # a new way to cast is a REWORK even when it narrows the targets (owner 2026-10-22, Bloodseeker 7.41 Bloodrage)
    (re.compile(r'^Now (?:is )?a no[- ]target ability\b', re.I),   'REWORK'),
    (re.compile(r'\bthat affects only\b|\bonly to a single\b', re.I), 'NERF'),       # Invoker scepter
    (re.compile(r"^(?:Passive|Active): [A-Z][\w' ]*\.", re.I),     'NEW'),            # a new item's ability card line
    (re.compile(r"^Aghanim's (?:Shard|Scepter): ", re.I),          'NEW'),            # a new upgrade, described
    (re.compile(r'^Now is a guaranteed\b.*\boption\b', re.I),       'REWORK'),         # neutral enchantment pools
    (re.compile(r'^\s*Now (?:is )?(?:an? )?innate ability\b', re.I), 'REWORK'),
    (re.compile(r'^Now (?:always |is )?a basic ability\b|^Now the default (?:\w+ )?ability\b', re.I), 'REWORK'),
    (re.compile(r'^Now automatically triggers\b', re.I), 'REWORK'),
    (re.compile(r'\bno longer has an? (?:\w+ ){0,3}self debuff\b', re.I), 'BUFF'),    # Bloodpact's own lockout lifted
    # a capability is taken away → DEL
    (re.compile(r'\bno longer (?:stealable|copyable|benefits? from|blinks?|copy|copies|has an alt-cast)\b', re.I), 'DEL'),
    # structural change of the entity → REWORK
    (re.compile(r'^(?:Now|Is now) (?:a|an) (?:universal|strength|agility|intelligence)\b', re.I), 'REWORK'),
    (re.compile(r'\bgained (?:a |an )?(?:\d+% )?creep penalty\b', re.I), 'NERF'),   # lifesteal now hits a creep penalty
    (re.compile(r"^Now \w+'s? (?:ultimate|basic|innate) ability\b", re.I), 'REWORK'),
    (re.compile(r'\b(?:ability )?is now (?:an? )?innate\b', re.I),  'REWORK'),
    # NERF — adding a penalty/restriction is negative (inverse of no-longer-has-penalty)
    (re.compile(r'\bnow has (?:an? |the )?(?:\w+ ){0,3}(?:penalty|restriction|drawback|downside)\b', re.I), 'NERF'),
    # NEW — new mechanic / capability added
    # map objectives (7.38 Tormentor / Lotus Pools): where and when a boss/objective appears is a
    # REWORK of how it works, not MISC; a boss/building that starts giving something is NEW
    (re.compile(r'\bspawns? (?:(?:have|has) been |are |is )?(?:repositioned|relocated)\b', re.I), 'REWORK'),
    (re.compile(r'\bspawns? for the first time at\b', re.I),       'REWORK'),
    (re.compile(r'\bonly (?:a )?single \w+ active at a time\b', re.I), 'REWORK'),
    (re.compile(r'\bdependent on the day and night cycle\b', re.I), 'REWORK'),
    (re.compile(r'\bwill now (?:spawn|grant|provide|give|drop)\b', re.I), 'NEW'),
    (re.compile(r'\bis back in the river\b|\bpits? (?:is |are )?(?:now )?located\b', re.I), 'REWORK'),
    (re.compile(r'\bno longer drops?\b', re.I),                  'DEL'),
    (re.compile(r'\bno longer stacks?\b', re.I),                 'DEL'),   # a stacking ability is taken away
    (re.compile(r'\bno longer uses charges\b', re.I),            'REWORK'),  # how the item is used changes
    (re.compile(r'\bcan now be dispelled\b|\bis now dispellable\b', re.I), 'NERF'),   # the effect can now be removed
    (re.compile(r'\bcan no longer be dispelled\b', re.I),        'BUFF'),
    # a new condition on using it is a restriction, not a feature taken away (owner 2026-10-27, Helm of the Dominator
    # 7.39e "Dominate can no longer be used if the currently dominated creep took damage …": NERF, not DEL); "Can no
    # longer be cast while rooted" stays DEL (owner 2026-09-27, patch-tags.md)
    (re.compile(r'\bcan no longer be used (?:if|when|after|within)\b', re.I), 'NERF'),
    # a protection is gone -> a NEW way to interact with it (Kobold aura can now be broken)
    (re.compile(r'\bno longer unbreakable\b', re.I),             'NEW'),
    # something that did not exist before: a cooldown, a restore on use
    (re.compile(r"^[A-Z][\w']*(?: [\w']+){0,3} now (?:also )?restores\b"), 'NEW'),
    # a limit on how long an effect lasts changes how it is used
    (re.compile(r'\bnow has an? \d+(?:\.\d+)?\s*(?:minutes?|min|s|seconds?) duration\b', re.I), 'REWORK'),
    # a loss with a stated compensation ("can no longer … However, … still …")
    (re.compile(r'\bno longer\b.*\bHowever\b.*\bstill\b', re.I), 'REWORK'),
    (re.compile(r'^No longer (?:refills|triggers|activates)\b', re.I), 'DEL'),
    (re.compile(r'\bno longer have special rules\b|\bnow consistent across\b', re.I), 'REWORK'),
    (re.compile(r'^The following (?:sources|targets|abilities|items|units)\b.*\b(?:do not|no longer|now)\b', re.I), 'REWORK'),
    # a rule changed for many abilities at once, its list and its special cases (owner 2026-10-27, 7.40 Invulnerability
    # Targeting "like 7.38 Lifesteal"): REWORK rows of a reworked mechanic, not MISC
    (re.compile(r'^The following (?:spells|abilities|items) have been changed\b', re.I), 'REWORK'),
    (re.compile(r'\bthat previously could\b.*\bno longer do so\b', re.I), 'REWORK'),
    (re.compile(r'\bthere are these special cases\b', re.I), 'REWORK'),
    (re.compile(r'\bstill result in\b.*\bcan benefit from\b', re.I), 'REWORK'),
    (re.compile(r"^[A-Z][\w']*(?: [\w']+){0,2} now (?:also )?(?:grants|provides|drops|gives)\b"), 'NEW'),
    (re.compile(r'\bAdded to Captains Mode\b', re.I),               'NEW'),
    # a bonus that now reaches someone it didn't (owner 2026-11-07, 7.38 Earth Spirit "Bonus movespeed is also granted
    # to Earth Spirit when rolling over an allied hero" — new, not a buff of a number)
    (re.compile(r'\bis (?:now )?also (?:granted|given|applied) to\b', re.I), 'NEW'),
    (re.compile(r'\bCan now be disassembled\b', re.I),              'NEW'),
    (re.compile(r'\bno longer disjointable\b', re.I),               'DEL'),
    (re.compile(r'^Now (?:also )?(?:passively |actively )?(?:grants|provides|gains?|adds?|applies?|deals?|increases|fires?|spawns?|summons?)', re.I), 'NEW'),
    (re.compile(r"\bAghanim's (?:Scepter|Shard) now (?:also )?(?:grants|provides|applies?|adds?|deals?|allows?|gives?|causes?)", re.I), 'NEW'),
    (re.compile(r'^Added\b', re.I),                                 'NEW'),
    # QoL — UI / display / convenience, no gameplay change
    (re.compile(r'\bpressing (?:and holding )?alt\b', re.I),        'QoL'),
    (re.compile(r'\bholding (?:and pressing )?alt\b', re.I),        'QoL'),
    (re.compile(r'\balt[\s-]clicking?\b', re.I),                    'QoL'),
    # MISC — mechanic toggle, classification change, polish, fix, no effective change
    (re.compile(r'\bClassified as\b', re.I),                        'MISC'),
    (re.compile(r'\btooltip now (?:shows?|displays?|reflects?)\b', re.I), 'QoL'),  # "The tooltip now shows..." — display-only improvement
    (re.compile(r'^\s*Fixed\s+(?:item\s+|ability\s+|spell\s+)?(?:description|tooltip|text)\b', re.I), 'QoL'),  # "Fixed description stating..." — tooltip fix
    (re.compile(r'^\s*Fixed\b', re.I),                              'MISC'),  # "Fixed X" — gameplay bug fix
    (re.compile(r'\bunchanged\b', re.I),                            'MISC'),  # "X is unchanged"
    # DEL — explicit removal / no-longer-targets / no-longer-applies
    (re.compile(r'\bcan no longer (?:target|be cast|be used|trigger|attack|move|stack|proc|crit|bash|leap|fly|deny|sell|disassemble)', re.I), 'DEL'),
    (re.compile(r'\bno longer (?:be )?applied by illusions\b', re.I), 'DEL'),
    (re.compile(r'\bno longer (?:applies?|affects?) ', re.I),       'DEL'),
    (re.compile(r'\bis not applied if\b', re.I),                    'DEL'),   # "X is not applied if Debuff Immune"
    (re.compile(r'\bno longer upgraded with Aghanim', re.I),        'DEL'),
    (re.compile(r"\bno longer.*'s? ability\b", re.I),               'DEL'),
    (re.compile(r'\bno longer (?:provides|grants|deals|fires|spawns|summons|adds|increases|works|considered|active|applied|kills|slows|buffs|restores|heals|casts|silences|freezes|suspends|manipulates|instantly)\b', re.I), 'DEL'),
    (re.compile(r'\bno longer levels with\b', re.I),                'REWORK'),  # memory rule: structural
    (re.compile(r'\bno longer has\b(?! (?:an? |the )?(?:\w+ )?(?:penalty|restriction|drawback|downside|debuff slow|separate))', re.I), 'DEL'),  # "X no longer has True Strike/feature" → DEL; excludes BUFF-pattern exceptions
    (re.compile(r'\bno longer counts? as\b', re.I),                 'DEL'),    # "Hero Creeps no longer count as heroes"
    (re.compile(r'\bRemoved\b', re.I),                              'DEL'),
    # REWORK
    (re.compile(r'\breplaced with\b', re.I),                        'REWORK'),
    (re.compile(r'\breworked\b', re.I),                             'REWORK'),
    (re.compile(r'\brescaled\b', re.I),                             'REWORK'),
    (re.compile(r'\bchanged from\b', re.I),                         'REWORK'),
    (re.compile(r'\bis now cancell?ed if.*interrupted\b', re.I),    'NERF'),    # movement now breaks on interrupt — a new restriction
    (re.compile(r'\bare now treated as\b', re.I),                   'REWORK'),  # reclassification: "X are now treated as Y"
    (re.compile(r'\bno longer considers?\b', re.I),                 'REWORK'),  # scoping: "no longer considers X for Y"
    # General "Now ..." → NEW unless context says otherwise
    (re.compile(r'^Now also\b', re.I),                              'NEW'),
    (re.compile(r'^Now ', re.I),                                    'NEW'),
]

# Cost / regen-style "lower-is-buff" keywords. When the row text matches one
# of these AND `b()` is the badge, set l=True.
LOWER_IS_BUFF = re.compile(
    r'(?<!reduction\s)(?<!resist\s)\b('
    r'cooldown|mana ?cost|mana cost|cast (?:point|time)|cast point|cast time'
    r'|gold cost|item cost|recipe cost|total cost|cost'
    r'|base attack time|\bBAT\b'
    r'|incoming damage|damage taken|damage vulnerability|building damage penalty'
    r'|status duration|stun resistance'
    r'|damage spread'                         # narrower = steadier hits (owner 2026-11-20)
    r'|attack point|projectile speed.*incoming'
    r'|penalty'
    r'|(?:intelligence|agility|strength)\s+required'
    r'|recharge\s+(?:time|cooldown)'
    r'|channel\s+time'
    r'|activation\s+time'
    r'|restore\s+time'
    r'|respawn\s+time'
    # 2026-09-18 proofread: self-penalties, owner-side timers and thresholds
    r'|disable\s+(?:range|radius|duration)'
    r'|(?:damage|attack|tick|pulse|explosion|spawn)\s+interval'
    r'|flight\s+(?:time|duration)'
    # 2026-10-03 second audit: seconds per attack, a count of hits needed, a wait before an effect lands,
    # an own illusion's damage penalty
    r'|attack\s+rate'
    r'|attacks?\s+required'
    # 2026-10-03 cross-check of 7.40-7.41 against the proofread flags
    r'|mana\s*costs'
    r'|mana\s*/\s*sec'
    r'|capture\s+time'
    r'|formation\s+(?:time|delay)'
    r'|time\s+to\s+max\s+effect'
    r'|time\s+until\s+\w+\s+starts'
    r'|charge\s+loss'
    r'|explosion\s+delay|fade\s+time|self\s+damage'
    r'|time\s+for\s+\w+\s+application'
    r'|illusion\s+damage\s+(?:reduction|penalty)'
    r'|stun\s+duration\s+from\s+falling'
    r'|slow\s+resistance\s+loss|status\s+resistance\s+loss'   # self-penalty (Spirit Breaker Relentless); NOT enemy armor/AS/MR reduction
    r'|creep\s+penalty|max\s+mana\s+penalty|vision\s+penalty'
    r'|mana\s+per\s+second'
    r'|health\s+cost'
    r'|(?:damage|hit)\s+threshold'
    # 2026-09-22: owner-side timers and trigger requirements
    r'|restock\s+time'
    # 2026-09-25: time to gain / restore a charge (Consecrated Wraps "Hallowed charge gain time 3s -> 4s" = NERF)
    r'|charge\s+(?:gain|restore|replenish|regen(?:eration)?)\s+time'
    r'|base\s+attack\s+rate'                     # seconds per attack (Kez Sai/Katana) — like BAT
    r'|required\s+to\s+(?:trigger|cast|activate|proc)'
    r'|(?:familiar|summon(?:ed)?|illusion|ward|spirit|eidolon|treant)s?\s+(?:gold\s+)?bounty'   # own summon's bounty
    # a bare "Bounty increased" sits under the ability whose unit it is (7.42 Tempest Double 70 → 100 + 10 per level:
    # the enemy's gold; creeps say "Gold Bounty" / "XP Bounty") — Fable audit 2026-11-19
    r'|^bounty\s+(?:increased|decreased|rescaled|changed)\b'
    # 7.37e proofread: a charge's wait (Demonic Purge Scepter), the caster's own spell damage reflected back (QoP)
    r'|charge\s+restoration\s+time'
    r'|outgoing\s+(?:spell\s+)?damage\s+reflected'
    # 2026-10-05 audit: faster forage (7.41e), a smaller Blur vanish radius (7.41 PA), a shorter wait for the max bonus
    r'|forage\s+time'
    r'|vanish\s+radius'
    r'|time\s+until\s+max(?:imum)?\s+\w+'
    r'|time\s+to\s+max(?:imum)?\s+\w+'           # 7.37b Solar Flare "Time to max damage/attack speed"
    # 7.42 proofread 2026-11-18: a wait before the spell acts (Gorgon's Grasp "Initial delay 1s -> 0.8s"), a shorter
    # channel (Fiend's Gate), a charge that comes back sooner (Spellslinger "Salvo restore duration"), less of an own
    # bonus lost (Tranquil Boots "Health Regen bonus lost … 14 -> 12") — all came out NERF
    r'|initial\s+delay|channel\s+(?:duration|time)|restore\s+duration|bonus\s+lost'
    # … and the waits of 7.42's heroes (Weaver "Thread establishing time", Dazzle "Soul Return Time")
    r'|establishing\s+time|return\s+time'
    # more experience to reach a level is slower levelling (7.42 "Total amount of experience needed to reach level 30
    # increased from 64400 to 66600" stood a green +3%; owner 2026-11-19: NERF)
    r'|experience\s+needed|xp\s+needed'
    r')\b',
    re.I,
)
_NOT_LOWER_IS_BUFF = re.compile(
    r'\bcooldown\s+reduction\b'
    r'|\bcooldown\s+advance\b'
    r'|\badvances\s+cooldown\b'                       # 7.42 "Duel Advances Cooldown on Victory decreased" = a cut
    r'|\bcooldown\s+(?:speed|recovery)\b'
    r'|\bmana\s+cost\s+reduction\b'
    r'|\bmana\s*cost(?:/\w+)?\s+reduction\b'          # "Manacost/Manaloss Reduction increased" (7.40 talent)
    r'|\bdamage\s+taken\s+reduction\b'                # "Illusion Damage Taken Reduction increased" (7.41 talent)
    r'|\bfalse\s+flight\b'                            # an ability's name, not a flight time
    r'|\ballied\s*/\s*self\s+damage\b'                # Luna Lunar Blessing bonus damage, not a self-hit (7.41 talent)
    r'|\bwithout\s+(?:a\s+)?cooldown\b'               # "grace period … without a cooldown increased" (7.38b)
    r'|\btime\s+reduction\b'                          # "Charge Restore Time Reduction decreased" (7.39 talent)
    r'|\bincoming\s+damage\s+buff\b'                  # Roshan's own Roar buff (7.39)
    r'|\bpenalty\s+reduction\b'
    # "Magic Resistance bonus" is higher-is-better (item stat), not incoming damage
    r'|\bmagic\s+resistance\s+bonus\b'
    # enemy-side values scaling "per cooldown" / max slow (Faceless Void, Open Wounds): higher is better
    r'|\bper\s+cooldown\b'
    r'|\bmax\s+slow\b'
    r'|\bsearch\s+radius\b'
    r'|\bmax\s+health\s+minimum\b'
    # "damage threshold reduction" is the opposite of a raw "damage threshold": more reduction = better
    r'|\bthreshold\s+reduction\b'
    # own bonuses that merely mention a lower-is-better word (2026-09-22)
    r'|\b(?:BAT|base\s+attack\s+time)\s+reduction\b'
    r'|\b(?:while|when|during)\s+(?:on\s+)?cooldown\b'
    r'|\bdamage\s+taken\s+as\s+(?:damage\s+)?bonus\b'
    # a NEGATIVE cooldown amount ("-5s Unstable Concoction Cooldown") is a reduction talent
    r'|-\d[\d./]*s?\s+(?:[\w\']+\s+){0,4}cooldown\b',
    re.I,
)


# Exact-substring overrides for rows the heuristics tag wrong: data/rules/tag_overrides.json (in order, first
# match wins; each with the owner's reason). Add there when a generated scaffold gets the wrong tag.
TAG_OVERRIDES = {e["text"]: e["tag"] for e in json.loads(
    (Path(__file__).resolve().parents[2] / "data" / "rules" / "tag_overrides.json").read_text(encoding="utf-8")
)["overrides"]}


_OLD_HEAL_STATS = re.compile(r"\bHealing, Health Regen, Lifesteal,? and Spell Lifesteal\b", re.I)
_RENAME_SPLIT = re.compile(r"\b(?:now|replaced with)\b", re.I)
_ROW_NUMS = re.compile(r"\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)*%?")


def _heal_stats_renamed(clean):
    """7.39: Health Restoration took the place of Healing / Health Regen / Lifesteal / Spell Lifesteal. A row that only
    says so with the same numbers ("instead of reducing … by 14/21/28/35%, now reduces Health Restoration by
    14/21/28/35%") renames the mechanic, the effect stays — MISC, not REWORK (owner 2026-10-27). Other numbers
    (Outfight Them! 50% -> 30/40/50/60%) are a change."""
    if not _OLD_HEAL_STATS.search(clean) or "health restoration" not in clean.lower():
        return False
    parts = _RENAME_SPLIT.split(clean, maxsplit=1)
    if len(parts) != 2:
        return False
    before, after = (_ROW_NUMS.findall(p) for p in parts)
    return bool(before) and before == after


_EXTRA_CREEP_AT = re.compile(r'\b(?:time at which|timing)\b[^.]*\b(?:melee|ranged|siege|flagbearer|lane) creeps?\b'
                             r'[^.]*\bfrom (\d{1,2}):(\d{2}) to (\d{1,2}):(\d{2})\b'
                             r'|\b(?:melee|ranged|siege|flagbearer) creeps?[^.]*\b(?:is|are) added\b[^.]*'
                             r'\bfrom (\d{1,2}):(\d{2}) to (\d{1,2}):(\d{2})\b', re.I)


def _extra_creep_timing(clean):
    """An extra lane creep coming earlier is its BUFF, later its NERF, whatever Valve's verb (owner 2026-10-16, 7.41
    "+1 siege creep timing decreased from 35:00 to 30:00"; 7.42 "Time at which 1 Ranged creep is added changed from
    40:00 to 35:00" said "changed" and came out REWORK). None for any other row."""
    m = _EXTRA_CREEP_AT.search(clean)
    if not m:
        return None
    g = [int(x) for x in m.groups() if x is not None]
    old, new = g[0] * 60 + g[1], g[2] * 60 + g[3]
    return None if old == new else ('BUFF' if new < old else 'NERF')


def _extra_creep_badge(text):
    """The extra lane creep's time as a % badge: b(old, new) in minutes, l=True — earlier is better (owner 2026-11-19,
    7.42 "Time at which 1 Ranged creep is added changed from 40:00 to 35:00": "% разницы нет"). None for other rows."""
    m = _EXTRA_CREEP_AT.search(_strip_html(text))
    if not m:
        return None
    g = [int(x) for x in m.groups() if x is not None]
    old, new = g[0] + g[1] / 60, g[2] + g[3] / 60
    return None if old == new else f'b({old:g}, {new:g}, l=True)'


def _guess_tag(text):
    """Heuristic tag from row text. Returns 'BUFF'/'NERF'/'REWORK'/'NEW'/'DEL'/
    'MISC'/'QoL'/None. None means caller should derive from b()/badge."""
    clean = _strip_html(text)
    if _heal_stats_renamed(clean):
        return 'MISC'
    # Manual overrides checked first — highest priority
    clean_lower = clean.lower()
    for substr, tag in TAG_OVERRIDES.items():
        if substr.lower() in clean_lower:
            return tag
    extra_creep = _extra_creep_timing(clean)
    if extra_creep:
        return extra_creep
    for rx, tag in CANONICAL_TAGS:
        if rx.search(clean):
            return tag
    # "increased/decreased by N" without from/to → can't make b(), emit tag
    # has_from_to: "from X to Y" where X/Y are slash-separated levels (parseable)
    has_parseable_from_to = bool(re.search(
        r'\bfrom\s+[-+]?\d[\d./]*\s+to\s+[-+]?\d[\d./]*', clean, re.I
    )) and not re.search(r'\bfrom\s+[-+]?\d+[^0-9\s./]*[–]', clean)
    # Unparseable values ("from 3 minutes to 4 minutes") can't become b(), so the
    # direction must come from here — honour lower-is-better (intervals, costs…).
    lower = _is_lower_better(clean)
    if re.search(r'\b(increased|raised)\b', clean, re.I):
        return None if has_parseable_from_to else ('NERF' if lower else 'BUFF')
    if re.search(r'\b(decreased|reduced|lowered|worsened)\b', clean, re.I):
        return None if has_parseable_from_to else ('BUFF' if lower else 'NERF')
    if re.search(r'\bimproved\b', clean, re.I):
        return None if has_parseable_from_to else 'BUFF'
    # Old notes (7.06-7.20) often have no verb at all (weights research 2026-11-11: 251 rows, 172 of them read as
    # MISC): "Cooldown from 40/32/24/16 to 15" -> the parseable values decide, as with a verb.
    if has_parseable_from_to or _FROM_TO_RE.search(clean):
        return None
    verbless = None if re.search(r'\bchange[ds]?\b', clean, re.I) else _VERBLESS_FROM_TO_RE.search(clean)
    if verbless:
        old, new = (float(x) for x in verbless.groups())
        if re.search(r'\btalent\b', clean, re.I):
            old, new, lower = abs(old), abs(new), False
        if old != new:
            return 'BUFF' if (new > old) != lower else 'NERF'
    return 'MISC'


# "Talent: Level 20 Talent from +12 Spiders Attack Damage to +14", "Scepter damage from 2x to 1.75x": words or units
# sit between the numbers, so no b(); the first value of each side decides. A talent value is a bonus, its sign only
# says which way the stat goes: "-3s Lucent Beam Cooldown to -4s" is a bigger bonus. "change from A to B" is a swap.
_VERBLESS_FROM_TO_RE = re.compile(
    r'\bfrom\s+([-+]?\d+(?:\.\d+)?)[^.]*?\bto\s+([-+]?\d+(?:\.\d+)?)', re.I)


def _is_lower_better(text):
    clean = _strip_html(text)
    if _NOT_LOWER_IS_BUFF.search(clean):
        return False
    return bool(LOWER_IS_BUFF.search(clean))


# ---------- B() / TEXT-TAG EMITTERS ----------

# unit suffix: % / s / x, and g for gold ("Total cost increased from 4450g to 4550g", 7.41f Hurricane Pike: no
# old/new, so the normalized record had no lower_is_better and the validator read the right NERF as a mistake)
_FROM_TO_RE = re.compile(
    r'\bfrom\s+'                                # 'from '
    r'([-+]?\d+(?:\.\d+)?(?:[/–][-+]?\d+(?:\.\d+)?)*[%sxg]?)\s+'  # OLD value(s), optional unit suffix
    r'to\s+'                                    # 'to '
    r'([-+]?\d+(?:\.\d+)?(?:[/–][-+]?\d+(?:\.\d+)?)*[%sxg]?)',    # NEW value(s)
)
