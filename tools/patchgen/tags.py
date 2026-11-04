"""Which tag a patch note gets: the canonical phrases, Valve's own errors, the owner's decisions."""
import re

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
    (re.compile(r'\bno longer has (?:an? |the )?(?:\w+ ){0,5}(?:penalt(?:y|ies)|restrictions?|drawbacks?|downsides?|debuff slow)\b', re.I), 'BUFF'),
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
    (re.compile(r'\bno longer (?:be )?(?:disabled|interrupted|cancell?ed|blocked|prevented|stopped) by\b', re.I), 'BUFF'),
    (re.compile(r'\bno longer (?:interrupts?|cancels?) (?:movement|channel)', re.I), 'BUFF'),
    (re.compile(r'\b(?:can now|now can) be (?:cast|used|toggled|activated) (?:without|while)\b', re.I), 'BUFF'),
    (re.compile(r'\bno longer has (?:a |an )?(?:reduced|decreased|lower|fixed|illusion vision)\b', re.I), 'BUFF'),
    (re.compile(r'\bno longer (?:freezes|loses|pauses|resets|delays)\b', re.I), 'BUFF'),
    (re.compile(r'\bis no longer (?:decreased|reduced|lowered) on \w+ from (?:his|her|their|its) own\b', re.I), 'BUFF'),
    (re.compile(r'\brequirement\b.*\b(?:is |was )?removed\b', re.I), 'BUFF'),
    (re.compile(r'\bno longer dispellable\b', re.I),                'BUFF'),   # own (de)buff can't be removed any more
    # a restriction / limit / delay is ADDED → NERF
    (re.compile(r'\bis now dispellable\b', re.I),                   'NERF'),   # own buff can now be removed
    (re.compile(r'\bis now disjointable\b', re.I),                  'NERF'),   # own projectile can now be dodged
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
    # 7.37e proofread: a charge's wait (Demonic Purge Scepter), the caster's own spell damage reflected back (QoP)
    r'|charge\s+restoration\s+time'
    r'|outgoing\s+(?:spell\s+)?damage\s+reflected'
    # 2026-10-05 audit: faster forage (7.41e), a smaller Blur vanish radius (7.41 PA), a shorter wait for the max bonus
    r'|forage\s+time'
    r'|vanish\s+radius'
    r'|time\s+until\s+max(?:imum)?\s+\w+'
    r'|time\s+to\s+max(?:imum)?\s+\w+'           # 7.37b Solar Flare "Time to max damage/attack speed"
    r')\b',
    re.I,
)
_NOT_LOWER_IS_BUFF = re.compile(
    r'\bcooldown\s+reduction\b'
    r'|\bcooldown\s+advance\b'
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


# Exact-substring overrides for cases where heuristics give the wrong tag.
# Key = substring to look for (case-insensitive), Value = forced tag.
# Add here when a generated scaffold consistently gets the wrong tag.
TAG_OVERRIDES = {
    # owner 2026-11-05: the behaviour changed, neither side only loses (7.40 The Shining, 7.41 free movement uphill)
    "only starts dealing damage to the surrounding enemies when attacked": "REWORK",
    "units with free movement now can miss their attacks":                 "REWORK",
    # owner 2026-10-27 (7.39): convenience of control, not a gameplay change → QoL (first: the row also says
    # "Now requires", which is REWORK below)
    "added an auto-cast":              "QoL",   # Quill Spray: "Right-click the ability to … cast it"
    "no longer automatically rejoins": "QoL",   # Astral Spirit: now the duration or Return brings it back
    # a click past max range used to blink only 75% of it — a penalty gone (owner 2026-10-27, 7.39 Blinks)
    "no longer has an overshoot range": "BUFF",
    # owner 2026-10-27 (7.39 Ringmaster): a Souvenir on death is a new grant, not a rework of the respawn one;
    # "will no longer be granted … if he dies to a Neutral Creep or Roshan" takes a case away — DEL
    "will be granted one upon death":   "NEW",
    "will no longer be granted":        "DEL",
    "starts with all":              "MISC",
    "separate heal reduction":      "MISC",
    "health restoration consolidat": "MISC",  # "consolidated Health Restoration" = structural
    "now shares cooldown":          "MISC",
    "now has a shared cooldown":    "MISC",
    "now requires aghanim's":       "NERF",    # a capability now gated behind Aghs (checked before "now requires")
    "now requires a single target tree": "NERF",  # 7.37 Nature's Call (Ironwood Treant): a new cast restriction
    "now requires at least one other allied hero": "NEW",  # 7.38 Hookshot (Hookup): a new condition (owner 2026-11-02)
    "now requires":                 "REWORK",  # "Now requires X instead of Y"
    "instead of only higher":       "BUFF",    # scope widened ("…equal or higher level, instead of only higher"; audit 2026-10-03)
    # 7.37e proofread (2026-10-28): the effect decides, not the phrase template
    "stack per second instead of all stacks": "BUFF",   # Natural Order: enemies keep the debuff longer after leaving
    "now also applies to units under":        "BUFF",   # Apex Predator: own bonus widened to controlled units
    "will no longer follow":                  "DEL",    # Chain Frost: a bought-back hero is no longer chased
    "buff is removed when":                   "NERF",   # Presence of the Dark Lord: a new way to lose the bonus
    "turn rate bonus changed from flat":      "NERF",   # Rolling Thunder: +110 → +40% (results in +48)
    "treant gold bounty rescaled":            "NERF",   # Nature's Call: the enemy gets more gold for a treant
    "no longer explode":                      "DEL",    # Eldritch Summoning: imps killed by heroes do not blow up
    "improved behavior":                      "QoL",    # Stroke of Fate at max cast range: handling, not power (owner)
    # 7.37 proofread (2026-10-30)
    "no longer an innate ability":            "REWORK", # the old innate becomes a basic ability ("is now an innate" = REWORK)
    "charges, and depletes a charge every time": "REWORK",  # Philosopher's Stone: a stone that runs out (owner)
    "no longer a levelable innate ability":   "REWORK", # Lina Fiery Soul
    "now always drops roshan's banner":       "NEW",    # Roshan's second death
    "now drops refresher shard and cheese during daytime": "REWORK",  # third death: by the time of day
    "are now fully disabled by break":        "NERF",
    "are now partially disabled by break":    "NERF",
    "no longer always cast chain lightning":  "DEL",    # Harpy Stormcrafter pulled by lane creeps
    "no longer requires the target to remain still": "BUFF",  # Shadow Amulet Fade: a restriction gone
    "no longer refreshes its cooldown if cast on self": "DEL",
    "now slows the target by":                "NEW",    # Fade
    "cooldown no longer ticks down if":       "NERF",   # Trusty Shovel out of the neutral slot
    "always digs up a water rune":            "NEW",
    "returning as a tier":                    "NEW",    # a neutral item back in the pool
    "now is a tier":                          "REWORK", # a neutral item's tier moved, as "Moved from Tier X to Y"
    "can now change direction while flopping": "NEW",   # Ogre Seal Totem
    "now stacks with other sources of":       "BUFF",   # Void Brawler status resistance
    "can now target roshan and tormentors":   "NEW",
    "is now applied on any kill made by":     "NEW",    # Earthshaker knockback, not only Enchant Totem
    "no longer prevents damage for a short duration": "DEL",  # Time Walk (Chronosphere facet)
    "touched by the ghostship receive a stronger": "NEW",  # Ghostship Scepter
    "in addition, lifestealer gains permanent max hp": "NEW",  # Feast
    "now also increases the attack distance threshold": "NEW",  # Spirit Bear
    "spirit bear can no longer equip its own neutral items": "REWORK",  # copies Lone Druid's instead
    "can no longer be activated. rotating glaives moved": "REWORK",  # Lucent Beam / Lunar Orbit split
    "health gained from lifesteal now also heals": "NEW",  # Bodyguard
    "new facet":                              "NEW",
    "no longer a levelable ability, now has a base": "REWORK",  # Mana Shield
    "now also increases duration by":         "NEW",    # Wukong's Command (facet)
    "is no longer destroyed or goes on additional cooldown": "BUFF",  # Ofrenda: a penalty gone
    "no longer scales with vendetta":         "DEL",    # as "no longer benefits from" (owner 2026-10-30: not REWORK)
    "now scales with pierce the veil":        "BUFF",   # Ofrenda's attack speed grows with the ultimate
    # owner 2026-10-30 ("Warpath почему-то rework … много где ещё такие же ситуации"): the effect decides
    "instead of a 33% chance to do nothing, now has": "BUFF",  # Reality Rift (Irrationality): Silence instead of nothing
    "lingering bonus movement speed is now determined by": "NERF",  # Charge of Darkness: the current speed, not the max
    "no longer spell stealable":              "DEL",
    "no longer procs magic stick":            "BUFF",   # the enemy no longer gets charges
    "now procs magic stick":                  "NERF",   # the enemy now gets charges
    "now shows a preview of":                 "QoL",
    "now also lowers strike cooldown by":     "NEW",    # Storm Surge
    "aghanim's shard pulses apply 1 stinger": "NEW",
    "every hero kill increases max souls by 1 until": "NEW",   # the facet takes the old default
    "hero kills no longer increase max souls": "DEL",
    "debuff now grants that the next attack": "NEW",    # Electric Vortex (facet)
    "no longer passively grants allies movement speed": "DEL",
    "now increases active movement speed bonus by additional": "BUFF",
    "now also grants 1 attack projectile speed": "NEW",
    "can see roshan's respawn timer":         "NEW",
    "are now applied when denying allies or traps": "NEW",
    "traps no longer provide vision":         "DEL",
    "traps now always take":                  "REWORK",
    "now always teleports the target enemy to": "REWORK",
    "damage no longer pierces magic resistance": "NERF",
    "can now be put on alt-cast":             "NEW",
    "can no longer be refreshed":             "NERF",
    "aoe now equals to":                      "REWORK", # Focus Fire (Tailwind facet)
    "now cannot be lower than the average":   "NEW",    # Mental Fortitude
    "when in melee form, troll warlord has":  "REWORK", # Berserker's Rage, a basic ability by stance
    # 7.37b proofread (2026-10-30): a new property is NEW even when it helps (owner's 7.37c/d rule)
    "now refunds clockwerk":                  "NEW",    # Hookshot (Hookup): mana refund
    "now also increases attack range for units under": "NEW",  # Enchant (Spellbound)
    "now increases duration to":              "NEW",    # Scurry (Hunter facet): the facet takes over the old duration
    "duration is no longer reduced":          "BUFF",   # Burning Spear (Incendiary): a penalty gone
    "can now be cast during channeling":      "NEW",    # Quas / Wex / Exort / Invoke
    "now stacks instead of refreshing":       "NEW",    # Magnus talent
    "of bonus damage is converted to base damage": "BUFF",  # Illusory Armaments: Phantom Lancer 65% → 100%
    "self bonus move speed when activated":   "NEW",    # Trample (Romp n' Stomp)
    "stun duration now increases by":         "NEW",    # Snowball: +0.2s per ally
    "now counts one debuff per unique":       "NERF",   # Septic Shock: Shiva's counts 1, not 3
    "is now decreased by the illusion damage reduction": "NERF",  # Predator: illusions' bonus cut
    "now has a primary and secondary target": "NEW",    # Death Ward (Cleft Death)
    # 7.37c proofread (2026-10-29)
    # owner 2026-10-29: these three are NEW (a new property), not BUFF
    "no longer requires enchant totem to be leveled": "NEW",   # Slugger: active without Enchant Totem
    "multicasts now prioritize":              "NEW",    # Fire Shield: a target order for multicasts
    "is now applied during the rush":         "NEW",    # Phantom Rush: the agility during the rush too
    # 7.38 re-read (2026-11-02), by the owner's rules: a new property is NEW even when it helps
    "all sources of evasion are doubled":     "NEW",    # Scurry had no evasion in 7.37e
    "now prioritizes heroes":                 "NEW",    # Gunslinger: a target order, as Fire Shield above
    "kills a non-hero unit during":           "NEW",    # Exterminator: a new way to cut Tricks of the Trade's cooldown
    "bonus experience for courier and ward":  "NEW",    # Contract Killer: a new source of experience
    "spell lifesteal apply to reflected":     "NEW",    # Succubus (Bondage)
    "can now be decreased by status resistance": "NEW", # Arcane Curse: both ways, Debuff Duration lengthens it
    "all attribute bonus provides an additional": "NEW",  # Accumulation: +3 replaces the removed +100%
    "improved glaive collision behavior":     "QoL",    # as "improved behavior" above (owner 2026-10-28)
    "can now be put on autocast":             "QoL",    # as "added an auto-cast" above (Tar Bomb)
    # the owner's own answers to the 7.38 re-read (2026-11-02)
    "classified as reflection damage":        "REWORK", # Quill Spray, Strike Damage: the kind of damage changes
    "no longer take increased":               "DEL",    # Winter's Curse: the amplification is gone
    "now has the same effect for both":       "REWORK", # Arc Warden and his Double: values evened out both ways
    # 7.37d proofread (2026-10-29)
    "no longer doubles its bonuses":          "DEL",    # Bracer / Wraith Band / Null Talisman: the 25-minute doubling
    "no longer makes caster or ally unslowable": "DEL", # Disperser Suppress (40% slow resistance comes instead, NEW)
    "always gains a charge when the owner dies": "NEW", # Spirit Vessel: a new way to get charges (owner 2026-10-29)
    "now triggers on death effects":          "NEW",    # Chen Martyrdom: sacrificed creeps' On Death effects (owner)
    "are no longer pulled to the center":     "REWORK", # Power Cogs: caught heroes placed another way (owner)
    "alt cast behavior now has":              "NERF",   # Drinking Buddies: alt cast at 50% of the cast range (owner)
    "now heals creeps for":                   "NERF",   # Leech Seed: creeps were healed in full before (7.37c KV +
                                                        # tooltip), now at 50% — creep_heal_reduction_pct (owner asked)
    "now disables blink dagger":              "NERF",   # Mana Shield: absorbing damage now counts as taking it
    "no longer allows to hit the same enemy": "DEL",    # Mirana Shard: secondary Starstorms no longer stack on one unit
    "percentually change the base damage":    "NEW",    # Illusory Armaments: base-damage % effects now count the bonus
    "toggling items no longer breaks invis":  "QoL",    # Riki: as 7.41 Burn toggling — handling, not power
    "can no longer shoot arrows while":       "DEL",    # Whirlwind Focus Fire: no own attacks while channeling
    "invisibility buff is now dispelled if":  "NERF",   # Windrun Scepter: a new way to lose the invisibility
    "instead of":                   "REWORK",  # component/requirement swap
    "respawn time increased":       "NERF",    # "increased" heuristic gives BUFF, but higher respawn = worse
    "respawn time decreased":       "BUFF",
    "no longer reduces cooldown":   "DEL",     # removal of a CD-reduction effect; lower-is-buff logic wrongly gives BUFF
    "no longer reduces the cooldown": "DEL",   # same, "the cooldown" phrasing
    "cycled out":                   "DEL",     # item removed from the pool
    "moved from tier":              "REWORK",  # tier-change is a structural move, not a buff/nerf
    "dormant curio increases":      "NEW",     # first-ever curio upgrade on an item = new capability
    "destroys the target illusion": "NERF",    # Spectre Reality (7.40): the swapped illusion is lost (audit 2026-10-03)
    # owner 2026-10-16 (7.41 review): the effect decides, not the phrase template
    "when determining if mars is outnumbered": "BUFF",   # Dauntless: allies no longer offset enemies -> regen more often
    "stolen spells now have their cooldown":   "NEW",    # Spell Steal: a new property in place of the debuff amp
    "avatar duration changed from 9/8/7/6s":   "BUFF",   # BKB: the duration now stops at 7s, not 6s
    "lifesteal don't apply to reflected damage": "REWORK",   # how reflected damage works now, not a lost effect
    # owner 2026-10-17 (7.41): where a boss starts changes the game — REWORK, not MISC
    "preference has switched":                 "REWORK",   # Tormentor's spawn / Roshan's pit preference
    "no longer prevents camp-clearing madstone": "MISC",   # Hand of Midas Transmute on a camp's last creep
    "toggling no longer breaks invisibility":  "QoL",      # Radiance Burn: toggling no longer reveals / interrupts
    # owner 2026-10-24 (7.41): what a projectile stops on changes play — REWORK, not MISC
    "treats creep heroes as creeps":           "REWORK",   # Sharpshooter: the arrow now flies through them
}


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
    return 'MISC'


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
# For "from X–Y to A–B" style (en-dash range): take first number of range as the value
_RANGE_FIRST_RE = re.compile(r'^([-+]?\d+(?:\.\d+)?)–')
