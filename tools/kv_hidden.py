"""kv_hidden.py — every change in the game files that the patch page does not write, three more parts of kv_review.

kv_review's part 3 only looked at abilities the page names and dropped an ability as soon as one row of it was a word
row; the 7.41 check (owner 2026-11-21: "пойми, почему ты эти изменения не нашёл, улучши себя") missed Viper Strike's
cast range (no row of the ability at all), Kinetic Fence's mana, Reactive Tazer's damage, Guardian Angel's dispel
(each next to a word row), items and units (data/stats before 7.41c keeps only heroes/), and every change Liquipedia
marks undocumented. Here:

  4. Every hero ability of both patches: a changed value whose numbers the hero's block on the page does not write.
  5. Hero stats, items.txt, npc_units.txt, npc_abilities.txt (the game-files store when data/stats lacks them): the same
     against the entity's block.
  6. Liquipedia's undocumented lines ({{cf|U}}, {{Undocumented}}) for the version, from the local cache
     (tools/liquipedia_cache.py), with whether the page writes their numbers.

Left out as not a game change: aspect (facet) keys, tooltip / display keys, a list cut to fewer levels (levels no one
reaches), a value only moved to another key, a new key of 0, a talent value of a talent the hero does not have, a
recipe's parts in another order, an entity added or removed whole (the page has its block or the removal).
What is left is a list of candidates: a person checks each in the game, a draft or a bug fix is not a hidden change
(docs/agent-rules/patch-tags.md). Print, do not commit the output.
"""
import gzip
import json
import re
import subprocess
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_NUM = re.compile(r"-?\d+(?:\.\d+)?")
_NOISE_KEY = re.compile(r"facet|display_type|tooltip|AbilityDraft|dynamic_value|DependentOnAbility|"
                        r"TooltipSummary|RequiresShard|RequiresScepter|LinkedSpecialBonus|apply_curio_bonus|"
                        r"affected_by_aoe_increase|DamageTypeTooltip|CalculateSpellDamageTooltip", re.I)
_HEADER = re.compile(r'W\((?:hero|item|unit|plain|enchant)_header\(\s*"([^"]+)"')
_LP_MARK = re.compile(r"\{\{cf\|[Uu]\}\}|\{\{[Uu]ndocumented[^}]*\}\}")
_LP_SKIP = re.compile(r"shop category|icon", re.I)


def nums(v):
    return [abs(float(x)) for x in _NUM.findall(str(v))] if v is not None else []


def truncated(old, new):
    """"80 160 240 320 400" → "80 160 240 320": a level no one reaches dropped (7.41 Night Stalker, Invoker)."""
    o, n = nums(old), nums(new)
    return bool(n) and len(n) < len(o) and o[:len(n)] == n


def page_blocks(version):
    """{header name (lower): the block's source text} of content/p<v>.py — every line up to the next header."""
    path = ROOT / "content" / f"p{version.replace('.', '')}.py"
    if not path.exists():
        return {}
    src = path.read_text(encoding="utf-8")
    marks = list(_HEADER.finditer(src))
    out = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(src)
        out[m.group(1).lower()] = out.get(m.group(1).lower(), "") + src[m.start():end]
    return out


# how an ability shows in the UI, not what it does (7.41: every innate got FORCE_NO_INNATE_UI / HIDDEN)
_UI_FLAGS = {"HIDDEN", "INNATE_UI", "FORCE_NO_INNATE_UI", "SKIP_FOR_KEYBINDS", "SHOW_IN_GUIDES", "FORCE_KEYBIND",
             "NOT_LEARNABLE", "DONT_RESUME_ATTACK", "DONT_RESUME_MOVEMENT", "DIRECT_KEYBIND", "HAS_DETAILS_UI"}
# a behaviour flag the page says in words (7.41e "Toggling on/off no longer breaks invisibility and can be done while
# silenced", "Can now be interrupted by root")
_FLAG_WORDS = {"IGNORE_INVISIBLE": r"invisib", "IGNORE_SILENCE": r"silence", "ROOT_DISABLES": r"\broot",
               "IMMEDIATE": r"instant|cast point|movement", "ALT_CASTABLE": r"alt[- ]cast", "AUTOCAST": r"autocast",
               "VECTOR_TARGETING": r"vector", "AOE": r"\bAoE\b|radius|area", "TOGGLE": r"toggl"}


def _flags(v):
    return {x.strip().replace("DOTA_ABILITY_BEHAVIOR_", "") for x in str(v or "").split("|") if x.strip()}


