#!/usr/bin/env python3
"""Patch the opening legend graphics with a translated 8x8 tilemap.

The legend is a pre-rendered BG3 screen.  Its tilemap is uploaded from
$7F:0010 to VRAM $6800 and its 16x16 font page from $7F:4000 (part of the
24 KB block at $7F:0000) to VRAM $5000.  Instead of recompressing the
bank-$37 asset, this tool stores a translated tilemap and 32 Latin tiles
in free space in bank $2E and hooks the two DMA launchers:

  0x17662  big block DMA  ($7F:0000 -> VRAM $3000, 0x6000 bytes)
  0x177C6  tilemap DMA    ($7F:0010 -> VRAM $6800, 0x0800 bytes)

The hooks copy the translated data into the WRAM buffers immediately
before the original DMA runs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HOOK_FONT = 0x17665
HOOK_TILE = 0x177C9
ORIG_DMA = bytes.fromhex("a9088d0b42")

# Free runs in the final PT/EN builds (bank $2A, LoROM).
LIB_BANK = 0x2A
LIB_BASE = 0x150000
FONT_HOOK_OFF = 0x153BC0
TILE_HOOK_OFF = 0x153C00
FONT_DATA_OFF = 0x157820
TILE_DATA_OFF = 0x153820
TILE_MAP_BYTES = 0x380          # rows 7..20, 14 rows
TILE_MAP_ROW = 7
FONT_DATA_ADDR = 0x8000 + (FONT_DATA_OFF - LIB_BASE)
TILE_DATA_ADDR = 0x8000 + (TILE_DATA_OFF - LIB_BASE)
FONT_HOOK_ADDR = 0x8000 + (FONT_HOOK_OFF - LIB_BASE)
TILE_HOOK_ADDR = 0x8000 + (TILE_HOOK_OFF - LIB_BASE)



# 5x7 glyphs, rows top to bottom.  Each row is five pixels wide.
GLYPHS = {
    " ": ("00000",) * 7,
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01110"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ".": ("00000", "00000", "00000", "00000", "00000", "00110", "00110"),
    ",": ("00000", "00000", "00000", "00000", "00110", "00110", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
}

# Tile slot for each supported character.  0x1E0 is blank; the rest follow.
SLOTS = {" ": 0x1E0, ".": 0x1FB, ",": 0x1FC, "'": 0x1FD, "-": 0x1FE, "?": 0x1FF}
for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    SLOTS[ch] = 0x1E1 + i

GLYPH_OFF = 0x1E0


def build_font() -> bytes:
    out = bytearray(0x200)
    for ch, slot in SLOTS.items():
        rows = GLYPHS[ch]
        off = (slot - GLYPH_OFF) * 16
        for y in range(7):
            bits = 0
            for x, c in enumerate(rows[y]):
                if c == "1":
                    bits |= 1 << (6 - x)  # 5 px wide, centred at x=1..5
            out[off + y * 2 + 1] = bits
    return bytes(out)


def build_tilemap(cfg: dict) -> tuple[bytes, list[dict]]:
    page = bytearray(0x800)
    start_row = int(cfg.get("start_row", 7))
    step = int(cfg.get("line_step", 2))
    report = []
    for i, line in enumerate(cfg["lines"]):
        text = line.upper()
        unknown = sorted({c for c in text if c not in SLOTS})
        if unknown:
            raise SystemExit(f"legend line {i}: unsupported chars {unknown!r}")
        row = start_row + i * step
        if row > 31:
            raise SystemExit(f"legend line {i}: row {row} out of range")
        col = max(0, (32 - len(text)) // 2)
        for j, ch in enumerate(text):
            if ch == " ":
                continue
            slot = SLOTS[ch]
            word = 0x2C00 | slot
            off = ((row * 32) + col + j) * 2
            page[off] = word & 0xFF
            page[off + 1] = word >> 8
        report.append({"line": i, "row": row, "col": col, "text": text})
    return bytes(page), report


def _assemble_mvn_hook(src_addr: int, dst_addr: int, count: int) -> bytes:
    code = bytearray()
    code += bytes.fromhex("08")            # PHP
    code += bytes.fromhex("c230")          # REP #$30
    code += bytes.fromhex("da5a8b")        # PHX PHY PHB
    code += bytes.fromhex("e220")          # SEP #$20
    code += bytes.fromhex("a9") + bytes([LIB_BANK])  # LDA #bank
    code += bytes.fromhex("48ab")          # PHA PLB (8-bit push)
    code += bytes.fromhex("c230")          # REP #$30
    code += bytes.fromhex("a2") + src_addr.to_bytes(2, "little")  # LDX #src
    code += bytes.fromhex("a0") + dst_addr.to_bytes(2, "little")  # LDY #dst
    code += bytes.fromhex("a9") + (count - 1).to_bytes(2, "little")  # LDA #count-1
    code += bytes.fromhex("54") + bytes([0x7F, LIB_BANK])  # MVN $7F,$bank
    code += bytes.fromhex("ab7afa")        # PLB PLY PLX
    code += bytes.fromhex("e220")          # SEP #$20
    code += bytes.fromhex("a908")          # LDA #$08
    code += bytes.fromhex("8d0b42")        # STA $420B
    code += bytes.fromhex("286b")          # PLP RTL
    return bytes(code)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True, type=Path)
    ap.add_argument("--translations", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()

    rom = bytearray(args.rom.read_bytes())
    cfg = json.loads(args.translations.read_text(encoding="utf-8"))
    page, lines = build_tilemap(cfg)
    tilemap = page[TILE_MAP_ROW * 64:TILE_MAP_ROW * 64 + TILE_MAP_BYTES]
    font = build_font()

    font_jsl = bytes([0x22, FONT_HOOK_ADDR & 0xFF, FONT_HOOK_ADDR >> 8, LIB_BANK])
    tile_jsl = bytes([0x22, TILE_HOOK_ADDR & 0xFF, TILE_HOOK_ADDR >> 8, LIB_BANK])
    if rom[HOOK_FONT:HOOK_FONT + 4] == font_jsl:
        raise SystemExit("ROM already contains the legend patch")
    if rom[HOOK_FONT:HOOK_FONT + 5] != ORIG_DMA:
        raise SystemExit(f"unexpected font DMA bytes at {HOOK_FONT:#x}")
    if rom[HOOK_TILE:HOOK_TILE + 5] != ORIG_DMA:
        raise SystemExit(f"unexpected tile DMA bytes at {HOOK_TILE:#x}")

    for off, size, name in [
        (FONT_HOOK_OFF, 0x40, "font hook"),
        (TILE_HOOK_OFF, 0x40, "tile hook"),
        (FONT_DATA_OFF, len(font), "font data"),
        (TILE_DATA_OFF, len(tilemap), "tilemap"),
    ]:
        if any(rom[off:off + size]):
            raise SystemExit(f"{name} area at {off:#x} is not free")

    font_hook = _assemble_mvn_hook(FONT_DATA_ADDR, 0x5E00, len(font))
    tile_hook = _assemble_mvn_hook(TILE_DATA_ADDR, 0x0010 + TILE_MAP_ROW * 64, len(tilemap))
    if len(font_hook) > 0x40 or len(tile_hook) > 0x40:
        raise SystemExit("hook code does not fit its 0x40-byte slot")

    rom[FONT_HOOK_OFF:FONT_HOOK_OFF + len(font_hook)] = font_hook
    rom[TILE_HOOK_OFF:TILE_HOOK_OFF + len(tile_hook)] = tile_hook
    rom[FONT_DATA_OFF:FONT_DATA_OFF + len(font)] = font
    rom[TILE_DATA_OFF:TILE_DATA_OFF + len(tilemap)] = tilemap

    rom[HOOK_FONT:HOOK_FONT + 5] = font_jsl + b"\xea"
    rom[HOOK_TILE:HOOK_TILE + 5] = tile_jsl + b"\xea"

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(rom)

    report = {
        "input": str(args.rom),
        "output": str(args.out),
        "input_sha256": sha256(args.rom.read_bytes()),
        "output_sha256": sha256(rom),
        "font_hook": f"0x{FONT_HOOK_OFF:06x}",
        "tile_hook": f"0x{TILE_HOOK_OFF:06x}",
        "font_data": f"0x{FONT_DATA_OFF:06x}",
        "tilemap_data": f"0x{TILE_DATA_OFF:06x}",
        "lines": lines,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("output", "output_sha256")}, indent=2))


if __name__ == "__main__":
    main()
