"""build_silent_changes.py — Diff per-hero KV files between consecutive patches
and emit a `patches/silent/{version}.html` "silent changes" page for each pair
where both `data/stats/{prev}/heroes/` and `data/stats/{curr}/heroes/` exist.

The KV files in data/stats/{version}/heroes/ are Valve's raw npc_dota_hero_*.txt
files (synced by fetch_stats.py + extract_patchnotes.py). They carry every field
of every ability — including hidden / service abilities the official patchnotes
don't mention.

Usage:
  python build_silent_changes.py             # all available pairs
  python build_silent_changes.py 7.41c       # one specific patch (vs prev)

This script intentionally stays standalone — it does NOT import or modify the
main build_patch.py monolith. The generated pages live under patches/silent/
and are linked from each regular patch page header (added separately).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent.parent
DATA_DIR = _HERE / "data" / "stats"
OUT_DIR = _HERE / "dist" / "patches" / "silent"

# When this file is executed as `python builders/silent.py`, Python puts the
# `builders/` directory first on sys.path. That shadows the real `patch/`
# package with `builders/patch.py`, so force the repo root to the front.
sys.path.insert(0, str(_HERE))

# Import from canonical source instead of maintaining a duplicate list.
from patch.meta import RELEASE_HISTORY as _RH
RELEASE_HISTORY = [p["version"] for p in _RH]

# Field-path patterns we suppress as engine-noise: visual FX, sound events,
# animation hooks, particle resource paths. Matched case-insensitively against
# the flattened key path (e.g. "Modifier_X.OnCreated.FireSound").
NOISE_PATTERNS = (
    "fx", "particle", "vpcf", "vsndevt", "vsnd", "sound", "animation",
    "anim_activity", "vmdl", "model", "thinkinterval",
    "scriptfile", "lua_", "abilityentityname", "abilityresource",
)

# Only these top-level field categories actually matter for gameplay; everything
# else is engine plumbing. Empty = no whitelist (diff everything except noise).
# Set the env var SC_FULL_DIFF=1 to bypass the whitelist for debugging.
INTERESTING_FIELDS = {
    "AbilityBehavior", "AbilityCastRange", "AbilityCastPoint", "AbilityCooldown",
    "AbilityManaCost", "AbilityDamage", "AbilityDuration",
    "AbilityCharges", "AbilityChargeRestoreTime",
    "AbilityUnitTargetTeam", "AbilityUnitTargetType", "AbilityUnitTargetFlags",
    "AbilityUnitDamageType", "SpellImmunityType", "SpellDispellableType",
    "FightRecapLevel", "MaxLevel",
    "HasScepterUpgrade", "HasShardUpgrade", "IsGrantedByScepter", "IsGrantedByShard",
    "ItemRequirements", "AbilityValues",  # whole AbilityValues block iterated below
}


# ───────────────────────── KV PARSER ───────────────────────────────────────

def _decode_bytes(raw: bytes) -> str:
    if raw.startswith(b"\xff\xfe"):
        return raw[2:].decode("utf-16-le", errors="replace")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8", errors="replace")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1", errors="replace")


def _tokenize_kv(text: str) -> list[str]:
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1
        elif c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
        elif c == "#":  # #base / #include directives
            while i < n and text[i] != "\n":
                i += 1
        elif c in "{}":
            out.append(c)
            i += 1
        elif c == '"':
            i += 1
            j = i
            while j < n and text[j] != '"':
                if text[j] == "\\" and j + 1 < n:
                    j += 2
                else:
                    j += 1
            out.append(text[i:j])
            i = j + 1
        else:
            j = i
            while j < n and text[j] not in ' \t\r\n{}"':
                j += 1
            if j > i:
                out.append(text[i:j])
            i = j
    return out


def parse_kv(text: str) -> dict:
    """Parse Valve KV-1 text. Returns the top-level {root_key: {...}} dict.
    Tolerates duplicate keys (last write wins) and unbalanced braces."""
    tokens = _tokenize_kv(text)
    pos = [0]

    def parse_block() -> dict:
        result: dict = {}
        while pos[0] < len(tokens) and tokens[pos[0]] != "}":
            key = tokens[pos[0]]
            pos[0] += 1
            if pos[0] >= len(tokens):
                break
            val = tokens[pos[0]]
            if val == "{":
                pos[0] += 1
                result[key] = parse_block()
                if pos[0] < len(tokens) and tokens[pos[0]] == "}":
                    pos[0] += 1
            else:
                pos[0] += 1
                result[key] = val
        return result

    if not tokens:
        return {}
    root = tokens[pos[0]]
    pos[0] += 1
    if pos[0] < len(tokens) and tokens[pos[0]] == "{":
        pos[0] += 1
        body = parse_block()
        if pos[0] < len(tokens) and tokens[pos[0]] == "}":
            pos[0] += 1
        return {root: body}
    return {}


# ───────────────────────── LOAD HEROES DIR ─────────────────────────────────

def _is_noise(key_path: str) -> bool:
    low = key_path.lower()
    return any(p in low for p in NOISE_PATTERNS)


def _flatten(d: dict, prefix: str = "") -> dict:
    """Flatten nested dict into {a.b.c: value}, skipping engine-noise paths."""
    out: dict = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if _is_noise(key):
            continue
        if isinstance(v, dict):
            out.update(_flatten(v, key))
        else:
            out[key] = v
    return out


_SKIP_TOP_KEYS = {"Version"}


def load_hero_abilities(version: str) -> dict[str, dict[str, dict]]:
    """Return { hero_slug: { ability_slug: { flat_field: value } } } for the
    given version. Empty dict if the heroes/ folder is missing.

    Per-hero files are structured as
        "DOTAAbilities" { "Version" "1" ability_slug { ... } ability_slug2 {...} }
    i.e. abilities are top-level inside DOTAAbilities. The hero identity comes
    from the filename, NOT from the KV body."""
    heroes_dir = DATA_DIR / version / "heroes"
    if not heroes_dir.exists():
        return {}
    out: dict[str, dict[str, dict]] = {}
    for p in sorted(heroes_dir.glob("npc_dota_hero_*.txt")):
        try:
            text = _decode_bytes(p.read_bytes())
            kv = parse_kv(text)
        except Exception as e:
            print(f"  ⚠ parse failed: {p.name}: {e}", file=sys.stderr)
            continue
        hero_slug = p.stem
        root = next(iter(kv.values()), {})
        if not isinstance(root, dict):
            continue
        abilities: dict[str, dict] = {}
        for key, val in root.items():
            if key in _SKIP_TOP_KEYS or not isinstance(val, dict):
                continue
            abilities[key] = _flatten(val)
        if abilities:
            out[hero_slug] = abilities
    return out


# ───────────────────────── DIFF ────────────────────────────────────────────

def _interesting(field: str) -> bool:
    if os.environ.get("SC_FULL_DIFF") == "1":
        return True
    top = field.split(".", 1)[0]
    if top in INTERESTING_FIELDS:
        return True
    # av_* per-level values (e.g. av_damage, av_duration) — always interesting.
    if top.startswith("av_"):
        return True
    return False


def diff_versions(prev: dict, curr: dict) -> dict:
    """Return { hero: { ability: { field: (old, new) } } }.
    None as old → added field/ability. None as new → removed."""
    out: dict = {}
    heroes = set(prev) | set(curr)
    for h in sorted(heroes):
        pabs = prev.get(h, {})
        cabs = curr.get(h, {})
        abilities = set(pabs) | set(cabs)
        h_diff: dict = {}
        for a in sorted(abilities):
            pf = pabs.get(a, {})
            cf = cabs.get(a, {})
            fields = set(pf) | set(cf)
            f_diff: dict = {}
            for f in sorted(fields):
                if not _interesting(f):
                    continue
                pv = pf.get(f)
                cv = cf.get(f)
                if pv != cv:
                    f_diff[f] = (pv, cv)
            if f_diff:
                h_diff[a] = f_diff
        if h_diff:
            out[h] = h_diff
    return out


# ───────────────────────── HTML RENDER ─────────────────────────────────────

def _esc(s) -> str:
    return (str(s).replace("&", "&amp;")
                  .replace("<", "&lt;")
                  .replace(">", "&gt;"))


def _val_cell(v) -> str:
    if v is None:
        return '<span class="sc-absent">—</span>'
    s = str(v)
    # Pretty-print AbilityBehavior flag soup (split on |).
    if "DOTA_ABILITY_BEHAVIOR" in s and "|" in s:
        parts = [p.strip() for p in s.split("|")]
        return ''.join(f'<span class="sc-flag">{_esc(p)}</span>' for p in parts)
    return _esc(s)


def _hero_display(slug: str) -> str:
    nice = slug.replace("npc_dota_hero_", "").replace("_", " ")
    return nice.title()


def render_diff_html(version: str, prev: str, diff: dict) -> str:
    if not diff:
        return '<p class="sc-empty">No diff detected (or both patches are identical for tracked fields).</p>'
    parts: list[str] = []
    for hero, abilities in diff.items():
        parts.append(f'<section class="sc-hero"><h2>{_esc(_hero_display(hero))}</h2>')
        for ability, fields in abilities.items():
            parts.append(
                f'<div class="sc-ability">'
                f'<h3 class="sc-ability-name">{_esc(ability)}</h3>'
                f'<table class="sc-table">'
                f'<thead><tr><th>Field</th>'
                f'<th>{_esc(prev)}</th><th>{_esc(version)}</th></tr></thead>'
                f'<tbody>'
            )
            for f, (pv, cv) in fields.items():
                parts.append(
                    f'<tr><td class="sc-field">{_esc(f)}</td>'
                    f'<td class="sc-old">{_val_cell(pv)}</td>'
                    f'<td class="sc-new">{_val_cell(cv)}</td></tr>'
                )
            parts.append('</tbody></table></div>')
        parts.append('</section>')
    return ''.join(parts)


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SIKLE\\Silent Changes {version}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Jersey+10&family=Jersey+25&display=swap">
<link rel="stylesheet" href="../../styles.css">
<link rel="icon" type="image/svg+xml" href="../../icons/favicon/favicon.svg">
<link rel="icon" type="image/png" sizes="96x96" href="../../icons/favicon/favicon-96x96.png">
<link rel="shortcut icon" href="../../icons/favicon/favicon.ico">
<style>
.sc-page {{ max-width: 1080px; margin: 0 auto; padding: 24px 28px 80px; }}
.sc-page h1 {{ font-family: 'Jersey 10', monospace; font-size: 38px;
              letter-spacing: 1px; color: #e6edf3; margin-bottom: 4px; }}
.sc-page .sc-sub {{ color: #8b949e; font-size: 13px; margin-bottom: 24px; }}
.sc-hero {{ margin: 28px 0; }}
.sc-hero h2 {{ font-size: 18px; color: #79c0ff; font-weight: 700;
              border-bottom: 1px solid #21262d; padding-bottom: 6px; }}
.sc-ability {{ margin: 14px 0 14px 0; }}
.sc-ability-name {{ font-size: 13px; color: #c9d1d9; font-weight: 600;
                    font-family: 'Courier New', monospace; margin-bottom: 6px; }}
.sc-table {{ border-collapse: collapse; width: 100%; font-size: 12px;
            font-variant-numeric: tabular-nums; }}
.sc-table th, .sc-table td {{ padding: 5px 10px; border: 1px solid #30363d;
                              text-align: left; vertical-align: top; }}
.sc-table th {{ background: #161b22; color: #c9d1d9; font-weight: 600;
                font-size: 11px; text-transform: uppercase;
                letter-spacing: 0.5px; }}
.sc-field {{ font-family: 'Courier New', monospace; color: #8b949e;
             max-width: 280px; word-break: break-all; }}
.sc-old {{ background: rgba(248, 81, 73, 0.08); color: #f8a39e; }}
.sc-new {{ background: rgba(86, 211, 100, 0.08); color: #92e3a3; }}
.sc-absent {{ color: #6e7681; font-style: italic; }}
.sc-flag {{ display: inline-block; padding: 1px 6px; margin: 2px 4px 2px 0;
            background: rgba(121, 192, 255, 0.12); color: #79c0ff;
            border-radius: 3px; font-size: 10.5px;
            font-family: 'Courier New', monospace; }}
.sc-empty {{ color: #8b949e; font-style: italic; padding: 40px 0;
             text-align: center; }}
.sc-back {{ display: inline-block; margin-bottom: 16px; color: #79c0ff;
            text-decoration: none; font-size: 13px; }}
.sc-back:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
<div class="sc-page">
<a class="sc-back" href="../{version}.html">← Back to {version} changelog</a>
<h1>Silent Changes</h1>
<p class="sc-sub">Raw KV-field deltas between <strong>{prev}</strong> → <strong>{version}</strong>, parsed
from <code>data/stats/{{ver}}/heroes/*.txt</code>. These may overlap with the
official patchnotes — this is the source-of-truth view. Engine noise (FX, sounds,
animation, particle resources) is filtered out.</p>
{body}
</div>
</body>
</html>
"""


