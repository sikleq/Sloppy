"""kv_review.py — check a patch page's rows against the game files of the patch before (owner 2026-10-30: "научить
генератор подобные предложения проверять и сравнивать с другими версиями"; a report first, no page edits).

For every hero ability the page names, the ability's KV of the patch before and of this patch are compared
(builders/silent.py's diff, the one the hidden-changes page uses). The report has three parts:

  1. Valve's "from" that the game did not have — scripts/audit/audit_from_values.py (a row not yet marked wrong-word).
  2. Word rows (no "from … to") and what changed in their ability's files — the facts for the "?" of the row; a row
     whose tag the files may contradict is marked "проверить тег" (the 7.37d Leech Seed case: "Now heals creeps for
     50% effectiveness" was tagged NEW, the files show a new creep heal reduction → a cut).
  3. Changes in the files of those abilities that no row of the page explains — this hero's hidden changes.

The meaning stays with a person: the files say "0 → 50", not whether that is a nerf.

    python tools/kv_review.py 7.37d [7.37c …]
Needs the site built (part 1 reads dist/patches/<v>.html) and data/normalized/patches/<v>.json (the generator).
Hidden findings are not for the public repo — print, do not commit the output.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from builders.silent import diff_versions, load_hero_abilities  # noqa: E402
from patch.ability_kv import hero_abilities  # noqa: E402
from patch.meta import _prev_patch_version  # noqa: E402

NORM = ROOT / "data" / "normalized" / "patches"
_NUM = re.compile(r"-?\d+(?:\.\d+)?")
_PREFIX = re.compile(r"^([^:]{2,40}):\s+")
# a new key whose name says it takes something away: a row that calls it NEW / BUFF / MISC may be a cut
_CUT_KEY = re.compile(r"reduction|penalty|reduce|loss|lost", re.I)
_GOOD_TAGS = {"new", "buff", "misc", "qol"}
# a value's flags, not a value: how the tooltip shows it, what scales it
_META = {"affected_by_aoe_increase", "DamageTypeTooltip", "CalculateSpellDamageTooltip", "RequiresFacet",
         "LinkedSpecialBonus", "RequiresScepter", "RequiresShard", "CalculateAttackDamageTooltip"}


def _nums(v):
    """Numbers of a KV value or a row's old/new: "15 30 45 60" / "=9 =11" / 12 / [1, 2] → [15.0, 30.0, …]."""
    if v is None:
        return []
    if isinstance(v, (int, float)):
        return [float(v)]
    if isinstance(v, (list, tuple)):
        return [float(x) for x in v if isinstance(x, (int, float))]
    return [float(x) for x in _NUM.findall(str(v))]


def _canon(field):
    """One name for a value wherever the file keeps it: "AbilityCooldown" = "AbilityValues.AbilityCooldown.value"
    (7.37e Escape Act moved its cooldown into AbilityValues — not a change)."""
    f = field[len("AbilityValues."):] if field.startswith("AbilityValues.") else field
    return f[:-len(".value")] if f.endswith(".value") else f


def _merge_moves(fields):
    """{field: (old, new)} with a value that only moved between paths dropped, the rest keyed by its canonical name."""
    olds, news = {}, {}
    for f, (o, n) in fields.items():
        if o is not None:
            olds.setdefault(_canon(f), o)
        if n is not None:
            news.setdefault(_canon(f), n)
    out = {}
    for key in sorted(set(olds) | set(news)):
        o, n = olds.get(key), news.get(key)
        no, nn = _nums(o), _nums(n)
        if no and nn and set(no) == set(nn) and len(set(no)) == 1:
            continue                                # "0" → "0 0 0": the same value written per level
        if o != n and no != nn or (o is None) != (n is None):
            out[key] = (o, n)
    return out


def _in_text(field_old, field_new, rows):
    """A KV change whose numbers a row writes in its text (7.37b a talent swap "… replaced with +25 Counter Helix
    Damage", 7.37e "Eidolon gold bounty increased from 14-20 to 17-20"); signs aside (a penalty -60 is "60%")."""
    new, old = [abs(x) for x in _nums(field_new)], [abs(x) for x in _nums(field_old)]
    if not new or not any(new):
        return False
    for r in rows:
        nums = {abs(x) for x in _nums(" ".join(_NUM.findall(r.get("text", ""))))}
        if set(new) <= nums and (not old or set(old) <= nums or r.get("tag") == "swap"):
            return True
    return False


