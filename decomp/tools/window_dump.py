#!/usr/bin/env python3
"""Render a window tilemap from a recomp state dump.

The recomp state dump has WRAM (128 KiB) and VRAM (64 KiB, 16-bit words).
Window tilemaps live at $7E:3800 (32x32 entries, 16 bits each). Each entry
is `tile | palette<<10 | hflip<<14 | vflip<<15`. This tool draws the whole
32x32 tilemap with the font page at `--font-base`, so a dialogue or menu
can be inspected without a running emulator.

Example:
  python3 tools/window_dump.py \
      --wram state.wram.bin --vram state.vram.bin \
      --out build/text/window.bmp --scale 2
"""
from __future__ import annotations

import argparse
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from vram_tiles import load_words, tile_pixels  # noqa: E402


def read_tilemap(wram: bytes, base: int, width: int = 32, height: int = 32) -> list[list[int]]:
    rows: list[list[int]] = []
    for y in range(height):
        row = []
        for x in range(width):
            off = base + (y * width + x) * 2
            if off + 1 >= len(wram):
                row.append(0)
            else:
                row.append(wram[off] | (wram[off + 1] << 8))
        rows.append(row)
    return rows


def render_tilemap(
    tilemap: list[list[int]],
    words: list[int],
    font_base: int,
    bpp: int,
    scale: int,
    palette: str,
) -> tuple[int, int, list[list[int]]]:
    width = len(tilemap[0]) * 8
    height = len(tilemap) * 8
    out_w = width * scale
    out_h = height * scale
    image = [[0] * out_w for _ in range(out_h)]
    for ty, row in enumerate(tilemap):
        for tx, entry in enumerate(row):
            tile = entry & 0x3FF
            if tile == 0:
                continue
            pixels = tile_pixels(words, font_base, tile, bpp)
            hflip = bool(entry & 0x4000)
            vflip = bool(entry & 0x8000)
            for y in range(8):
                sy = 7 - y if vflip else y
                for x in range(8):
                    sx = 7 - x if hflip else x
                    value = pixels[sy][sx]
                    if value == 0:
                        continue
                    for oy in range(scale):
                        for ox in range(scale):
                            py = (ty * 8 + y) * scale + oy
                            px = (tx * 8 + x) * scale + ox
                            if 0 <= py < out_h and 0 <= px < out_w:
                                image[py][px] = value
    return out_w, out_h, image


def write_bmp(path: pathlib.Path, width: int, height: int, image: list[list[int]]) -> None:
    stride = (width * 3 + 3) & ~3
    raw = bytearray()
    for y in range(height - 1, -1, -1):
        row = bytearray()
        for x in range(width):
            value = image[y][x]
            shade = min(255, 32 + value * 32) if value else 0
            row += bytes((shade, shade, shade))
        row += b"\x00" * (stride - len(row))
        raw += row
    file_size = 14 + 40 + len(raw)
    header = b"BM" + struct.pack("<IHHI", file_size, 0, 0, 14 + 40)
    info = struct.pack("<IiiHHIIiiII", 40, width, height, 1, 24, 0, len(raw), 2835, 2835, 0, 0)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + info + bytes(raw))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--wram", required=True)
    ap.add_argument("--vram", required=True)
    ap.add_argument("--tilemap-base", default="3800", help="WRAM byte offset (hex)")
    ap.add_argument("--font-base", default="1000", help="VRAM word address (hex)")
    ap.add_argument("--bpp", type=int, choices=(2, 4), default=2)
    ap.add_argument("--scale", type=int, default=2)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    wram = pathlib.Path(args.wram).read_bytes()
    words = load_words(pathlib.Path(args.vram))
    tilemap = read_tilemap(wram, int(args.tilemap_base, 16))
    width, height, image = render_tilemap(
        tilemap, words, int(args.font_base, 16), args.bpp, max(1, args.scale), ""
    )
    write_bmp(pathlib.Path(args.out), width, height, image)
    print(f"wrote {args.out} ({width}x{height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
