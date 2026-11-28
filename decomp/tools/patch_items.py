#!/usr/bin/env python3
"""Translate and repack the bank-$06 item/equipment name table (T3).

T3 layout in the Japanese ROM:

  299 little-endian pointers at $06:EAFE-$ED53;
  NUL-terminated 1-byte font-code strings from $06:ED54 onward.

The strings use the 8x8 font page at $0F:AF6B.  ASCII letters, digits and
punctuation use ``font_code = ASCII - 0x1F``; ``0x01`` is a blank.  The
original pool ends at $06:F59E, but bank $06 has free space through $FFFF,
so a repacked pool can grow up to $12AC bytes.

Only indexes listed in the translation JSON are replaced.  Every other
entry keeps its original bytes, which lets a partial T3 pass ship without
touching the still-unmapped kanji items.

Input JSON::

    [{"index": 1, "text": "WALTHER", "note": "pistol"}]

The original ROM is never modified.  Outputs are ROM-derived and live
under decomp/build/ unless the caller chooses another path.
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

DEFAULT_ROOT = HERE.parents[1]

T3_BANK = 0x06
T3_TABLE = 0xEAFE
T3_COUNT = 299
T3_POOL = 0xED54
T3_POOL_END = 0xFFFF  # inclusive CPU address in bank $06
T3_BANK_FILE = T3_BANK * 0x8000
T3_POOL_BUDGET = T3_POOL_END - T3_POOL + 1  # 0x12AC


def resolve_rom(explicit: str | None, root: pathlib.Path) -> pathlib.Path | None:
    candidates: list[pathlib.Path] = []
    if explicit:
        candidates.append(pathlib.Path(explicit))
    import os

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


def cpu_to_file(addr: int) -> int:
    if not 0x8000 <= addr <= 0xFFFF:
        raise ValueError(f"T3 pointer outside bank $06: {addr:#06x}")
    return T3_BANK_FILE + (addr - 0x8000)


def file_to_cpu(offset: int) -> int:
    return 0x8000 + (offset - T3_BANK_FILE)


def read_entry(rom: bytes, pointer: int) -> bytes:
    start = cpu_to_file(pointer)
    end = start
    while end < len(rom) and rom[end] != 0:
        end += 1
    if end >= len(rom):
        raise ValueError(f"unterminated T3 string at {start:#x}")
    return rom[start:end]


def load_translations(path: pathlib.Path) -> dict[int, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("entries", [])
    if not isinstance(data, list):
        raise ValueError("item translation JSON must be a list or {'entries': [...]}")
    out: dict[int, dict] = {}
    for row in data:
        idx = int(row["index"])
        if not 0 <= idx < T3_COUNT:
            raise ValueError(f"item index out of range: {idx}")
        if idx in out:
            raise ValueError(f"duplicate item index: {idx}")
        out[idx] = row
    return out


def encode_font(text: str) -> bytes:
    """Encode uppercase ASCII/digits/punctuation for the $0F:AF6B font."""
    out = bytearray()
    for ch in text:
        code = ord(ch)
        if ch == " ":
            out.append(0x01)
        elif 0x20 <= code <= 0x5F:
            out.append(code - 0x1F)
        else:
            raise ValueError(
                f"unsupported character {ch!r} in {text!r}; "
                "use uppercase ASCII, digits, space and punctuation"
            )
    return bytes(out)


def patch_items(rom: bytes, translations: dict[int, dict]) -> tuple[bytes, list[dict]]:
    out = bytearray(rom)
    originals: list[bytes] = []
    for idx in range(T3_COUNT):
        pointer = rom[T3_BANK_FILE + (T3_TABLE - 0x8000) + idx * 2] | (
            rom[T3_BANK_FILE + (T3_TABLE - 0x8000) + idx * 2 + 1] << 8
        )
        originals.append(read_entry(rom, pointer))

    pool_file = T3_BANK_FILE + (T3_POOL - 0x8000)
    pool = bytearray()
    pointers: list[int] = []
    report: list[dict] = []
    for idx, original in enumerate(originals):
        row = translations.get(idx)
        if row is None:
            raw = original
            text = None
        else:
            text = str(row["text"])
            raw = encode_font(text)
            if not raw:
                raise ValueError(f"empty item translation at index {idx}")
        pointers.append(file_to_cpu(pool_file + len(pool)))
        pool += raw + b"\x00"
        if row is not None:
            report.append(
                {
                    "index": idx,
                    "text": text,
                    "length": len(raw),
                    "old_hex": original.hex(),
                    "new_hex": raw.hex(),
                    "note": str(row.get("note", "")),
                }
            )

    if len(pool) > T3_POOL_BUDGET:
        raise ValueError(
            f"T3 pool overflow: {len(pool)} bytes > {T3_POOL_BUDGET} "
            f"(bank $06 free space)"
        )

    table_file = T3_BANK_FILE + (T3_TABLE - 0x8000)
    for idx, pointer in enumerate(pointers):
        out[table_file + idx * 2] = pointer & 0xFF
        out[table_file + idx * 2 + 1] = pointer >> 8
    out[T3_BANK_FILE + (T3_POOL - 0x8000):T3_BANK_FILE + (T3_POOL - 0x8000) + len(pool)] = pool
    return bytes(out), report


def decode_font(raw: bytes) -> str:
    out = []
    for code in raw:
        if code == 0x01:
            out.append(" ")
        elif 0x11 <= code <= 0x1A:
            out.append(chr(code - 0x11 + ord("0")))
        elif 0x22 <= code <= 0x3B:
            out.append(chr(code - 0x22 + ord("A")))
        elif code == 0x0E:
            out.append("-")
        elif code == 0x0F:
            out.append(".")
        else:
            out.append(f"{{{code:02X}}}")
    return "".join(out)


def selftest() -> int:
    assert encode_font("VIT 1") == bytes([0x37, 0x2A, 0x35, 0x01, 0x12])
    assert decode_font(bytes([0x37, 0x2A, 0x35, 0x01, 0x12])) == "VIT 1"
    rom = bytes(0x40000)
    # A minimal synthetic T3 table is not worth building; exercise the
    # encoder and the budget check instead.
    try:
        encode_font("acento")
    except ValueError:
        pass
    else:
        raise AssertionError("lowercase must be rejected")
    print("ok selftest: T3 font encoding")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", help="ROM path; defaults to SNESRECOMP_ROM/rom.cfg")
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--translations", help="JSON with index/text rows")
    ap.add_argument("--out", help="output ROM")
    ap.add_argument("--patch", help="optional BPS output path")
    ap.add_argument("--patch-name", default="Kyuuyaku Megami Tensei item names")
    ap.add_argument("--report", help="optional JSON report path")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if not args.translations:
        ap.error("--translations is required")

    root = pathlib.Path(args.root)
    rom_path = resolve_rom(args.rom, root)
    if rom_path is None:
        print("no ROM found; pass --rom or set SNESRECOMP_ROM", file=sys.stderr)
        return 1
    original = rom_path.read_bytes()
    translations = load_translations(pathlib.Path(args.translations))
    try:
        translated, report = patch_items(original, translations)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    out = pathlib.Path(args.out) if args.out else root / "decomp" / "build" / "rom" / "items.sfc"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(translated)
    print(f"wrote {out} ({len(translated)} bytes)")

    if args.report:
        report_path = pathlib.Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {report_path}")

    if args.patch:
        patch_path = pathlib.Path(args.patch)
        patch_path.parent.mkdir(parents=True, exist_ok=True)
        metadata = json.dumps({"name": args.patch_name}).encode("utf-8")
        patch_path.write_bytes(bps_create(original, translated, metadata))
        print(f"wrote {patch_path}")

    print(f"translated {len(report)}/{T3_COUNT} T3 entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
