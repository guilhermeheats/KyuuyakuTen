#!/usr/bin/env python3
"""Render SNES tiles from a recomp state-dump VRAM file.

The recomp state dump writes VRAM as 32768 little-endian 16-bit words. Each
tile row is one word: low byte = plane 0, high byte = plane 1 (and, for 4bpp,
the next 8 words carry planes 2/3). This is the PPU's native row-interleaved
format, not the byte layout of the raw cartridge.

Examples:
  # text view of the 8x8 font at word base $6000
  python3 tools/vram_tiles.py --vram state.vram.bin --base 6000 --start 20 --count 32

  # 4x contact sheet for the whole 2bpp page
  python3 tools/vram_tiles.py --vram state.vram.bin --base 6000 --count 256 \
      --bmp build/text/font_6000.bmp --scale 4
"""
from __future__ import annotations

import argparse
import pathlib
import struct
import sys

PALETTE = " .oO0#@%*+=:;,.?"


def load_words(path: pathlib.Path) -> list[int]:
    data = path.read_bytes()
    if len(data) % 2:
        raise ValueError("VRAM dump must have an even size")
    return [data[i] | (data[i + 1] << 8) for i in range(0, len(data), 2)]


def tile_pixels(words: list[int], base: int, tile: int, bpp: int) -> list[list[int]]:
    words_per_tile = 8 * (bpp // 2)
    start = base + tile * words_per_tile
    rows: list[list[int]] = []
    for y in range(8):
        w0 = words[(start + y) & 0x7FFF]
        p0 = w0 & 0xFF
        p1 = (w0 >> 8) & 0xFF
        p2 = p3 = 0
        if bpp >= 4:
            w1 = words[(start + 8 + y) & 0x7FFF]
            p2 = w1 & 0xFF
            p3 = (w1 >> 8) & 0xFF
        row = []
        for x in range(8):
            bit = 7 - x
            value = ((p0 >> bit) & 1) | (((p1 >> bit) & 1) << 1)
            if bpp >= 4:
                value |= ((p2 >> bit) & 1) << 2
                value |= ((p3 >> bit) & 1) << 3
            row.append(value)
        rows.append(row)
    return rows


def print_tiles(words: list[int], base: int, bpp: int, start: int, count: int) -> None:
    for tile in range(start, start + count):
        print(f"=== tile {tile:03X} (base={base:04X} bpp={bpp}) ===")
        for row in tile_pixels(words, base, tile, bpp):
            print("".join(PALETTE[min(v, len(PALETTE) - 1)] for v in row))


def write_bmp(path: pathlib.Path, words: list[int], base: int, bpp: int, start: int, count: int, scale: int) -> None:
    cols = 16
    rows_of_tiles = (count + cols - 1) // cols
    tile_px = 8 * scale
    gap = 2
    width = cols * (tile_px + gap) + gap
    height = rows_of_tiles * (tile_px + gap) + gap
    pixels = [[(0, 0, 0) for _ in range(width)] for _ in range(height)]

    def put(x: int, y: int, value: int) -> None:
        shade = min(255, value * 36 + (40 if value else 0))
        pixels[y][x] = (shade, shade, shade)

    for i in range(count):
        tile = start + i
        tx = gap + (i % cols) * (tile_px + gap)
        ty = gap + (i // cols) * (tile_px + gap)
        tile_rows = tile_pixels(words, base, tile, bpp)
        for y in range(8):
            for x in range(8):
                value = tile_rows[y][x]
                for sy in range(scale):
                    for sx in range(scale):
                        put(tx + x * scale + sx, ty + y * scale + sy, value)

    # 24-bit BMP, rows bottom-up, rows padded to 4 bytes.
    stride = (width * 3 + 3) & ~3
    raw = bytearray()
    for y in range(height - 1, -1, -1):
        row = bytearray()
        for x in range(width):
            r, g, b = pixels[y][x]
            row += bytes((b, g, r))
        row += b"\x00" * (stride - len(row))
        raw += row
    file_size = 14 + 40 + len(raw)
    header = b"BM" + struct.pack("<IHHI", file_size, 0, 0, 14 + 40)
    info = struct.pack(
        "<IiiHHIIiiII",
        40,
        width,
        height,
        1,
        24,
        0,
        len(raw),
        2835,
        2835,
        0,
        0,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + info + bytes(raw))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vram", required=True, help="recomp *.vram.bin state dump")
    ap.add_argument("--base", default="6000", help="tile base in VRAM words (hex)")
    ap.add_argument("--bpp", type=int, choices=(2, 4), default=2)
    ap.add_argument("--start", type=lambda s: int(s, 0), default=0)
    ap.add_argument("--count", type=lambda s: int(s, 0), default=64)
    ap.add_argument("--bmp", help="write a BMP contact sheet instead of text")
    ap.add_argument("--scale", type=int, default=4)
    args = ap.parse_args()

    words = load_words(pathlib.Path(args.vram))
    base = int(args.base, 16)
    if args.bmp:
        write_bmp(pathlib.Path(args.bmp), words, base, args.bpp, args.start, args.count, max(1, args.scale))
        print(f"wrote {args.bmp}")
    else:
        print_tiles(words, base, args.bpp, args.start, args.count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
