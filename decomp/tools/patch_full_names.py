#!/usr/bin/env python3
"""Add a full race prefix and full demon name to the battle intro.

The stock battle intro uses the 2-character race table at ``$02:BC8E`` and
the 8-character T1/T2 name copy at ``$02:C87B``. This tool installs a
battle-only path that reads full names from free space:

* ``$2E:BB38`` / ``$2E:BD32`` - full T1/T2 name pointer tables;
* ``$2F:B81F`` and ``$2F:F820`` - full name strings (mixed-case 8x8
  codes, mapped to Shift-JIS before display);
* ``$2E:BE50`` - full race pointer table;
* ``$2E:DF08`` - full race prefixes (8x8 uppercase font codes);
* ``$2E:DD08`` - 8x8 code -> full-width Shift-JIS map;
* ``$2E:BE90`` / ``$2E:BF00`` - 65816 race/name display routines.

The routines are assembled from ``tools/full-race.s`` and
``tools/full-name.s``. The race routine sets ``$7E:1FF0``; the name copy
uses the full table only when that flag is set, so ordinary ``<04>``
messages keep the eight-character names used by menus and status screens.

The full race prefix is drawn in 8x8 with ``$01E311``; the full name is mapped
through ``$2E:DD08`` and drawn in 16x16 with ``$01DFAD``, which gives the
dialogue font's lowercase Latin. The direct-page ``$57`` buffer and the
``$02:BADE`` loop patch remain for ordinary ``<04>`` messages (attack
lines, player names), which keep the eight-character T1/T2 names. The
result is e.g. ``FOUL Green Slime``.

This tool expects ``full_en.sfc`` (script + battle + races + names) as
input. The BPS is diffed against the original Japanese ROM.

Outputs are ROM-derived and must stay under decomp/build/ unless the
caller chooses another path.
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
from font_codec import encode as font_encode, encode_mixed  # noqa: E402
import fullwidth  # noqa: E402
from extract_messages import resolve_rom  # noqa: E402

DEFAULT_ROOT = HERE.parents[1]

FULL_T1_PTR = (0x2E, 0xBB38)
FULL_T2_PTR = (0x2E, 0xBD32)
RACE_PTR = (0x2E, 0xBE50)
RACE_CODE = (0x2E, 0xBE90)
NAME_CODE = (0x2E, 0xBF00)
FULLWIDTH_MAP = (0x2E, 0xDD08)
RACE_STRINGS = (0x2E, 0xDF08)
HOLES = ((0x2F, 0xB81F, 2017), (0x2F, 0xF820, 2016))

# Assembled from tools/full-race.s and tools/full-name.s. Refresh with:
#   wla-65816 -o /tmp/full-race.o tools/full-race.s
#   printf '[objects]\n/tmp/full-race.o\n' > /tmp/link && wlalink -i /tmp/link /tmp/full-race.sfc
# and take $3E90/$3F40 from the 32 KiB bank image (the .s files use .ORG
# $3E90/$3F40 because WLA-DX addresses the 32 KiB slot from zero).
RACE_CODE_BYTES = bytes.fromhex(
    "088b4babe230ad8c042275bf0248a9018ff01f7e680aaac220bf50be2ec210aae220bf00002ef023da2211e301fae220ad8902f013297f48ad2f0209108d2f0222979300683ad0f0e880d5ab286b"
)
NAME_CODE_BYTES = bytes.fromhex(
    "088b4babc230da5a29ff008500e220aff01f7ef075a9008ff01f7ea500c9fdb069ade80cd00fc220a5000aaabf38bb2ec210aa8015c220a5000aaae01c019003a21c01bf32bd2ec210aae220bf00002ff032c22029ff000aa8b908ddf023eb8500da22addf01fae220ad8902f013297f48ad2f0209108d2f0222979300683ad0f0e880c8a90085578017c230a500227bc802e220a20000b5229557e8e00900d0f6c2107afaab286b"
)

# (file offset, expected bytes, replacement)
CODE_PATCHES = (
    (0x013ADA, bytes.fromhex("227bc802"), bytes.fromhex("2200bf2e")),
    (0x013AE3, bytes.fromhex("b522"), bytes.fromhex("b557")),
    (0x013AE7, bytes.fromhex("c901f021"), bytes.fromhex("eaeaeaea")),
    (0x013231, bytes.fromhex("22f6bc02"), bytes.fromhex("2290be2e")),
    (0x0188AA, bytes.fromhex("22f6bc02"), bytes.fromhex("2290be2e")),
)


def lorom_offset(bank: int, addr: int) -> int:
    return (bank & 0x7F) * 0x8000 + (addr - 0x8000)


def load_entries(path: pathlib.Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("entries", [])
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a list or {{'entries': [...]}}")
    return data


def check_zero(rom: bytes, bank: int, addr: int, length: int, label: str) -> None:
    start = lorom_offset(bank, addr)
    blob = rom[start : start + length]
    if len(blob) != length:
        raise ValueError(f"{label}: range exceeds ROM")
    if any(blob):
        first = next(i for i, byte in enumerate(blob) if byte)
        raise ValueError(f"{label}: target is not zero at {bank:02X}:{addr + first:04X}")


def pack_names(entries: list[dict]) -> tuple[list[int], list[tuple[int, int, bytes]], list[dict]]:
    by_table: dict[str, dict[int, dict]] = {"t1": {}, "t2": {}}
    for entry in entries:
        table = str(entry["table"]).lower()
        if table not in by_table:
            raise ValueError(f"unknown name table: {table}")
        by_table[table][int(entry["index"])] = entry

    holes = list(HOLES)
    hole_index = 0
    cursor = holes[0][1]
    strings: list[tuple[int, int, bytes]] = []
    pointers: list[int] = []
    report: list[dict] = []

    for table, count in (("t1", 253), ("t2", 143)):
        if len(by_table[table]) != count:
            raise ValueError(f"{table} has {len(by_table[table])} entries, want {count}")
        for index in range(count):
            entry = by_table[table][index]
            text = str(entry.get("en") or entry.get("name") or "").strip()
            if not text:
                raise ValueError(f"{table}[{index}] has no English name")
            encoded = encode_mixed(text) + b"\x00"
            if len(encoded) > 16:
                raise ValueError(f"{table}[{index}] {text!r} is {len(encoded)} bytes, max 16")
            bank, base, size = holes[hole_index]
            if cursor + len(encoded) > base + size:
                hole_index += 1
                if hole_index >= len(holes):
                    raise ValueError("full names do not fit in the free bank $2F holes")
                bank, base, size = holes[hole_index]
                cursor = base
            pointers.append(cursor)
            strings.append((bank, cursor, encoded))
            report.append(
                {
                    "table": table,
                    "index": index,
                    "text": text,
                    "bank": bank,
                    "addr": f"{cursor:04X}",
                    "length": len(encoded) - 1,
                }
            )
            cursor += len(encoded)
    return pointers, strings, report


def pack_races(entries: list[dict]) -> tuple[list[int], list[tuple[int, bytes]], list[dict]]:
    by_index = {int(entry["index"]): entry for entry in entries}
    bank, cursor = RACE_STRINGS
    end = 0xE000
    pointers: list[int] = []
    strings: list[tuple[int, bytes]] = []
    report: list[dict] = []
    for index in range(26):
        entry = by_index.get(index)
        text = str(entry.get("en") or "") if entry else ""
        if text:
            text = text.upper() + " "  # full 8x8 race prefix + separator
        encoded = font_encode(text) + b"\x00"
        if cursor + len(encoded) > end:
            raise ValueError("full race strings do not fit in $2E:DF08-$E000")
        pointers.append(cursor)
        strings.append((cursor, encoded))
        report.append(
            {
                "index": index,
                "text": text,
                "jp": entry.get("jp", "") if entry else "",
                "addr": f"{cursor:04X}",
                "length": len(encoded) - 1,
            }
        )
        cursor += len(encoded)
    return pointers, strings, report


def pointer_blob(pointers: list[int]) -> bytes:
    return b"".join(pointer.to_bytes(2, "little") for pointer in pointers)

def fullwidth_map_blob() -> bytes:
    """Map 8x8 name codes to full-width Shift-JIS for the dialogue font."""
    out = bytearray()
    for code in range(256):
        if code == 0x01:
            char = " "
        elif 0x02 <= code <= 0x40:
            char = chr(code + 0x1F)
        elif 0x41 <= code <= 0x5A:
            char = chr(code + 0x20)
        else:
            out += b"\x00\x00"
            continue
        out += fullwidth.encode(char, 2)
    if len(out) != 512:
        raise ValueError(f"fullwidth map is {len(out)} bytes, want 512")
    return bytes(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", help="input ROM (normally full_en.sfc)")
    ap.add_argument("--base-rom", help="ROM for the BPS diff; defaults to the original")
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--names", default="translations/names_en.json")
    ap.add_argument("--races", default="translations/races_en.json")
    ap.add_argument("--out", help="output ROM (default: build/rom/full_names.sfc)")
    ap.add_argument("--patch", help="optional BPS output path")
    ap.add_argument("--patch-name", default="Kyuuyaku Megami Tensei English full-name battle intro")
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

    original = rom_path.read_bytes()
    base_rom = base_path.read_bytes()
    if len(original) != len(base_rom):
        print("input and base ROM sizes differ", file=sys.stderr)
        return 1
    out = bytearray(original)

    names = load_entries(pathlib.Path(args.names))
    races = load_entries(pathlib.Path(args.races))

    # Verify free space before writing anything.
    check_zero(original, *FULL_T1_PTR, 0x4A0, "full-name tables/code")
    check_zero(original, *FULLWIDTH_MAP, 512, "fullwidth map")
    check_zero(original, *RACE_STRINGS, 0xE000 - RACE_STRINGS[1], "full race strings")
    for bank, addr, size in HOLES:
        check_zero(original, bank, addr, size, f"full-name hole ${bank:02X}:{addr:04X}")

    for offset, expected, _ in CODE_PATCHES:
        actual = original[offset : offset + len(expected)]
        if actual != expected:
            print(
                f"unexpected bytes at {offset:#x}: {actual.hex()} (want {expected.hex()})",
                file=sys.stderr,
            )
            return 1

    t1_pointers, name_strings, name_report = pack_names(names)
    race_pointers, race_strings, race_report = pack_races(races)

    def write(bank: int, addr: int, data: bytes) -> None:
        start = lorom_offset(bank, addr)
        out[start : start + len(data)] = data

    write(*FULL_T1_PTR, pointer_blob(t1_pointers[:253]))
    write(*FULL_T2_PTR, pointer_blob(t1_pointers[253:]))
    write(*RACE_PTR, pointer_blob(race_pointers))
    write(*FULLWIDTH_MAP, fullwidth_map_blob())
    for bank, addr, data in name_strings:
        write(bank, addr, data)
    for addr, data in race_strings:
        write(RACE_STRINGS[0], addr, data)
    write(*RACE_CODE, RACE_CODE_BYTES)
    write(*NAME_CODE, NAME_CODE_BYTES)

    for offset, _, replacement in CODE_PATCHES:
        out[offset : offset + len(replacement)] = replacement

    out_path = pathlib.Path(args.out) if args.out else root / "decomp" / "build" / "rom" / "full_names.sfc"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(out)
    print(f"wrote {out_path} ({len(out)} bytes)")

    if args.report:
        report_path = pathlib.Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(
                {
                    "source": str(rom_path),
                    "base": str(base_path),
                    "full_name_holes": [
                        {"bank": bank, "addr": f"{addr:04X}", "size": size}
                        for bank, addr, size in HOLES
                    ],
                    "names": name_report,
                    "races": race_report,
                    "code_patches": [
                        {"offset": f"{offset:06X}", "old": old.hex(), "new": new.hex()}
                        for offset, old, new in CODE_PATCHES
                    ],
                    "fullwidth_map": {
                        "bank": FULLWIDTH_MAP[0],
                        "addr": f"{FULLWIDTH_MAP[1]:04X}",
                        "bytes": 512,
                    },
                },
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
            {"name": args.patch_name, "encoding": "8x8-font/full-name-battle"},
            ensure_ascii=False,
        ).encode("utf-8")
        patch_path.write_bytes(bps_create(base_rom, bytes(out), metadata))
        print(f"wrote {patch_path} ({patch_path.stat().st_size} bytes)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
