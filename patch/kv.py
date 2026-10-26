"""Valve KeyValues (KV1) text -> dict: the one parser of the project (audit 2026-10-26: builders/silent.py,
builders/mana_items.py and tools/fetch_stats.py each had their own copy; on all 9 819 KV files of the game-files store
and data/stats/ the three gave the same result). No imports outside the standard library: builders/, tools/ and
scripts/ import it from here."""
from __future__ import annotations


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
