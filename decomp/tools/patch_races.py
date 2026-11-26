#!/usr/bin/env python3
"""Replace the fixed-width race prefixes used by the battle text engine.

The battle name line is built by the text renderer: control ``01 0C`` calls
``$02:BCF6``, which reads a two-character race name from the table at
``$02:BC8E`` (26 entries, four bytes each: two Shift-JIS full-width chars).
The table is data-only, so patching it works for both the 65816 ROM path and
the native recomp.

Each entry in the JSON is::

    {"index": 2, "name": "T", "jp": "魔王", "en": "Tyrant"}

``name`` is encoded as full-width Shift-JIS and padded with the ideographic
space to the fixed four-byte slot (so a one-letter code becomes ``X ``).
Outputs are ROM-derived and must stay under decomp/build/ unless the caller
chooses another path. The BPS defaults to the resolved Japanese ROM.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from bps import create as bps_create  # noqa: E402
import fullwidth  # noqa: E402
from extract_messages import resolve_rom  # noqa: E402

DEFAULT_ROOT = HERE.parents[1]

BANK = 0x02
TABLE = 0xBC8E
COUNT = 26
SLOT = 4


def lorom_offset(bank: int, addr: int) -> int:
    return (bank & 0x7F) * 0x8000 + (addr - 0x8000)


def load_entries(path: pathlib.Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("entries", [])
    if not isinstance(data, list):
        raise ValueError("race JSON must be a list or {'entries': [...]}")
    return data


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", help="input ROM; defaults to SNESRECOMP_ROM/rom.cfg")
    ap.add_argument("--base-rom", help="ROM for the BPS diff; defaults to --rom")
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--translations", default="translations/races_en.json")
    ap.add_argument("--out", help="output ROM (default: build/rom/races_en.sfc)")
    ap.add_argument("--patch", help="optional BPS output path")
    ap.add_argument("--patch-name", default="Kyuuyaku Megami Tensei English race names")
    ap.add_argument("--report", help="optional JSON report path")
    args = ap.parse_args()

    root = pathlib.Path(args.root)
    rom_path = pathlib.Path(args.rom) if args.rom else resolve_rom(None, root)
    if rom_path is None or not rom_path.is_file():
        print("no input ROM found; pass --rom", file=sys.stderr)
        return 1
    if args.base_rom:
        base_path = pathlib.Path(args.base_rom)
    else:
        base_path = resolve_rom(None, root) or rom_path
    if not base_path.is_file():
        print(f"base ROM not found: {base_path}", file=sys.stderr)
        return 1

    rom = rom_path.read_bytes()
    base_rom = base_path.read_bytes()
    if len(rom) != len(base_rom):
        print("input and base ROM sizes differ", file=sys.stderr)
        return 1

    entries = load_entries(pathlib.Path(args.translations))
    out = bytearray(rom)
    report = []
    seen: set[int] = set()
    for entry in entries:
        index = int(entry["index"])
        if not (0 <= index < COUNT):
            print(f"error: race index out of range: {index}", file=sys.stderr)
            return 1
        if index in seen:
            print(f"error: duplicate race index: {index}", file=sys.stderr)
            return 1
        seen.add(index)
        name = str(entry["name"])
        encoded = fullwidth.encode(name, SLOT)
        offset = lorom_offset(BANK, TABLE + index * SLOT)
        old = bytes(out[offset : offset + SLOT])
        out[offset : offset + SLOT] = encoded
        report.append(
            {
                "index": index,
                "name": name,
                "jp": entry.get("jp", ""),
                "en": entry.get("en", ""),
                "old_hex": old.hex(),
                "new_hex": encoded.hex(),
            }
        )

    out_path = pathlib.Path(args.out) if args.out else root / "decomp" / "build" / "rom" / "races_en.sfc"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(out)
    print(f"wrote {out_path} ({len(out)} bytes)")

    if args.report:
        report_path = pathlib.Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(
                {"source": str(rom_path), "base": str(base_path), "entries": report},
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"wrote {report_path}")

    if args.patch:
        patch_path = pathlib.Path(args.patch)
        patch_path.parent.mkdir(parents=True, exist_ok=True)
        metadata = json.dumps(
            {"name": args.patch_name, "encoding": "shift_jis/fullwidth"},
            ensure_ascii=False,
        ).encode("utf-8")
        patch_path.write_bytes(bps_create(base_rom, bytes(out), metadata))
        print(f"wrote {patch_path} ({patch_path.stat().st_size} bytes)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
