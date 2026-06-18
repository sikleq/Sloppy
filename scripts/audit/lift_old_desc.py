"""lift_old_desc.py — dump historical context for one ability slug.

Workflow:
    python scripts/audit/lift_old_desc.py <ability_slug> [--before <patch>]

Prints (to stdout):
  1. All patchnotes_english.txt deltas for this slug, in chronological order.
  2. Slot location across recent patches (which Ability1..7 slot held the
     slug — useful for spotting promotion to ult / demotion to basic).
  3. A copy-paste-ready skeleton for ability_change(old=..., new=...).

This is a semi-automatic helper for the manual rework-conversion workflow
(memory rule sloppy_innate_rework_pattern): the script gathers all the
historical context needed to compose the OLD pane's desc=[...] list, but
the human still chooses which deltas to surface and how to phrase them.

Why not full automation: the OLD pane describes the ability's PRE-PATCH
tooltip text. patchnotes_english.txt only stores per-patch DELTAS — the
full baseline tooltip lives in Valve's npc_heroes.txt KV which we only
have for the current patch. Walking deltas backwards from current state
is feasible for numeric stats but breaks on behavioral changes ("Now
applies as multi-instance damage" — irreversible). Showing the human
the deltas + slot history is the highest-confidence cheap option.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
STATS = DATA / 'stats'

# Patch chronology — match RELEASE_HISTORY order in patch/meta.py.
# Loaded lazily from stats/ subdirs.
def _patch_chronology():
    return sorted([p.name for p in STATS.iterdir() if p.is_dir()],
                  key=lambda v: tuple(int(x) if x.isdigit() else (-1, x)
                                       for x in re.split(r'(\d+)', v) if x))


_PATCH_LINE_RE = re.compile(
    r'"DOTA_Patch_(?P<patch>[0-9_a-z]+?)_'
    r'(?P<sub>[a-z_]*?)(?P<slug>[a-z_]+?)(?:_\d+)?"\s+"(?P<note>[^"]+)"'
)


def _normalize_patch(s):
    """7_06d → 7.06d, 7_41c → 7.41c."""
    return s.replace('_', '.', 1)


_PATCH_PREFIX_RE = re.compile(r'^(\d+(?:_\d+)+[a-z]?)_')


def _split_patch_prefix(key_suffix):
    """Pull `<patch>_<rest>` off the start of a `DOTA_Patch_*` key tail."""
    m = _PATCH_PREFIX_RE.match(key_suffix)
    if not m:
        return None, key_suffix
    return _normalize_patch(m.group(1)), key_suffix[m.end():]


def _index_patchnotes(slug, also_search_text=False):
    """Return list of (patch, key, note) tuples mentioning the slug.
    patchnotes_english.txt keys come in forms like:
      DOTA_Patch_7_40_lone_druid_lone_druid_entangle
      DOTA_Patch_7_40_druid_bear1_lone_druid_spirit_bear_entangle
      DOTA_Patch_7_30c_npc_dota_neutral_<...>
    so the unit/hero prefix is variable. Match slug as substring anywhere
    in the key after the patch prefix.

    If also_search_text=True, also pull entries whose NOTE body mentions
    the slug's display fragment — catches renames like
    `lone_druid_spirit_bear_entangling_claws` → `lone_druid_spirit_bear_entangle`.
    """
    text = (DATA / 'patchnotes_english.txt').read_text(encoding='utf-8')
    rx = re.compile(r'"DOTA_Patch_([^"]+)"\s+"([^"]+)"')
    out = []
    for m in rx.finditer(text):
        key_tail = m.group(1)
        note = m.group(2)
        patch, rest = _split_patch_prefix(key_tail)
        if not patch:
            continue
        if slug in rest:
            out.append((patch, rest, note))
            continue
        if also_search_text and any(tok in note for tok in [slug, slug.replace('_', ' ')]):
            out.append((patch, rest, note))
    try:
        chronology = _patch_chronology()
        order = {p: i for i, p in enumerate(chronology)}
        out.sort(key=lambda x: order.get(x[0], 1_000_000))
    except Exception:
        pass
    return out


def _find_related_slugs(slug, hero_prefix=None):
    """Look for sibling slugs that share a fragment with `slug` — often the
    pre-rework slug that got renamed. Returns ordered list of candidates."""
    text = (DATA / 'patchnotes_english.txt').read_text(encoding='utf-8')
    # Extract slug fragments
    tokens = [t for t in slug.split('_') if len(t) > 3]
    rx = re.compile(r'"DOTA_Patch_[^"]+"\s*"[^"]*"')
    seen = {}
    key_rx = re.compile(r'"DOTA_Patch_([^"]+)"')
    for m in key_rx.finditer(text):
        key_tail = m.group(1)
        _, rest = _split_patch_prefix(key_tail)
        # Strip trailing _N index
        bare = re.sub(r'_\d+$', '', rest)
        if any(tok in bare for tok in tokens):
            seen[bare] = seen.get(bare, 0) + 1
    related = sorted(seen.items(), key=lambda x: -x[1])
    return [s for s, _ in related if s != slug][:10]


def _slot_history(slug):
    """For each patch we have heroes.json for, return which hero+slot held
    the slug. Tracks promotion (basic → ult), reshuffles, removal."""
    history = []
    for patch_dir in sorted(STATS.iterdir(), key=lambda p: p.name):
        if not patch_dir.is_dir():
            continue
        hp = patch_dir / 'heroes.json'
        if not hp.exists():
            continue
        try:
            d = json.loads(hp.read_text(encoding='utf-8'))
        except Exception:
            continue
        for hero_key, hero_data in d.items():
            if not isinstance(hero_data, dict):
                continue
            for slot_key, slot_val in hero_data.items():
                if slot_key.startswith('Ability') and slot_val == slug:
                    history.append((patch_dir.name, hero_key, slot_key))
                    break
    return history


def _summarize_slot_history(rows):
    """Collapse consecutive identical (hero, slot) rows into ranges."""
    if not rows:
        return []
    out = []
    cur = rows[0]
    span_start = cur[0]
    for r in rows[1:]:
        if r[1:] == cur[1:]:
            continue
        out.append((span_start, cur[0], cur[1], cur[2]))
        cur = r
        span_start = r[0]
    out.append((span_start, rows[-1][0], cur[1], cur[2]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('slug', help='Engine slug, e.g. lone_druid_spirit_bear_entangle')
    ap.add_argument('--before', metavar='PATCH',
                    help='Only show deltas with patch < PATCH (e.g. 7.40)')
    ap.add_argument('--display', help='Display name for the skeleton (e.g. "Entangling Claws")')
    args = ap.parse_args()

    slug = args.slug
    deltas = _index_patchnotes(slug)
    if args.before:
        chronology = _patch_chronology()
        order = {p: i for i, p in enumerate(chronology)}
        cutoff = order.get(args.before, 1_000_000)
        deltas = [(p, k, n) for (p, k, n) in deltas if order.get(p, 1_000_000) < cutoff]

    print(f"# Historical context for ability `{slug}`")
    if args.before:
        print(f"# Showing deltas BEFORE patch {args.before}")
    print(f"# Total deltas found: {len(deltas)}")
    print()
    print("# ---- DELTAS (chronological) ----")
    for patch, key, note in deltas:
        print(f"  [{patch:7s}]  {note}")

    # If we found nothing, suggest related slugs (likely pre-rename names).
    if not deltas:
        related = _find_related_slugs(slug)
        if related:
            print()
            print("# ---- NO DIRECT HISTORY — related slugs (likely pre-rename) ----")
            for r in related:
                print(f"  {r}")
            print(f"\n  Re-run with one of these: python scripts/audit/lift_old_desc.py <slug> --before {args.before or '<patch>'}")

    print()
    print("# ---- SLOT HISTORY (hero + Ability slot per patch range) ----")
    sh = _slot_history(slug)
    for span_start, span_end, hero, slot in _summarize_slot_history(sh):
        # Trim 'npc_dota_hero_' prefix for readability
        h = hero.replace('npc_dota_hero_', '')
        if span_start == span_end:
            print(f"  {span_start}:                {h}.{slot}")
        else:
            print(f"  {span_start} .. {span_end}: {h}.{slot}")

    print()
    print("# ---- ability_change SKELETON (copy + fill) ----")
    display = args.display or slug.split('_')[-1].title()
    last_two = deltas[-2:] if len(deltas) >= 2 else deltas
    seed_lines = ',\n        '.join(
        f't("MISC")("{n.replace(chr(34), chr(92)+chr(34))}")' for _, _, n in last_two
    )
    print(f"""W(ability_change(
    old=dict(
        name="{display}",
        slug="{slug}",
        desc=[
            # TODO: replace with pre-{args.before or '<patch>'} tooltip text.
            # Last {len(last_two)} delta(s) before the rework (seed):
            {seed_lines or 't("MISC")("Pre-rework form here")'},
        ],
    ),
    new=dict(
        name="{display}",
        slug="{slug}",
        desc=[
            # TODO: paste new-side rows from this patch's existing W(li(...))
            # block above; convert t("REWORK") → t("MISC") inside desc list.
        ],
    ),
    summary="Ability reworked.",
    tag="rework",
))""")


if __name__ == '__main__':
    main()
