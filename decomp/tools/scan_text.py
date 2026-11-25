#!/usr/bin/env python3
"""Initial text-table probe for the decomp.

The game builds ITEM names from pointer tables in bank $11. This tool dumps
the pointer tables and the raw null-terminated byte strings they point to.
It deliberately does not embed the game's text: output goes to
decomp/build/text/ (ignored by git) for analysis.

Known starting points from the recomp item-name work:
  $11:CDFD and $11:D5A8  (16-bit pointer tables)
  $11:C000              (character/glyph-related table)
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[2]
TABLES = [(0x11, 0xCDFD), (0x11, 0xD5A8)]


def lorom_offset(bank: int, addr: int) -> int:
    bank &= 0x7F
    if addr >= 0x8000:
        return bank * 0x8000 + (addr - 0x8000)
    return bank * 0x8000 + addr


def resolve_rom(explicit: str | None, root: pathlib.Path) -> pathlib.Path | None:
    if explicit:
        candidates = [pathlib.Path(explicit)]
    else:
        candidates = []
    env = os.environ.get("SNESRECOMP_ROM")
    if env:
        candidates.append(pathlib.Path(env))
    rom_cfg = root / "rom.cfg"
    if rom_cfg.exists():
        text = rom_cfg.read_text(encoding="utf-8", errors="replace").strip()
        if text:
            candidates.append(pathlib.Path(text))
    for name in ("kyuuyaku.sfc", "kyuuyakumegamitensei.sfc", "kyuuyakumegamitensei.smc"):
        candidates.append(root / name)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def read_c_string(data: bytes, offset: int, max_len: int) -> bytes:
    end = offset
    limit = min(len(data), offset + max_len)
    while end < limit and data[end] != 0:
        end += 1
    return data[offset:end]


def dump_pointer_table(data: bytes, bank: int, addr: int, count: int, max_len: int) -> dict:
    base = lorom_offset(bank, addr)
    entries = []
    for i in range(count):
        p = base + i * 2
        if p + 1 >= len(data):
            break
        target = data[p] | (data[p + 1] << 8)
        raw = read_c_string(data, lorom_offset(bank, target), max_len)
        entries.append(
            {
                "index": i,
                "target": f"{target:04X}",
                "length": len(raw),
                "hex": raw.hex(),
            }
        )
    return {
        "bank": f"{bank:02X}",
        "addr": f"{addr:04X}",
        "count_requested": count,
        "count_read": len(entries),
        "entries": entries,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", help="ROM path; defaults to SNESRECOMP_ROM/rom.cfg")
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--count", type=int, default=63)
    ap.add_argument("--max-len", type=int, default=64)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    root = pathlib.Path(args.root)
    rom = resolve_rom(args.rom, root)
    if rom is None:
        print("no ROM found; pass --rom or set SNESRECOMP_ROM", file=sys.stderr)
        return 1
    data = rom.read_bytes()
    out = pathlib.Path(args.out) if args.out else root / "decomp" / "build" / "text" / "item_ptrs.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "rom": str(rom),
        "tables": [
            dump_pointer_table(data, bank, addr, args.count, args.max_len)
            for bank, addr in TABLES
        ],
    }
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    for table in result["tables"]:
        print(
            f"  ${table['bank']}:{table['addr']} entries={table['count_read']} "
            f"lengths={[e['length'] for e in table['entries'][:12]]}..."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