def build_page(version: str) -> str | None:
    try:
        idx = RELEASE_HISTORY.index(version)
    except ValueError:
        print(f"  ⚠ unknown version: {version}")
        return None
    if idx + 1 >= len(RELEASE_HISTORY):
        print(f"  ⚠ {version} is the oldest patch — nothing to diff against")
        return None
    prev = RELEASE_HISTORY[idx + 1]

    prev_data = load_hero_abilities(prev)
    curr_data = load_hero_abilities(version)
    if not prev_data:
        print(f"  ⚠ no heroes/ data for {prev} — skip")
        return None
    if not curr_data:
        print(f"  ⚠ no heroes/ data for {version} — skip")
        return None

    diff = diff_versions(prev_data, curr_data)
    body = render_diff_html(version, prev, diff)
    n_heroes = len(diff)
    n_changes = sum(len(f) for ab in diff.values() for f in ab.values())
    print(f"  -> silent/{version}.html  ({n_heroes} heroes, {n_changes} field deltas)")
    return PAGE_TEMPLATE.format(version=version, prev=prev, body=body)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) > 1:
        versions = [sys.argv[1]]
    else:
        versions = [
            v for i, v in enumerate(RELEASE_HISTORY)
            if i + 1 < len(RELEASE_HISTORY)
            and (DATA_DIR / v / "heroes").exists()
            and (DATA_DIR / RELEASE_HISTORY[i + 1] / "heroes").exists()
        ]
    if not versions:
        print("No patch pairs with both heroes/ folders available — nothing to do.")
        print("Run fetch_stats.py / extract_patchnotes.py first to populate heroes/.")
        return 0
    print(f"Building silent-changes pages for {len(versions)} patch(es)...")
    for v in versions:
        html = build_page(v)
        if html is not None:
            (OUT_DIR / f"{v}.html").write_text(html, encoding="utf-8")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
