#!/usr/bin/env python3
"""Collect Telegram channel members' display names -> data/signatures.json.

The Sloppy index page has a "wall of signatures": faint pixel-font graffiti of
channel-member usernames scattered around the inventory book. This script
produces the data that wall reads from.

WHY Telethon (and not a bot):
    The Telegram **Bot API cannot enumerate channel members** — there is no
    `getChatMembers`. Only the **MTProto client API**, acting as a real user
    account, can iterate participants (and for broadcast channels you must be an
    admin of the channel). So this runs under YOUR user account via Telethon.
    A future "bot" can trigger this same MTProto flow; it can't replace it.

USAGE (manual, for now):
    pip install telethon
    set TG_API_ID=1234567                # from https://my.telegram.org/apps
    set TG_API_HASH=0123456789abcdef...
    set TG_CHANNEL=@your_channel         # @username, t.me link, or numeric id
    # Private group/supergroup: use the -100 form, e.g.  set TG_CHANNEL=-1002279897249
    python scripts/fetch_signatures.py
    # First run asks for your phone + login code (saved to .tg_signatures.session,
    # which is gitignored). Later runs are non-interactive.

OUTPUT (data/signatures.json):
    {
      "updated": "2026-06-02T12:00:00Z",
      "source": "-1002279897249",
      "total_members": 206,    # members seen (excludes bots)
      "shown": 199,            # members with a usable display name
      "hidden": 7,             # empty or punctuation-only names -> "Hidden (x7)"
      "names": ["Alex", "Иван", ...]   # display names (first+last), sorted
    }

We use display NAMES, not @usernames: a name can't be used to find or DM a
member the way a public @handle can, so it leaks less. Members whose name is
empty or just punctuation (".", "...", emoji-only) are not shown — they're
counted into the single "Hidden (xN)" sign instead.

builders/patch.py reads this file at build time. If it is absent the wall falls
back to random placeholder usernames, so the site still builds without it.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = REPO_ROOT / "data" / "signatures.json"
SESSION_NAME = str(REPO_ROOT / ".tg_signatures")  # -> .tg_signatures.session

# Members to always skip entirely (not shown, not counted as Hidden) — matched
# by @username, case-insensitive, no leading @. The channel owner's own account
# lives here so it never appears on the signature wall.
EXCLUDE_USERNAMES = {"mr_sikle"}

# Display names that contain a link / @mention / promo (channel ads people put
# in their name) are dropped → counted into Hidden. Catches http(s)://, www.,
# t.me, telegram.me/org, @handle, and bare domains like "foo.com".
_LINK_RE = re.compile(
    r"https?://"
    r"|www\."
    r"|t\.me"
    r"|telegram\.(?:me|org)"
    r"|@[a-zA-Z]\w{2,}"
    r"|\b[\w-]+\.(?:com|net|org|io|gg|tv|me|ru|ua|by|kz|su|info|xyz|online|"
    r"site|link|app|dev|biz|shop|store|club|fun|live|pro|space|website)\b",
    re.IGNORECASE,
)


def _die(msg: str) -> "NoReturn":  # type: ignore[name-defined]
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def _load_config() -> tuple[int, str, str]:
    api_id = os.environ.get("TG_API_ID", "").strip()
    api_hash = os.environ.get("TG_API_HASH", "").strip()
    # Channel from CLI arg first, then env.
    channel = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("TG_CHANNEL", "")).strip()

    if not api_id or not api_hash:
        _die("set TG_API_ID and TG_API_HASH (get them at https://my.telegram.org/apps)")
    if not channel:
        _die("pass the channel as an argument or set TG_CHANNEL (e.g. @your_channel)")
    if not api_id.isdigit():
        _die("TG_API_ID must be numeric")
    return int(api_id), api_hash, channel


def _usernames(user) -> set[str]:
    """All public @usernames a Telethon User carries, lowercased, no @. Used
    only to match the EXCLUDE_USERNAMES skip-list (the displayed value is the
    name, not the handle)."""
    out: set[str] = set()
    primary = getattr(user, "username", None)
    if primary:
        out.add(primary.lower())
    for u in getattr(user, "usernames", None) or []:
        name = getattr(u, "username", None)
        if name:
            out.add(name.lower())
    return out


# Code points that render as nothing but can report isalnum()==True: Hangul
# fillers, zero-width chars, Braille blank, Mongolian vowel separator, ideographic
# space. Names made only of these collapse into "Hidden (xN)".
_BLANK_CP = frozenset({
    0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF,
    0x115F, 0x1160, 0x3164, 0xFFA0, 0x2800, 0x180E, 0x3000,
})


def _display_name(user) -> str | None:
    """Return the member's set display name (first + last), or None when it is
    empty or just punctuation (e.g. someone using "." or "..." as their name)."""
    first = (getattr(user, "first_name", None) or "").strip()
    last = (getattr(user, "last_name", None) or "").strip()
    name = " ".join(part for part in (first, last) if part)
    if not name:
        return None
    # Require at least one VISIBLE letter or digit -> drops ".", "...", emoji-only
    # and other symbol-only "names". str.isalnum() is Unicode-aware, so Cyrillic
    # and other scripts count as real names. But some "blank" code points report
    # isalnum()==True yet render as nothing (Hangul fillers U+1160/U+3164/etc.,
    # zero-width chars, Braille blank) — exclude them, else a beam on the site
    # flies to an invisible name.
    if not any(ch.isalnum() and ord(ch) not in _BLANK_CP for ch in name):
        return None
    if _LINK_RE.search(name):
        return None  # contains a link / @mention / promo — skip (→ Hidden)
    return name


def main() -> None:
    api_id, api_hash, channel = _load_config()

    try:
        from telethon.sync import TelegramClient
        from telethon.tl.types import User
    except ImportError:
        _die("telethon is not installed — run:  pip install telethon")

    names: list[str] = []
    total = 0
    hidden = 0

    # Numeric IDs (e.g. a private supergroup "-1002279897249") must be passed as
    # an int, otherwise Telethon treats the string as a username and fails.
    target = int(channel) if channel.lstrip("-").isdigit() else channel

    with TelegramClient(SESSION_NAME, api_id, api_hash) as client:
        try:
            entity = client.get_entity(target)
        except Exception:  # noqa: BLE001
            # A private group/channel referenced by numeric id is not resolvable
            # until the session has loaded its dialog list — that's where Telethon
            # learns the entity's access_hash. Prime the cache, then retry once.
            try:
                client.get_dialogs()
                entity = client.get_entity(target)
            except Exception as exc:  # noqa: BLE001 - surface the failure plainly
                _die(
                    f"could not resolve channel {channel!r}: {exc}\n"
                    f"  Private group/supergroup? use the -100 form, e.g. -100<id>.\n"
                    f"  Also make sure this account is a member of it."
                )

        print(f"Fetching participants of {channel} ...", file=sys.stderr)
        for member in client.iter_participants(entity):
            # Only count real human members; bots aren't "signatures".
            if not isinstance(member, User):
                continue
            if getattr(member, "bot", False):
                continue
            if _usernames(member) & EXCLUDE_USERNAMES:
                continue  # owner / explicitly excluded — skip entirely
            total += 1
            name = _display_name(member)
            if name:
                names.append(name)
            else:
                hidden += 1

    names.sort(key=str.lower)
    payload = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": channel,
        "total_members": total,
        "shown": len(names),
        "hidden": hidden,
        "names": names,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")

    rel = OUT_PATH.relative_to(REPO_ROOT)
    print(
        f"  -> {rel}: {len(names)} names, Hidden (x{hidden}), "
        f"{total} members total",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
