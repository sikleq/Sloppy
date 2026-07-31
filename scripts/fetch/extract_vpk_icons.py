"""extract_vpk_icons.py — достаёт иконки предметов прямо из игрового VPK.

Зачем: Valve обновляет арт в клиенте сразу, а на веб-CDN
(`cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/`) новые
файлы появляются с задержкой в несколько дней. Когда патчноут пишет
"Updated item icons for …", единственный актуальный источник — сам клиент.

Источник: `<Steam>/dota 2 beta/game/dota/pak01_dir.vpk`,
внутренний путь `panorama/images/items/<slug>_png.vtex_c`.

Формат: Source 2 vtex_c. Встречаются два варианта пикселей:
  * DXT5 + YCoCg (метаблок RED2 содержит "YCoCg Conv") — яркость лежит в
    альфа-канале, Co/Cg в R/G, масштаб цветности в B;
  * BGRA8888 — несжатый.
Оба разбираются здесь, PNG пишется в `icons/items/<slug>.png`.

Запуск:
    python scripts/fetch/extract_vpk_icons.py splintmail hydras_breath
    python scripts/fetch/extract_vpk_icons.py --check        # сверить все локальные иконки
    python scripts/fetch/extract_vpk_icons.py --check --write  # и обновить расхождения
"""
import argparse
import struct
import sys
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[2]
ICONS = ROOT / "icons" / "items"
DEFAULT_VPK = Path(
    r"C:/Program Files (x86)/Steam/steamapps/common/dota 2 beta/game/dota/pak01_dir.vpk")
VPK_ITEM_PATH = "panorama/images/items/{}_png.vtex_c"
DIFF_THRESHOLD = 8.0          # средняя разница по каналам, выше — считаем арт другим

FOURCC = {1: b"DXT1", 2: b"DXT5"}
DX10 = {19: 95, 20: 98}       # BC6H_UF16, BC7_UNORM
BGRA8888 = 28


# ---------- VPK v2 ----------

def _cstr(buf, pos):
    end = buf.index(b"\0", pos)
    return buf[pos:end].decode("utf-8"), end + 1


def read_tree(dir_path: Path):
    """{internal path: (archive_idx, offset, length, preload)} + data base offset."""
    data = dir_path.read_bytes()
    sig, ver, tree_size = struct.unpack_from("<III", data, 0)
    if sig != 0x55AA1234:
        raise ValueError(f"{dir_path} is not a VPK")
    pos = header = 28 if ver == 2 else 12
    entries = {}
    while True:
        ext, pos = _cstr(data, pos)
        if not ext:
            break
        while True:
            folder, pos = _cstr(data, pos)
            if not folder:
                break
            while True:
                name, pos = _cstr(data, pos)
                if not name:
                    break
                _crc, preload_len, archive_idx, offset, length, _term = \
                    struct.unpack_from("<IHHIIH", data, pos)
                pos += 18
                preload = data[pos:pos + preload_len]
                pos += preload_len
                entries[f"{folder}/{name}.{ext}"] = (archive_idx, offset, length, preload)
    return entries, header + tree_size


def read_file(dir_path: Path, internal: str, entries=None, base=None) -> bytes:
    if entries is None:
        entries, base = read_tree(dir_path)
    archive_idx, offset, length, preload = entries[internal]
    if length == 0:
        return preload
    if archive_idx == 0x7FFF:
        blob = dir_path.read_bytes()[base + offset: base + offset + length]
    else:
        pak = dir_path.parent / dir_path.name.replace("_dir.vpk", f"_{archive_idx:03d}.vpk")
        with open(pak, "rb") as fh:
            fh.seek(offset)
            blob = fh.read(length)
    return preload + blob


# ---------- vtex_c ----------

def vtex_spec(blob: bytes):
    """(width, height, format_id, pixel_payload). The first uint32 is the length
    of the resource metadata; mip-0 pixels follow it."""
    meta_len = struct.unpack_from("<I", blob, 0)[0]
    _hdr_ver, _ver, block_off, block_count = struct.unpack_from("<HHII", blob, 4)
    pos, data_off = 8 + block_off, None
    for _ in range(block_count):
        if blob[pos:pos + 4] == b"DATA":
            data_off = pos + 4 + struct.unpack_from("<I", blob, pos + 4)[0]
        pos += 12
    w, h, _depth = struct.unpack_from("<HHH", blob, data_off + 20)
    return w, h, blob[data_off + 26], blob[meta_len:]


