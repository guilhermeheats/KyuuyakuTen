#!/usr/bin/env python3
"""Translate the status-screen stat labels (BG2 $6C00, 4bpp font $3000).

The five labels are part of the compressed panel asset $07:E998, which
the loader decompresses to $7F:0000 (labels at $7F:2686) and the 8x8
font page to $7F:0100.  This tool patches the decompressor call at the
status loader (file 0x19720) with a wrapper that:

  1. runs the original decompressor ($01:D61B);
  2. writes 13 Latin glyphs to $7F:01A0 (font tiles $05-$11);
  3. writes the five label rows to $7F:2686-$2786.

The following loader code fills the tilemap high bytes with $2C and
DMAs the font page/tilemap to VRAM, so the translated labels appear.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from patch_legend import GLYPHS as _LEGEND_GLYPHS

GLYPHS = dict(_LEGEND_GLYPHS)
GLYPHS["V"] = ("10001", "10001", "10001", "01010", "01010", "00100", "00100")

JSL_SITE = 0x19720
ORIG_JSL = bytes.fromhex("221bd601")

LIB_BANK = 0x2C
LIB_BASE = 0x160000
TABLE_OFF = 0x163A00
GLYPH_OFF = 0x163A40
WRAP_OFF = 0x163C00

TABLE_ADDR = 0x8000 + (TABLE_OFF - LIB_BASE)
GLYPH_ADDR = 0x8000 + (GLYPH_OFF - LIB_BASE)
WRAP_ADDR = 0x8000 + (WRAP_OFF - LIB_BASE)

TILE_ORDER = ["V", "I", "T", "N", "F", "O", "R", "A", "G", "S", "L", "U", "K"]
TILE = {ch: 0x05 + i for i, ch in enumerate(TILE_ORDER)}

ROW0 = 22
COL0 = 3
ROWS = 5
COLS = 5


def build_glyphs() -> bytes:
    out = bytearray(len(TILE_ORDER) * 32)
    for ti, ch in enumerate(TILE_ORDER):
        rows = GLYPHS[ch]
        off = ti * 32
        for y in range(7):
            bits = 0
            for x, c in enumerate(rows[y]):
                if c == "1":
                    bits |= 1 << (6 - x)
            # 4bpp: 8 rows of plane 0/1 (16 bytes), then 8 rows of plane 2/3.
            out[off + y * 2] = bits
            out[off + y * 2 + 1] = bits
    return bytes(out)


def build_table(labels: list[str]) -> bytes:
    if len(labels) != ROWS:
        raise SystemExit(f"expected {ROWS} labels, got {len(labels)}")
    out = bytearray()
    for label in labels:
        text = label.upper()
        if len(text) != 3:
            raise SystemExit(f"label {label!r} is not 3 characters")
        missing = sorted({c for c in text if c not in TILE})
        if missing:
            raise SystemExit(f"label {label!r}: unsupported {missing!r}")
        vals = [0x2C00 | TILE[c] for c in text] + [0x0000] * (COLS - 3)
        for w in vals:
            out += w.to_bytes(2, "little")
    return bytes(out)


def _long(addr: int) -> bytes:
    return bytes([0x8F]) + addr.to_bytes(3, "little")


def _lda_long_x(addr: int) -> bytes:
    return bytes([0xBF]) + addr.to_bytes(3, "little")


def build_wrapper(table_addr: int, glyph_addr: int, glyph_bytes: int) -> bytes:
    code = bytearray()
    code += bytes.fromhex("08c230da5a8b")          # PHP REP PHX PHY PHB
    code += bytes.fromhex("221bd601")              # JSL $01D61B
    code += bytes.fromhex("e220a97f48ab")          # SEP LDA #$7F PHA PLB
    code += bytes.fromhex("c230")                  # REP
    code += bytes([0xA2]) + glyph_addr.to_bytes(2, "little")  # LDX #glyph
    code += bytes([0xA0]) + 0x01A0.to_bytes(2, "little")     # LDY #$01A0
    code += bytes([0xA9]) + (glyph_bytes - 1).to_bytes(2, "little")
    code += bytes.fromhex("547f2c")                # MVN $7F,$2C
    code += bytes.fromhex("a20000")                # LDX #0
    table24 = (LIB_BANK << 16) | table_addr
    for r in range(ROWS):
        base = 0x7F0000 + 0x2100 + ((ROW0 + r) * 32 + COL0) * 2
        for c in range(COLS):
            code += _lda_long_x(table24)
            code += _long(base + c * 2)
            code += bytes.fromhex("e8e8")
    code += bytes.fromhex("ab7afa")                # PLB PLY PLX
    code += bytes.fromhex("286b")                  # PLP RTL
    return bytes(code)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True, type=Path)
    ap.add_argument("--labels", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()

    rom = bytearray(args.rom.read_bytes())
    cfg = json.loads(args.labels.read_text(encoding="utf-8"))
    labels = cfg["labels"]
    table = build_table(labels)
    glyphs = build_glyphs()
    wrapper = build_wrapper(TABLE_ADDR, GLYPH_ADDR, len(glyphs))

    if rom[JSL_SITE:JSL_SITE + 4] != ORIG_JSL:
        raise SystemExit(f"unexpected JSL bytes at {JSL_SITE:#x}")
    for off, size, name in [
        (TABLE_OFF, len(table), "table"),
        (GLYPH_OFF, len(glyphs), "glyphs"),
        (WRAP_OFF, len(wrapper), "wrapper"),
    ]:
        if any(rom[off:off + size]):
            raise SystemExit(f"{name} area at {off:#x} is not free")

    rom[TABLE_OFF:TABLE_OFF + len(table)] = table
    rom[GLYPH_OFF:GLYPH_OFF + len(glyphs)] = glyphs
    rom[WRAP_OFF:WRAP_OFF + len(wrapper)] = wrapper
    rom[JSL_SITE:JSL_SITE + 4] = bytes([0x22, WRAP_ADDR & 0xFF,
                                        WRAP_ADDR >> 8, LIB_BANK])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(rom)
    report = {
        "input": str(args.rom),
        "output": str(args.out),
        "input_sha256": sha256(args.rom.read_bytes()),
        "output_sha256": sha256(rom),
        "table": f"0x{TABLE_OFF:06x}",
        "glyphs": f"0x{GLYPH_OFF:06x}",
        "wrapper": f"0x{WRAP_OFF:06x}",
        "labels": labels,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("output", "output_sha256")}, indent=2))


if __name__ == "__main__":
    main()
