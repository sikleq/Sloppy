"""Build-time replacements for CSS :has() on patch pages.

A patch page is one document of 12-20k elements. With ~50 `:has(...)` selectors in
styles.css, every DOM change during scrolling (the patch-dynamics rows are built lazily
as entities come into view) made Chrome re-match those selectors over thousands of
rows: 4-5 s of style recalculation per scroll of 7.38 / 7.41. The same facts are known
when the page is written, so they become plain classes here and styles.css matches the
classes instead:

    ul.changes > li  with a direct .row-tag-empty child   -> li-notag
    ul.changes > li  without a direct .row-text child     -> li-notext
    ul.changes > li  with a direct .badge-group child     -> li-bg
    ul.changes > li  with a direct .formula-table child   -> li-formula
    ul.subnotes > li with a direct .subnote-collapse       -> li-collapse
    .ability-block   without a direct ul.changes > li     -> ab-empty
    .ability-change.unified-panes containing a .formula-table-wrap -> has-formula-wrap
"""
import re

_TAG_RE = re.compile(r'<(/?)([a-zA-Z][\w-]*)((?:[^>"\']|"[^"]*"|\'[^\']*\')*?)(/?)>')
_CLASS_RE = re.compile(r'\bclass="([^"]*)"')
_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
_RAW = {"script", "style"}


class _Node:
    __slots__ = ("name", "cls", "start", "end", "kids", "parent", "has_fw", "add")

    def __init__(self, name, cls, start, end, parent):
        self.name, self.cls, self.start, self.end = name, cls, start, end
        self.kids, self.parent, self.has_fw, self.add = [], parent, False, []


def _parse(html):
    nodes, stack, pos = [], [], 0
    while True:
        m = _TAG_RE.search(html, pos)
        if not m:
            break
        closing, name = m.group(1), m.group(2).lower()
        if not closing:
            cm = _CLASS_RE.search(m.group(3))
            node = _Node(name, set(cm.group(1).split()) if cm else set(), m.start(), m.end(),
                         stack[-1] if stack else None)
            if stack:
                stack[-1].kids.append(node)
            nodes.append(node)
            if name in _RAW:                     # skip script / style bodies
                close = html.find(f"</{name}", m.end())
                pos = len(html) if close < 0 else close
                continue
            if name not in _VOID and not m.group(4):
                stack.append(node)
        else:
            for i in range(len(stack) - 1, -1, -1):   # pop to the matching open tag
                if stack[i].name == name:
                    del stack[i:]
                    break
        pos = m.end()
    return nodes


def add_static_has_classes(html):
    nodes = _parse(html)
    for n in reversed(nodes):                    # descendant flag, children before parents
        if n.parent and (n.has_fw or "formula-table-wrap" in n.cls):
            n.parent.has_fw = True
    for n in nodes:
        kid_cls = set().union(*(k.cls for k in n.kids)) if n.kids else set()
        p = n.parent
        if n.name == "li" and p is not None and p.name == "ul":
            if "changes" in p.cls:
                if "row-tag-empty" in kid_cls:
                    n.add.append("li-notag")
                if "row-text" not in kid_cls:
                    n.add.append("li-notext")
                if "badge-group" in kid_cls:
                    n.add.append("li-bg")
                if "formula-table" in kid_cls:
                    n.add.append("li-formula")
            if "subnotes" in p.cls and "subnote-collapse" in kid_cls:
                n.add.append("li-collapse")
        elif n.name == "div" and "ability-block" in n.cls:
            if not any(k.name == "ul" and "changes" in k.cls and any(g.name == "li" for g in k.kids)
                       for k in n.kids):
                n.add.append("ab-empty")
        elif n.name == "div" and {"ability-change", "unified-panes"} <= n.cls and n.has_fw:
            n.add.append("has-formula-wrap")
    out, last = [], 0
    for n in nodes:
        if not n.add:
            continue
        tag = html[n.start:n.end]
        extra = " ".join(c for c in n.add if c not in n.cls)
        if not extra:
            continue
        if _CLASS_RE.search(tag):
            tag = _CLASS_RE.sub(lambda m: f'class="{m.group(1)} {extra}"', tag, count=1)
        else:
            cut = len(tag) - (2 if tag.endswith("/>") else 1)
            tag = f'{tag[:cut]} class="{extra}"{tag[cut:]}'
        out.append(html[last:n.start])
        out.append(tag)
        last = n.end
    out.append(html[last:])
    return "".join(out)