def _noise(f, o, n, block):
    """A change that is no game change (the module doc's list)."""
    leaf = f.rsplit(".", 1)[-1]
    if _NOISE_KEY.search(f) or truncated(o, n) or truncated(n, o):
        return True                                    # a level cut or added past the max (Invoker's orbs 7 → 8)
    if re.fullmatch(r"Ability\d+", f):
        return True                                    # a hero's ability / talent slots: their rows say the swap
    if leaf == "AbilityBehavior" or f == "AbilityBehavior":
        moved = (_flags(o) ^ _flags(n)) - _UI_FLAGS
        return all(re.search(_FLAG_WORDS.get(x, r"(?!)"), block, re.I) for x in moved)
    if f.lower() == "maxlevel" and ("1" in (str(o).strip(), str(n).strip()) or None in (o, n)):
        return True                                    # an ability turned innate or back: its own row says so
    if f in ("HasShardUpgrade", "HasScepterUpgrade", "IsGrantedByShard", "IsGrantedByScepter") and re.search(
            r"Aghanim's (?:Shard|Scepter)", block):
        return True                                    # the block's Shard / Scepter rows say it in words
    if n is None and not any(nums(o)):
        return True                                    # a key of 0 or "" removed
    if o is None and not any(nums(n)) and not re.search(r"[A-Za-z]", str(n or "")):
        return True                                    # a new key of 0: a placeholder
    for kind in ("shard", "scepter"):                  # "No longer upgraded with Aghanim's Shard" says the rest
        if f"special_bonus_{kind}" in f and n is None and re.search(
                rf"No longer (?:upgraded|granted) (?:with|by) Aghanim's {kind}", block, re.I):
            return True
    return False


def uncovered(fields, block, talents=None):
    """{field: (old, new)} the page block does not write: what is left after the rules of the module doc.
    `talents`: the hero's talent names (both patches) — a talent value of another talent is a dead reference."""
    have = set(nums(block))
    out = {}
    for f, (o, n) in fields.items():
        if _noise(f, o, n, block):
            continue
        if o is not None and n is not None and set(nums(o)) == set(nums(n)) and nums(o):
            continue                                   # "0" → "0 0 0", "5.0" → "5"
        t = re.search(r"(special_bonus_\w+)", f)
        if t and talents is not None and t.group(1) not in talents and "shard" not in t.group(1) \
                and "scepter" not in t.group(1):
            continue                                   # 7.41d Brewmaster: a talent the tree does not have
        if o is None and nums(n) and not any(nums(n)):
            continue                                   # a new key of 0: a placeholder
        if f.startswith("ItemRequirements") and "components" in block:
            continue                                   # the parts: the page's components card
        if _written(o, n, have):
            continue
        out[f] = (o, n)
    return out


def _written(o, n, have):
    """The page writes the change: its new numbers, the old ones of a value gone to 0 ("No longer provides +7
    Intelligence"), or the step of one number ("Base Damage increased by 3")."""
    new, old = nums(n), nums(o)
    if new and any(new) and set(new) <= have:
        return True
    if (not new or not any(new)) and old and set(old) <= have:
        return True
    if len(new) == 1 and len(old) == 1 and round(abs(new[0] - old[0]), 4) in have:
        return True
    return False


def entity_block(blocks, name):
    """The entity's own block, else every block that names it (a summon under its hero: Razorback under Beastmaster,
    a neutral's ability under its creep: Chain Lightning under Harpy Stormcrafter)."""
    own = blocks.get(name.lower())
    if own:
        return own
    low = name.lower()
    return "\n".join(b for b in blocks.values() if low in b.lower())


@lru_cache(maxsize=1)
def _names():
    heroes, items = {}, {}
    try:
        heroes = {h["name"]: h["name_english_loc"] for h in json.loads(
            (ROOT / "data" / "herolist.json").read_text(encoding="utf-8"))["result"]["data"]["heroes"]}
        items = {i["name"]: i["name_english_loc"] for i in json.loads(
            (ROOT / "data" / "itemlist.json").read_text(encoding="utf-8"))["result"]["data"]["itemabilities"]}
    except (OSError, KeyError, ValueError):
        pass
    return heroes, items


def display(kind, ent):
    heroes, items = _names()
    if kind == "hero" or ent.startswith("npc_dota_hero_"):
        return heroes.get(ent, ent)
    if kind == "item":
        return items.get(ent.replace("item_recipe_", "item_")) or items.get(ent) or ent
    try:
        from builders.silent import _entity_display
        return re.sub(r"<[^>]+>", "", str(_entity_display(kind, ent)))
    except Exception:                                  # a name is a convenience, the slug still says it
        return ent