def _dds(w: int, h: int, fmt: int, payload: bytes) -> bytes:
    if fmt in FOURCC:
        pixel_format = struct.pack("<II4sIIIII", 32, 0x4, FOURCC[fmt], 0, 0, 0, 0, 0)
        extra = b""
    elif fmt in DX10:
        pixel_format = struct.pack("<II4sIIIII", 32, 0x4, b"DX10", 0, 0, 0, 0, 0)
        extra = struct.pack("<IIIII", DX10[fmt], 3, 0, 1, 0)
    else:
        raise ValueError(f"unsupported vtex format id {fmt}")
    header = (b"DDS " + struct.pack("<IIIIIII", 124, 0x1 | 0x2 | 0x4 | 0x1000 | 0x80000,
                                    h, w, len(payload), 0, 1)
              + b"\0" * 44 + pixel_format
              + struct.pack("<IIIII", 0x1000, 0, 0, 0, 0))
    return header + extra + payload


def _ycocg(img: Image.Image) -> Image.Image:
    a = np.array(img.convert("RGBA")).astype(np.int32)
    r, g, b, luma = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    scale = (b >> 3) + 1
    co, cg = (r - 128) // scale, (g - 128) // scale
    rgb = np.stack([luma + co - cg, luma + cg, luma - co - cg], axis=-1)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB")


def decode(blob: bytes) -> Image.Image:
    w, h, fmt, payload = vtex_spec(blob)
    if fmt == BGRA8888:
        arr = np.frombuffer(payload[:w * h * 4], dtype=np.uint8).reshape(h, w, 4)
        return Image.fromarray(arr[..., [2, 1, 0, 3]], "RGBA")
    img = Image.open(BytesIO(_dds(w, h, fmt, payload)))
    meta_len = struct.unpack_from("<I", blob, 0)[0]
    if b"YCoCg" in blob[:meta_len]:
        return _ycocg(img)
    img = img.convert("RGBA")
    return img.convert("RGB") if img.getchannel("A").getextrema() == (255, 255) else img


def mean_diff(a: Image.Image, b: Image.Image) -> float:
    mode = "RGBA" if "A" in a.mode and "A" in b.mode else "RGB"
    return float(np.abs(np.array(a.convert(mode), dtype=float)
                        - np.array(b.convert(mode), dtype=float)).mean())


# ---------- CLI ----------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("slugs", nargs="*", help="иконки для обновления (без .png)")
    ap.add_argument("--vpk", type=Path, default=DEFAULT_VPK)
    ap.add_argument("--check", action="store_true",
                    help="сверить все локальные иконки с клиентом")
    ap.add_argument("--write", action="store_true",
                    help="вместе с --check: перезаписать расходящиеся")
    args = ap.parse_args()

    if not args.vpk.exists():
        print(f"VPK не найден: {args.vpk}", file=sys.stderr)
        return 1
    entries, base = read_tree(args.vpk)

    slugs = args.slugs
    if args.check:
        slugs = [p.stem for p in sorted(ICONS.glob("*.png"))]
    if not slugs:
        ap.error("укажи слаги или --check")

    stale = 0
    for slug in slugs:
        key = VPK_ITEM_PATH.format(slug)
        if key not in entries:
            if not args.check:
                print(f"{slug:24} нет в VPK")
            continue
        img = decode(read_file(args.vpk, key, entries, base))
        dst = ICONS / f"{slug}.png"
        note = "новый файл"
        if dst.exists():
            cur = Image.open(dst)
            note = (f"размер {cur.size} vs {img.size}" if cur.size != img.size
                    else f"расхождение {mean_diff(cur, img):.1f}")
            if cur.size == img.size and mean_diff(cur, img) <= DIFF_THRESHOLD:
                if args.check:
                    continue
                note = "арт совпадает"
        stale += 1
        if not args.check or args.write:
            img.save(dst, optimize=True)
            note += " -> записано"
        print(f"{slug:24} {img.size[0]}x{img.size[1]}  {note}")
    if args.check:
        print(f"сверено {len(slugs)}, расходится {stale}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
