"""Every object a generator module defines has a name no other generator module defines (Fable review 2026-11-21: 13
names in two to four modules, each different — the facade tools/generate_patch_code_v2.py keeps only the last one, so
a test through the facade could check another module's function than its name says)."""
import importlib
import inspect
import pkgutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


def test_generator_modules_share_no_names():
    import patchgen
    own = {}
    for info in pkgutil.iter_modules(patchgen.__path__):
        if info.name in ("cli",):
            continue
        mod = importlib.import_module(f"patchgen.{info.name}")
        for name, obj in vars(mod).items():
            if name.startswith("__") or inspect.ismodule(obj):
                continue
            if callable(obj) and getattr(obj, "__module__", mod.__name__) != mod.__name__:
                continue                                    # imported from another module
            if not callable(obj) and not hasattr(obj, "pattern"):
                continue                                    # plain constants: tuples, dicts
            own.setdefault(name, set()).add(info.name)
    shared = {n: sorted(m) for n, m in own.items() if len(m) > 1}
    # a compiled regex imported from another module is the same object: count only distinct ones
    clash = {}
    for n, mods in shared.items():
        objs = {id(getattr(importlib.import_module(f"patchgen.{m}"), n)) for m in mods}
        if len(objs) > 1:
            clash[n] = mods
    assert not clash, f"give each its own name: {clash}"
