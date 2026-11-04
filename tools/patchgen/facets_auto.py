"""New facet slugs of a patch, written into patch/badges.py."""
import os

from .common import _HERE
from .data import HEROES

def _auto_register_facets(version, datafeed):
    """Add any missing facet slugs from datafeed into patch/badges.py FACETS dict.

    Reads the datafeed for facet subsections, checks each slug against the
    current FACETS dict, and appends missing entries at the end of the FACETS
    block in badges.py.
    """
    from patch.badges import FACETS
    badges_path = os.path.join(_HERE, 'patch', 'badges.py')

    from patch.ability_kv import hero_facets
    missing = {}
    for hero in datafeed.get('heroes', []):
        hero_slug = HEROES.get(hero.get('hero_id'), ('', ''))[1]
        for s in hero.get('subsections', []):
            if s.get('style', '').startswith('hero_facet'):
                slug = s.get('facet', '')
                if slug and slug not in FACETS and slug not in missing:
                    # the game files of the patch first: Valve's web feed had Convergence "Yellow0", npc_heroes.txt
                    # Yellow + GradientID 1 in every 7.37 build (2026-10-29)
                    game = hero_facets(hero_slug, version).get(slug) if hero_slug else None
                    missing[slug] = (game[0] or s.get('title', slug), game[1]) if game else \
                        (s.get('title', slug), s.get('facet_color', 'Gray3'))

    if not missing:
        return

    src = open(badges_path, encoding='utf-8').read()
    # Find the closing brace of the FACETS dict specifically.
    # FACETS is followed by the _FACET_COLOR_GRADIENT comment block, so we
    # search for "}\n\n# Mapping from Valve" which is unique to the FACETS end.
    import re as _re
    facets_end = _re.search(r'\n}\n\n# Mapping from Valve', src)
    if not facets_end:
        print('[WARN] Could not auto-register facets — could not locate FACETS closing brace')
        return
    last_brace_idx = facets_end.start()

    new_lines = [f'    # {version} — auto-registered by generate_patch_code_v2.py']
    for slug, (title, color) in missing.items():
        new_lines.append(f'    "{slug}": ("{title}", "{color}"),')
        print(f'[INFO] Auto-registered facet: "{slug}": ("{title}", "{color}")')

    insertion = '\n'.join(new_lines)
    new_src = src[:last_brace_idx] + '\n' + insertion + src[last_brace_idx:]
    open(badges_path, 'w', encoding='utf-8').write(new_src)
    print(f'[INFO] Updated patch/badges.py with {len(missing)} new facet(s)')