def _ratio(a, b):
    """The one factor b = k·a for every element (a per-tick value vs Valve's per second, 7.37d Ink Tendrils), or None."""
    if not a or len(a) != len(b) or any(x == 0 for x in a):
        return None
    ks = {round(y / x, 6) for x, y in zip(a, b)}
    return ks.pop() if len(ks) == 1 else None


def _same(a, b):
    return bool(a) and len(a) == len(b) and all(abs(x - y) < 1e-6 for x, y in zip(a, b))


def _covered(field_old, field_new, rows, base=None):
    """A KV change a numeric row of the page states: its new values or its old ones, the same values in another unit
    (one factor for old and new: per tick vs per second), or a facet/talent's "+x" on the ability's base value
    (7.37d Rolling Thunder Thunderbolt "-2 → -1" on 10 = the row's 8s → 9s)."""
    new, old = _nums(field_new), _nums(field_old)
    candidates = [(old, new)]
    if base and str(field_new or "").lstrip()[:1] in "+-" and str(field_old or "").lstrip()[:1] in "+-":
        candidates.append(([base[0] + x for x in old], [base[0] + x for x in new]))
    for o, n in candidates:
        for r in rows:
            rn, ro = _nums(r.get("new")), _nums(r.get("old"))
            if rn and (_same(n, rn) or (len(set(rn)) == 1 and set(n) == set(rn)) or (len(rn) == 1 and rn[0] in n)):
                return True
            if ro and _same(o, ro):
                return True
            k_new, k_old = _ratio(n, rn), _ratio(o, ro)
            if k_new is not None and k_new == k_old:
                return True
    return False


def _ability_of(hero, change, version, hero_diff):
    """The ability slug a row is about: its scope (an ability's name), the "Ability:" prefix of a facet row, or the
    one ability whose files name the facet (7.37d Luna Moonstorm "Damage Buff per beam …" → Lucent Beam)."""
    names = hero_abilities(hero, version)
    scope = change.get("scope") or ""
    if scope.startswith("facet:") and not _PREFIX.match(change.get("text", "")):
        facet = scope.split(":", 1)[1]
        hits = [a for a, fields in hero_diff.items() if any(f"special_bonus_facet_{facet}" in f for f in fields)]
        if len(hits) == 1:
            return hits[0]
        from patch.ability_kv import facet_ability
        return facet_ability(facet, version)
    if scope and not scope.startswith("facet:") and scope not in ("base", "talent", "talents"):
        hit = names.get(scope.lower())
        if hit:
            return hit[0]
    m = _PREFIX.match(change.get("text", ""))
    if m:
        hit = names.get(m.group(1).strip().lower())
        if hit:
            return hit[0]
    return None


def _show(v):
    return "—" if v is None else str(v).strip()


_PAGE_ROW = re.compile(r"""W\(li\((["'])(.*?)\1,\s*t\("([A-Za-z]+)"\)""")


def _page_tags(version):
    """{row text: tag} of the page itself (content/p<v>.py) — the owner's review is there; the normalized JSON keeps
    the generator's first guess (7.37d Leech Seed NEW there, NERF on the page)."""
    path = ROOT / "content" / f"p{version.replace('.', '')}.py"
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    return {re.sub(r"<[^>]+>", "", m.group(2)): m.group(3).lower() for m in _PAGE_ROW.finditer(text)}


