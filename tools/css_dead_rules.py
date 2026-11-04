"""Declarations of the site's stylesheet that can never take effect, by a rule strict enough to prove it.

A declaration is dead when a later one in the same stylesheet has the same selector list, the same @media wrapper, the same
property and the same !important: it applies to the same elements with the same specificity and always wins. The earlier
one is a fallback only if a browser can reject the later value, so a later value with anything beyond plain numbers,
keywords, colours and common functions keeps the earlier one. @font-face and @keyframes are left alone.

    python tools/css_dead_rules.py          # list them
"""
import os
import re
import sys
from dataclasses import dataclass

# what every browser the site targets parses: a later value made of only this cannot be rejected
_SAFE_FUNCTIONS = {"rgb", "rgba", "hsl", "hsla", "var", "calc", "url", "linear-gradient", "repeating-linear-gradient",
                   "radial-gradient", "translate", "translateX", "translateY", "translateZ", "translate3d", "scale", "scaleX",
                   "scaleY", "rotate", "repeat", "minmax", "cubic-bezier", "steps", "drop-shadow", "brightness", "contrast",
                   "saturate", "grayscale", "opacity", "blur", "sepia", "hue-rotate", "inset"}
_NEW_UNITS = re.compile(r"\d(?:dvh|svh|lvh|dvw|svw|lvw|cqw|cqh|cqi|cqb|lh|rlh)\b")


@dataclass
class Decl:
    prop: str
    value: str
    important: bool
    start: int
    end: int           # past its ";" when it has one


@dataclass
class Rule:
    selector: str
    media: str
    start: int
    open_brace: int
    close_brace: int
    decls: list


def _skip_comment(text, i):
    return text.index("*/", i) + 2


def _block_end(text, i):
    """The index of the "}" closing the "{" at i."""
    depth, n, quote = 0, len(text), None
    while i < n:
        c = text[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif text.startswith("/*", i):
            i = _skip_comment(text, i)
            continue
        elif c in "\"'":
            quote = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("unbalanced braces")


def _decls(text, start, end):
    """The declarations between start and end, each with its exact span; comments between them stay out of the spans."""
    out, i = [], start
    while i < end:
        while i < end and (text[i].isspace() or text[i] == ";"):
            i += 1
        if text.startswith("/*", i):
            i = _skip_comment(text, i)
            continue
        if i >= end:
            break
        begin, depth, quote = i, 0, None
        while i < end:
            c = text[i]
            if quote:
                if c == "\\":
                    i += 2
                    continue
                if c == quote:
                    quote = None
            elif text.startswith("/*", i):
                i = _skip_comment(text, i)
                continue
            elif c in "\"'":
                quote = c
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            elif c == ";" and depth == 0:
                break
            i += 1
        stop = i + 1 if i < end and text[i] == ";" else i
        body = re.sub(r"/\*.*?\*/", " ", text[begin:i], flags=re.S).strip()
        if ":" in body:
            prop, value = body.split(":", 1)
            value = re.sub(r"\s+", " ", value).strip()
            important = bool(re.search(r"!\s*important\s*$", value, re.I))
            value = re.sub(r"\s*!\s*important\s*$", "", value, flags=re.I)
            out.append(Decl(prop.strip(), value, important, begin, stop))
        i = stop
    return out


def _norm(selector):
    selector = re.sub(r"/\*.*?\*/", " ", selector, flags=re.S)
    selector = re.sub(r"\s+", " ", selector).strip()
    return re.sub(r"\s*,\s*", ", ", selector)


def rules(text, start=0, end=None, media=""):
    """Every style rule in order, with the @media text it sits in. @font-face, @keyframes, @supports inside stay out."""
    end = len(text) if end is None else end
    i, out = start, []
    while i < end:
        while i < end and text[i].isspace():
            i += 1
        if i >= end:
            break
        if text.startswith("/*", i):
            i = _skip_comment(text, i)
            continue
        begin = i
        while i < end and text[i] not in "{;":
            if text.startswith("/*", i):
                i = _skip_comment(text, i)
                continue
            i += 1
        if i >= end:
            break
        if text[i] == ";":
            i += 1
            continue
        close = _block_end(text, i)
        prelude = _norm(text[begin:i])
        if prelude.startswith("@"):
            if prelude.lower().startswith("@media"):
                out += rules(text, i + 1, close, (media + " " + prelude).strip())
        else:
            out.append(Rule(prelude, media, begin, i, close, _decls(text, i + 1, close)))
        i = close + 1
    return out


def _can_be_rejected(value):
    if _NEW_UNITS.search(value):
        return True
    return any(fn not in _SAFE_FUNCTIONS for fn in re.findall(r"([A-Za-z-]+)\(", value))


def dead_declarations(text):
    """[(rule, decl, the rule of the later declaration that beats it)], in file order."""
    found, last = [], {}
    for rule in reversed(rules(text)):
        for decl in reversed(rule.decls):
            key = (rule.media, rule.selector, decl.prop.lower(), decl.important)
            later = last.get(key)
            if later is not None and not decl.prop.startswith("-") and not later[1].prop.startswith("-"):
                if not _can_be_rejected(later[1].value):
                    found.append((rule, decl, later[0]))
            if not decl.prop.startswith("-") or decl.prop.startswith("--"):
                last[key] = (rule, decl)
    found.sort(key=lambda x: x[1].start)
    return found


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from patch.css_bundle import read_css
    text = read_css()
    found = dead_declarations(text)
    print(f"{len(found)} declarations can never take effect")
    for rule, decl, _later in found:
        print(f"line {text.count(chr(10), 0, decl.start) + 1}: {rule.selector[:70]} {{ {decl.prop}: {decl.value[:50]} }}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