def _talents(stats):
    return {v for k, v in stats.items() if re.fullmatch(r"Ability\d+", k) and str(v).startswith("special_bonus")}


def abilities_part(version, prev, curr_kv, prev_kv, diff, blocks, hero_stats):
    """Part 4: [(hero, ability, {field: (old, new)})]."""
    out = []
    for hero_key, abilities in sorted(diff.items()):
        name = display("hero", hero_key)
        block = blocks.get(name.lower(), "")
        talents = _talents(hero_stats[0].get(hero_key, {})) | _talents(hero_stats[1].get(hero_key, {}))
        for slug, fields in sorted(abilities.items()):
            if slug not in prev_kv.get(hero_key, {}) or slug not in curr_kv.get(hero_key, {}) or slug.endswith("_ad"):
                continue                               # a new or removed ability: its own block / row; *_ad: Ability Draft
            left = uncovered(_moved(fields), block, talents or None)
            if left:
                out.append((name, slug, left))
    return out


def _moved(fields):
    """A value only moved between "AbilityCooldown" and "AbilityValues.AbilityCooldown.value" is no change."""
    def canon(f):
        f = f[len("AbilityValues."):] if f.startswith("AbilityValues.") else f
        f = f[:-len(".value")] if f.endswith(".value") else f
        return "MaxLevel" if f.lower() == "max_level" else f       # Lycan 7.41: max_level → MaxLevel
    olds, news = {}, {}
    for f, (o, n) in fields.items():
        if o is not None:
            olds.setdefault(canon(f), o)
        if n is not None:
            news.setdefault(canon(f), n)
    return {k: (olds.get(k), news.get(k)) for k in set(olds) | set(news) if olds.get(k) != news.get(k)}


def _store_root(version, name):
    """A root KV file of data/stats/<v>/, else of the game-files store (patch/game_files.py)."""
    from builders.silent import DATA_DIR, _SKIP_TOP_KEYS, _decode_bytes, _flatten, parse_kv
    path = DATA_DIR / version / name
    raw = path.read_bytes() if path.exists() else None
    if raw is None:
        from patch import game_files
        raw = game_files.read_bytes(version, f"scripts/npc/{name}") if game_files.available() else None
    if raw is None:
        return None
    kv = parse_kv(_decode_bytes(raw))
    if name == "npc_heroes.txt":
        from builders.silent import _hero_blocks
        return _hero_blocks(kv)
    root = next(iter(kv.values()), {}) if kv else {}
    return {k: _flatten(v) for k, v in root.items() if isinstance(v, dict) and k not in _SKIP_TOP_KEYS}


def hero_stats(version):
    from builders.silent import load_hero_stats
    return load_hero_stats(version) or _store_root(version, "npc_heroes.txt") or {}


def root_part(version, prev, blocks, stats):
    """Part 5: [(section, name, slug, {field: (old, new)})] and the files neither patch has."""
    from builders.silent import ROOT_FILES, _FILTERS, _interesting_hero, _same_number, diff_versions
    out, missing = [], []
    files = [("Hero stats", "hero", stats[0], stats[1], _interesting_hero)]
    for name, title, kind in ROOT_FILES:
        a, b = _store_root(prev, name), _store_root(version, name)
        if not a or not b:
            missing.append(name)
            continue
        files.append((title, kind, a, b, _FILTERS[kind]))
    for title, kind, a, b, interesting in files:
        if not a or not b:
            continue
        d = diff_versions({title: a}, {title: b}, interesting).get(title) or {}
        for ent, fields in sorted(d.items()):
            olds, news = [v[0] for v in fields.values()], [v[1] for v in fields.values()]
            if all(o is None for o in olds) or all(n is None for n in news):
                continue
            fields = {f: v for f, v in fields.items() if not _same_number(*v) and not (
                f.startswith("ItemRequirements") and sorted(filter(None, str(v[0]).split(";")))
                == sorted(filter(None, str(v[1]).split(";"))))}
            name = display(kind, ent)
            left = uncovered(_moved(fields), entity_block(blocks, name))
            if left:
                out.append((title, name, ent, left))
    return out, missing