def review(version):
    prev = _prev_patch_version(version)
    doc = json.loads((NORM / f"{version}.json").read_text(encoding="utf-8"))
    tags = _page_tags(version)
    for ent in doc.get("entities", []):
        for ch in ent.get("changes", []):
            text = ch.get("text", "")
            ch["tag"] = tags.get(text) or tags.get(_PREFIX.sub("", text)) or ch.get("tag", "")
    curr_kv, prev_kv = load_hero_abilities(version), load_hero_abilities(prev)
    diff = diff_versions(prev_kv, curr_kv)
    words, hidden, checks = [], [], 0
    for ent in doc.get("entities", []):
        if ent.get("entity_type") != "hero":
            continue
        hero = ent["id"]
        key = f"npc_dota_hero_{hero}"
        hero_diff = diff.get(key, diff.get(hero, {}))
        hero_kv = curr_kv.get(key, curr_kv.get(hero, {}))
        by_ability = {}
        for ch in ent.get("changes", []):
            slug = _ability_of(hero, ch, version, hero_diff)
            if slug:
                by_ability.setdefault(slug, []).append(ch)
        # every numeric row of the hero: a talent's value sits in its ability's file (7.37d Sand Storm DPS talent)
        hero_numeric = [r for r in ent.get("changes", []) if "old" in r or "new" in r]
        for slug, rows in by_ability.items():
            fields = _merge_moves({f: ov for f, ov in hero_diff.get(slug, {}).items()
                                   if f.rsplit(".", 1)[-1] not in _META})
            numeric = [r for r in rows if "old" in r or "new" in r]
            abil_kv = hero_kv.get(slug, {})

            def base(field):
                stem = field.split(".special_bonus", 1)[0]
                return _nums(abil_kv.get(f"AbilityValues.{stem}.value") or abil_kv.get(f"AbilityValues.{stem}")
                             or abil_kv.get(stem))
            # a new ability (a new hero: Ringmaster 7.37c, Kez 7.37e) — no hidden change, and no file list for its rows
            is_new = slug not in (prev_kv.get(key) or prev_kv.get(hero) or {})
            # a word row shows every change no "from … to" row states; the hidden list also drops what a row's text
            # writes (a talent swap) — for a word row that text is exactly what the files should back up
            open_fields = {f: ov for f, ov in fields.items() if not _covered(ov[0], ov[1], hero_numeric, base(f))}
            unstated = {f: ov for f, ov in open_fields.items() if not _in_text(ov[0], ov[1], ent.get("changes", []))}
            for r in rows:
                if r in numeric or r.get("tag") in ("swap",):
                    continue
                flag = ""
                if not is_new and r.get("tag") in _GOOD_TAGS and any(
                        old is None and _CUT_KEY.search(f) for f, (old, _n) in open_fields.items()):
                    flag, checks = "проверить тег", checks + 1
                words.append((ent["name"], slug, r, {} if is_new else open_fields, flag))
            if unstated and not is_new and not any(r not in numeric for r in rows):
                hidden.append((ent["name"], slug, unstated))
    wrong = []
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("afv", ROOT / "scripts" / "audit" / "audit_from_values.py")
        afv = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(afv)
        wrong = afv.audit_page(version, prev)
    except FileNotFoundError:
        pass
    return prev, wrong, words, hidden, checks


def _fields(fields):
    return "; ".join(f"{f}: {_show(o)} → {_show(n)}" for f, (o, n) in sorted(fields.items())) or "в файлах без изменений"


def report(version):
    prev, wrong, words, hidden, checks = review(version)
    out = [f"# {version} против {prev}", ""]
    out.append(f"## 1. «from», которого не было в игре: {len(wrong)}")
    out += [f"- {ctx} {name}: {text}" for _v, ctx, name, text in wrong] or ["- нет"]
    out += ["", f"## 2. Строки словами и что поменялось в файлах способности: {len(words)} (проверить тег: {checks})"]
    for hero, slug, r, fields, flag in words:
        mark = f" **{flag}**" if flag else ""
        out.append(f"- {hero} / {slug} [{r.get('tag', '').upper()}]{mark}: {r['text']}")
        out.append(f"    файлы: {_fields(fields)}")
    out += ["", f"## 3. Изменения в файлах, которых нет ни в одной строке: {len(hidden)} способностей"]
    for hero, slug, fields in hidden:
        out.append(f"- {hero} / {slug}: {_fields(fields)}")
    return "\n".join(out)


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    sys.stdout.reconfigure(encoding="utf-8")
    for v in argv:
        print(report(v))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
