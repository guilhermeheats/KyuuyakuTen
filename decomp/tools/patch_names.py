#!/usr/bin/env python3
"""Patch the T1/T2 demon-name tables with 8x8-font English names.

The original tables live in bank $11:
  T1 pointer table at $11:CDFD (253 entries)
  T2 pointer table at $11:D5A8 (143 entries)

Each pointer points to a NUL-terminated string of 8x8 font codes. The
battle/name code copies at most 8 bytes from that string, so names must fit
in eight characters. We repack the strings into the zero-filled free tail
of bank $2E and point the original code at the new tables:

  $2E:B820  T1 pointers (absolute addresses in $2E)
  $2E:BA1A  T2 pointers
  $2E:D1A0  names (NUL-terminated, packed)

The three long loads in the name copy routine are retargeted from bank $11
to bank $2E. No code in bank $2E exists; the target areas are verified to
be zero before writing.

Input JSON is a list of entries:
  {"table": "t1", "index": 0, "name": "DARKHERO", ...}
`name` is uppercased and encoded with the 8x8 font codec. `en`/`jp` are
kept for report/glossary purposes.

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
from font_codec import decode as font_decode, encode as font_encode  # noqa: E402
from replace_text import resolve_rom  # noqa: E402

DEFAULT_ROOT = HERE.parents[1]

T1_COUNT = 253
T2_COUNT = 143
T1_PTR = 0x2EB820
T2_PTR = 0x2EBA1A
NAMES = 0xD1A0
T1_PTR_FILE = 0x173820
T2_PTR_FILE = 0x173A1A
NAMES_FILE = 0x1751A0

CODE_PATCHES = (
    (0x0148BB, bytes.fromhex("bf fd cd 11"), bytes.fromhex("bf 20 b8 2e")),
    (0x0148C9, bytes.fromhex("bf a8 d5 11"), bytes.fromhex("bf 1a ba 2e")),
    (0x0148D3, bytes.fromhex("bf 00 00 11"), bytes.fromhex("bf 00 00 2e")),
)


def load_entries(path: pathlib.Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("entries", [])
    if not isinstance(data, list):
        raise ValueError("name JSON must be a list or {'entries': [...]}")
    return data


def build_tables(entries: list[dict]) -> tuple[bytes, bytes, bytes, list[dict]]:
    grouped = {"t1": {}, "t2": {}}
    for entry in entries:
        table = str(entry["table"]).lower()
        if table not in grouped:
            raise ValueError(f"unknown table: {table}")
        index = int(entry["index"])
        if index in grouped[table]:
            raise ValueError(f"duplicate {table} index {index}")
        grouped[table][index] = entry

    names = bytearray()
    report: list[dict] = []
    name_offsets: dict[tuple[str, int], int] = {}
    for table, count in (("t1", T1_COUNT), ("t2", T2_COUNT)):
        if len(grouped[table]) != count:
            raise ValueError(f"{table} has {len(grouped[table])} entries, want {count}")
        for index in range(count):
            entry = grouped[table][index]
            text = str(entry["name"]).strip().upper()
            if not text:
                raise ValueError(f"empty {table}[{index}]")
            encoded = font_encode(text)
            if len(encoded) > 8:
                raise ValueError(f"{table}[{index}] {text!r} is {len(encoded)} bytes, max 8")
            name_offsets[(table, index)] = len(names)
            names.extend(encoded)
            names.append(0)
            report.append(
                {
                    "table": table,
                    "index": index,
                    "name": text,
                    "pointer": f"{NAMES + name_offsets[(table, index)]:04X}",
                    "length": len(encoded),
                    "jp": entry.get("jp", ""),
                    "en": entry.get("en", ""),
                }
            )
    if len(names) > 0x10000 - (NAMES & 0xFFFF):
        raise ValueError("name blob does not fit in bank $2E")

    def pointer_blob(table: str, count: int) -> bytes:
        out = bytearray()
        for index in range(count):
            ptr = NAMES + name_offsets[(table, index)]
            out += ptr.to_bytes(2, "little")
        return bytes(out)

    return pointer_blob("t1", T1_COUNT), pointer_blob("t2", T2_COUNT), bytes(names), report


def load_slots(path: pathlib.Path) -> dict[tuple[str, int], tuple[int, int]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    tables = data.get("tables", {})
    slots: dict[tuple[str, int], tuple[int, int]] = {}
    for table in ("t1", "t2"):
        for entry in tables.get(table, []):
            offset = int(entry["file_offset"], 16)
            length = len(entry["codes"]) // 2
            slots[(table, int(entry["index"]))] = (offset, length)
    return slots


def apply_in_place(
    rom: bytes,
    entries: list[dict],
    slots: dict[tuple[str, int], tuple[int, int]],
) -> tuple[bytes, list[dict], list[dict]]:
    out = bytearray(rom)
    report: list[dict] = []
    conflicts: list[dict] = []
    seen: dict[int, tuple[str, int]] = {}
    by_key = {(str(e["table"]).lower(), int(e["index"])): e for e in entries}
    for key, (offset, slot) in sorted(slots.items(), key=lambda item: item[1][0]):
        if key not in by_key:
            raise ValueError(f"missing translation for {key[0]}[{key[1]}]")
        entry = by_key[key]
        if offset + slot >= len(out):
            raise ValueError(f"{key} out of ROM range")
        if out[offset + slot] != 0:
            raise ValueError(f"{key} slot at {offset:#x} is not NUL-terminated")
        text = str(entry["name"]).strip().upper()
        if not text:
            raise ValueError(f"empty {key[0]}[{key[1]}]")
        encoded = font_encode(text)
        limit = min(slot, 8)
        truncated = len(encoded) > limit
        if truncated:
            encoded = encoded[:limit]
        if not encoded:
            raise ValueError(f"{key[0]}[{key[1]}] has no encodable characters")
        if offset in seen and seen[offset] != key:
            conflicts.append({"offset": f"{offset:06X}", "kept": seen[offset], "also": key})
        seen[offset] = key
        old = bytes(out[offset : offset + slot])
        out[offset : offset + len(encoded)] = encoded
        out[offset + len(encoded)] = 0
        report.append(
            {
                "table": key[0],
                "index": key[1],
                "name": font_decode(encoded),
                "slot": slot,
                "pointer": f"{offset:06X}",
                "old_hex": old.hex(),
                "new_hex": bytes(out[offset : offset + slot]).hex(),
                "truncated": truncated,
                "jp": entry.get("jp", ""),
                "en": entry.get("en", ""),
            }
        )
    return bytes(out), report, conflicts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", help="input ROM; defaults to SNESRECOMP_ROM/rom.cfg")
    ap.add_argument("--base-rom", help="ROM for the BPS diff; defaults to --rom")
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--translations", default="translations/names_en.json")
    ap.add_argument("--in-place", action="store_true", help="rewrite the original T1/T2 strings instead of relocating")
    ap.add_argument("--original-names", default="build/text/names.json", help="names.json with T1/T2 slot offsets")
    ap.add_argument("--out", help="output ROM (default: build/rom/names_en.sfc)")
    ap.add_argument("--patch", help="optional BPS patch output path")
    ap.add_argument("--patch-name", default="Kyuuyaku Megami Tensei English names")
    ap.add_argument("--report", help="optional JSON report path")
    args = ap.parse_args()

    root = pathlib.Path(args.root)
    rom_path = resolve_rom(args.rom, root)
    if rom_path is None:
        print("no ROM found; pass --rom or set SNESRECOMP_ROM", file=sys.stderr)
        return 1
    entries = load_entries(pathlib.Path(args.translations))
    original = rom_path.read_bytes()
    base_rom = pathlib.Path(args.base_rom).read_bytes() if args.base_rom else original
    if len(base_rom) != len(original):
        print("input and base ROM sizes differ", file=sys.stderr)
        return 1

    if args.in_place:
        names_path = pathlib.Path(args.original_names)
        if not names_path.exists():
            names_path = root / "decomp" / args.original_names
        slots = load_slots(names_path)
        try:
            out, report, conflicts = apply_in_place(original, entries, slots)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        out_path = pathlib.Path(args.out) if args.out else root / "decomp" / "build" / "rom" / "names_inplace.sfc"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(out)
        print(f"wrote {out_path} ({len(out)} bytes)")
        if args.report:
            report_path = pathlib.Path(args.report)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "source": str(rom_path),
                "mode": "in-place",
                "entries": report,
                "conflicts": conflicts,
            }
            report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"wrote {report_path}")
        if args.patch:
            patch_path = pathlib.Path(args.patch)
            patch_path.parent.mkdir(parents=True, exist_ok=True)
            metadata = json.dumps(
                {"name": args.patch_name, "encoding": "8x8-font/inplace"},
                ensure_ascii=False,
            ).encode("utf-8")
            patch = bps_create(base_rom, out, metadata)
            patch_path.write_bytes(patch)
            print(f"wrote {patch_path} ({len(patch)} bytes)")
        return 0

    t1_ptr, t2_ptr, names, report = build_tables(entries)
    out = bytearray(original)
    if len(out) < NAMES_FILE + len(names):
        print("ROM is too small for the relocated name table", file=sys.stderr)
        return 1
    for offset, old, new in CODE_PATCHES:
        if original[offset : offset + len(old)] != old:
            print(f"unexpected bytes at {offset:#x}: {original[offset:offset+4].hex()}", file=sys.stderr)
            return 1
    used = T1_PTR_FILE + len(t1_ptr) + len(t2_ptr)
    if any(out[T1_PTR_FILE:used]) or any(out[NAMES_FILE : NAMES_FILE + len(names)]):
        print("target free space is not zero; refusing to overwrite", file=sys.stderr)
        return 1

    out[T1_PTR_FILE : T1_PTR_FILE + len(t1_ptr)] = t1_ptr
    out[T2_PTR_FILE : T2_PTR_FILE + len(t2_ptr)] = t2_ptr
    out[NAMES_FILE : NAMES_FILE + len(names)] = names
    code_report = []
    for offset, old, new in CODE_PATCHES:
        out[offset : offset + len(new)] = new
        code_report.append({"offset": f"{offset:06X}", "old": old.hex(), "new": new.hex()})

    out_path = pathlib.Path(args.out) if args.out else root / "decomp" / "build" / "rom" / "names_en.sfc"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(out)
    print(f"wrote {out_path} ({len(out)} bytes)")

    if args.report:
        report_path = pathlib.Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "source": str(rom_path),
            "t1_pointer_file": f"{T1_PTR_FILE:06X}",
            "t2_pointer_file": f"{T2_PTR_FILE:06X}",
            "names_file": f"{NAMES_FILE:06X}",
            "names_bytes": len(names),
            "code_patches": code_report,
            "entries": report,
        }
        report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {report_path}")

    if args.patch:
        patch_path = pathlib.Path(args.patch)
        patch_path.parent.mkdir(parents=True, exist_ok=True)
        metadata = json.dumps(
            {"name": args.patch_name, "encoding": "8x8-font/relocated"},
            ensure_ascii=False,
        ).encode("utf-8")
        patch = bps_create(base_rom, bytes(out), metadata)
        patch_path.write_bytes(patch)
        print(f"wrote {patch_path} ({len(patch)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