def _lp_dir():
    try:
        import tools.liquipedia_cache as lc
        here = Path(lc.ROOT) / "wikitext"
    except Exception:
        here = ROOT / "outputs" / "liquipedia" / "wikitext"
    if here.exists():
        return here
    try:                                               # a worktree: the cache sits in the main checkout
        common = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--git-common-dir"],
                                capture_output=True, text=True, check=True).stdout.strip()
        main = Path(common).resolve().parent / "outputs" / "liquipedia" / "wikitext"
        return main if main.exists() else None
    except (OSError, subprocess.CalledProcessError):
        return None


def _lp_clean(s):
    s = re.sub(r"\{\{A\|[^|}]*\|([^}]*)\}\}", r"\1", s)
    s = re.sub(r"\{\{(?:H|M|I|Code)\|([^}|]*)[^}]*\}\}", r"\1", s)
    s = re.sub(r"\{\{Symbol\|[^}]*\}\}", "", s)
    s = re.sub(r"\[\[(?:[^]|]*\|)?([^]]*)\]\]", r"\1", s)
    s = re.sub(r"\{\{cf\|([^}]*)\}\}", r"[\1]", s)
    return re.sub(r"\s+", " ", s).strip(" *")


def _lp_versions(text):
    for m in re.finditer(r"\{\{VersionTableElement\|([^|]+)\|", text):
        depth, i = 1, m.end()
        while i < len(text) and depth:
            if text.startswith("{{", i):
                depth, i = depth + 1, i + 2
            elif text.startswith("}}", i):
                depth, i = depth - 1, i + 2
            else:
                i += 1
        yield m.group(1).strip(), text[m.end():i - 2]


def lp_lines(version, lp_dir=None):
    """[(page, text)] of Liquipedia's undocumented lines for the version (a marked line + the lines under it)."""
    lp_dir = lp_dir or _lp_dir()
    if not lp_dir:
        return None
    out = []
    for f in sorted(Path(lp_dir).glob("*_Changelogs.txt.gz")):
        page = f.name[:-len("_Changelogs.txt.gz")].replace("_", " ")
        for ver, body in _lp_versions(gzip.open(f, "rt", encoding="utf-8").read()):
            if ver != version:
                continue
            lines = body.splitlines()
            for i, ln in enumerate(lines):
                if not _LP_MARK.search(ln) or _LP_SKIP.search(ln):
                    continue
                depth = len(ln) - len(ln.lstrip("*"))
                parts = [_lp_clean(ln)]
                for nx in lines[i + 1:]:
                    if len(nx) - len(nx.lstrip("*")) <= depth:
                        break
                    parts.append(_lp_clean(nx))
                out.append((page, " / ".join(p for p in parts if p)))
    return out


def report_parts(version, prev):
    from builders.silent import diff_versions, load_hero_abilities
    blocks = page_blocks(version)
    curr_kv, prev_kv = load_hero_abilities(version), load_hero_abilities(prev)
    stats = (hero_stats(prev), hero_stats(version))
    show = lambda v: "—" if v is None else str(v).strip()  # noqa: E731
    fields = lambda fs: "; ".join(f"{f}: {show(o)} → {show(n)}" for f, (o, n) in sorted(fs.items()))  # noqa: E731
    out = []
    part4 = abilities_part(version, prev, curr_kv, prev_kv, diff_versions(prev_kv, curr_kv), blocks, stats)
    out += ["", f"## 4. Способности героев: изменения, чьих чисел нет в блоке героя на странице: {len(part4)}"]
    out += [f"- {h} / {s}: {fields(f)}" for h, s, f in part4] or ["- нет"]
    part5, missing = root_part(version, prev, blocks, stats)
    out += ["", f"## 5. Характеристики, предметы, юниты: изменения, чьих чисел нет в их блоке: {len(part5)}"]
    if missing:
        out.append(f"- (нет файлов: {', '.join(missing)} — ни в data/stats, ни в хранилище)")
    out += [f"- [{t}] {n} ({e}): {fields(f)}" for t, n, e, f in part5] or ["- нет"]
    lp = lp_lines(version)
    out += ["", "## 6. Liquipedia: строки с отметкой «нет в заметках» "
            + ("(кэша нет: python tools/liquipedia_cache.py sync heroes items)" if lp is None else f"{len(lp)}")]
    for page, text in lp or []:
        block = blocks.get(page.lower(), "")
        want = set(nums(text))
        mark = "на странице: числа есть" if want and want <= set(nums(block)) else (
            "героя/предмета нет на странице" if not block else "проверить")
        out.append(f"- {page}: {text[:300]} [{mark}]")
    return out
