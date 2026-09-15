# -*- coding: utf-8 -*-
r"""Build the slim JSONs of data/stats/<version>/ from the raw KV .txt already in that folder.

Why: fetch_stats.py (D:\Sloppy Patches) derives these only while pulling KV from d2vpkr, which
lands up to a day after a patch. extract_patchnotes.py can drop the raw .txt from the LIVE VPK
minutes after release — this runner closes the gap using fetch_stats' own parse/extract functions,
so the output is byte-for-byte the same shape.

Usage:  python tools/slim_from_kv.py 7.41f          # writes heroes/items/units/abilities/ability_ids .json
        python tools/slim_from_kv.py 7.41e --check  # regenerate to a temp dir and diff vs existing (self-test)
"""
import sys, os, json, tempfile, filecmp, importlib.util
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FETCH_STATS = r"D:\Sloppy Patches\fetch_stats.py"
spec = importlib.util.spec_from_file_location("fetch_stats", FETCH_STATS); fs = importlib.util.module_from_spec(spec); spec.loader.exec_module(fs)
OUTPUTS = {  # slim file -> (source .txt, extractor)
    "heroes.json": ("npc_heroes.txt", fs.extract_heroes), "items.json": ("items.txt", fs.extract_items),
    "units.json": ("npc_units.txt", fs.extract_units), "abilities.json": ("npc_abilities.txt", fs.extract_abilities),
    "ability_ids.json": ("npc_ability_ids.txt", fs.extract_ability_ids),
}
def build(version, out_dir):
    src = os.path.join(HERE, "data", "stats", version); os.makedirs(out_dir, exist_ok=True); done = []
    for name, (txt, fn) in OUTPUTS.items():
        p = os.path.join(src, txt)
        if not os.path.exists(p): print(f"  skip {name}: no {txt}"); continue
        kv = fs.parse_kv(open(p, encoding="utf-8", errors="replace").read())
        data = fn(kv)
        open(os.path.join(out_dir, name), "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=2))
        done.append(name)
    return done
if __name__ == "__main__":
    ver = sys.argv[1]; check = "--check" in sys.argv
    if check:
        tmp = tempfile.mkdtemp(); done = build(ver, tmp); ok = True
        for name in done:
            a, b = os.path.join(tmp, name), os.path.join(HERE, "data", "stats", ver, name)
            same = os.path.exists(b) and json.load(open(a, encoding="utf-8")) == json.load(open(b, encoding="utf-8"))
            print(f"  {name}: {'identical' if same else 'DIFFERENT'}"); ok &= same
        print("SELF-TEST", "OK" if ok else "FAILED"); sys.exit(0 if ok else 1)
    done = build(ver, os.path.join(HERE, "data", "stats", ver)); print("written:", done)
