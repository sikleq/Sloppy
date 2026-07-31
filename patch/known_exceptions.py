"""known_exceptions.py — shared allowlists for ability/icon audits.

Imported by both audit_abilities.py and check_icons.py so the two scripts
cannot drift. No network/IO side effects at import time — this module is
data-only and safe to import from any audit context.

Maintenance rules (read before adding entries):

- KNOWN_HISTORICAL_RENAMES: 3-tuple (hero, display, content_file). Scope
  to the specific p<version>.py where the historical name is correct.
  Never suppress globally — the same (hero, display) in a current patch
  file is a real bug.

- KNOWN_NON_DATAFEED_ABILITIES: each entry MUST be confirmed against
  data/abilities_slim.json (extracted from npc_dota_hero_<slug>.txt KV
  files, the authoritative source per sloppy_kv_files_authoritative
  memory). A local PNG existing is NOT sufficient evidence — that was
  the circular-validation bug fixed in commit 717694c4.

- KNOWN_DISPLAY_NAME_OVERRIDES: 3-tuple (hero, display_used,
  resolved_slug). For content describing a facet-applied effect on top
  of a base ability, where display intentionally differs from Valve's
  base name_loc.

- KNOWN_ICON_URL_PSEUDO_SLUGS: synthetic pseudo-slugs paired with an
  explicit icon_url= override at the call site. The call supplies its
  own icon and bypasses CDN lookup entirely.

- KNOWN_SYNTHETIC_SUBBLOCKS: visual sub-blocks of a real parent
  ability that do NOT exist as standalone engine slugs. Used as layout
  conventions to render per-element/per-stance bonuses under their own
  heading. Each entry must document the parent engine ability it
  visually decomposes.

- KNOWN_INNATE_NO_CDN_ICON: innates whose engine entry exists
  (abilities_slim.json with is_innate=True) but Valve publishes no
  public CDN icon. Rendered via the elements.py innate-icon fallback
  (data-slug attr + INNATE_ICON_URL), NOT a duplicated PNG file.
  Builders that reference these slugs should emit innate_icon.png
  directly rather than a 404-then-onerror dance.
"""

KNOWN_HISTORICAL_RENAMES = {
    ("Lich", "Death Charge", "p739b.py"),  # renamed to Sacrifice in 7.41
}

KNOWN_NON_DATAFEED_ABILITIES = {
    ("Io", "wisp_essence_conduction"),
    ("Nyx Assassin", "nyx_assassin_nyxth_sense"),
    ("Snapfire", "snapfire_buckshot"),
    ("Venomancer", "venomancer_sepsis"),
    ("Beastmaster", "beastmaster_rugged"),
    ("Clinkz", "clinkz_bone_and_arrow"),
    ("Centaur Warrunner", "centaur_rawhide"),
    ("Night Stalker", "night_stalker_heart_of_darkness"),
    ("Morphling", "morphling_morph_replicate"),
    ("Lina", "lina_combustion"),
    ("Monkey King", "monkey_king_primal_spring"),
    ("Spectre", "spectre_reality"),
    ("Tinker", "tinker_keen_teleport"),
    ("Anti-Mage", "antimage_counterspell_ally"),
    ("Brewmaster", "brewmaster_primal_companion"),
    ("Clinkz", "clinkz_tar_bomb"),
    ("Lone Druid", "lone_druid_spirit_bear_return"),
    ("Lone Druid", "lone_druid_spirit_bear_entangle"),
    ("Oracle", "oracle_diviners_deck"),
    ("Chen", "chen_summon_convert"),        # renamed to Zealot in a later patch; historical in p738c.py
    ("Medusa", "medusa_venomed_volley"),    # old facet-specific ability, not in live herodata
    ("Ringmaster", "ringmaster_crystal_ball"),   # Sideshow Secrets sub-ability, not surfaced in live API
    ("Ringmaster", "ringmaster_weighted_pie"),   # Sideshow Secrets sub-ability, not surfaced in live API
    ("Tinker", "tinker_defense_matrix"),    # not surfaced in live herodata API
    # Familiar's self-cast Stone Form (7.41e). Exists in abilities_slim.json as
    # "Stone Form"; live herodata only lists the Familiars' own entry.
    ("Visage", "visage_stone_form_self_cast"),
}

KNOWN_DISPLAY_NAME_OVERRIDES = {
    ("Slark", "Barracuda", "slark_pounce"),
}

KNOWN_ICON_URL_PSEUDO_SLUGS = {
    "brewmaster_earth_unit", "brewmaster_storm_unit",
    "brewmaster_fire_unit", "brewmaster_void_unit",
}

KNOWN_SYNTHETIC_SUBBLOCKS = {
    # Brewmaster Drunken Brawler per-element stance bonus blocks
    # (parent: brewmaster_drunken_brawler).
    "brewmaster_drunken_brawler_earth",
    "brewmaster_drunken_brawler_fire",
    "brewmaster_drunken_brawler_void",
}

KNOWN_INNATE_NO_CDN_ICON = {
    "queenofpain_succubus",       # Succubus innate
    "terrorblade_dark_unity",     # Dark Unity innate
    "wisp_essence_conduction",    # Io innate — no CDN art
}
