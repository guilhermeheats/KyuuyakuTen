#!/usr/bin/env python3
"""Replace extracted text runs in the ROM and optionally build a BPS patch.

The first translation pass uses ASCII in place: Japanese text is Shift-JIS
(two bytes per full-width character) and ASCII is one byte per character, so
most lines fit in the original slot. Unused bytes are padded with spaces.
Control bytes themselves are never modified; only the selected text run is.

Input JSON (a list, or {"entries": [...]}):

    [{"offset": "80248", "length": 32, "text": "After a while, ..."}]

`offset` is the ROM file offset in hex. `length` is optional but strongly
recommended: when present the tool verifies the original slot size. With
--encoding sjis the replacement is encoded as Shift-JIS; with ascii (the
default) it must be plain ASCII; with font it is encoded for the 8x8 name
font page (`font_code = ASCII - 0x1F`, uppercase only); with fullwidth the
text is converted to full-width Shift-JIS (two bytes per character) and
padded with U+3000, which is what the dialogue renderer expects.

The original ROM is never modified. Outputs are ROM-derived and live under
decomp/build/ unless the caller chooses another path.
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
from font_codec import encode as font_encode  # noqa: E402
import fullwidth  # noqa: E402

DEFAULT_ROOT = HERE.parents[1]


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


def load_entries(path: pathlib.Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("entries", [])
    if not isinstance(data, list):
        raise ValueError("translation JSON must be a list or {'entries': [...]}")
    return data


def apply_entries(
    rom: bytes,
    entries: list[dict],
    encoding: str = "ascii",
    fill: int = 0x20,
) -> tuple[bytes, list[dict]]:
    out = bytearray(rom)
    report: list[dict] = []
    used: list[tuple[int, int]] = []
    for entry in entries:
        offset = int(str(entry["offset"]), 16)
        text = str(entry["text"])
        if offset < 0 or offset >= len(out):
            raise ValueError(f"offset out of range: {offset:#x}")
        for start, end in used:
            if start <= offset < end:
                raise ValueError(f"overlapping entries at {offset:#x}")
        declared = entry.get("length")
        if encoding == "fullwidth":
            if declared is not None:
                length = int(declared)
                encoded = fullwidth.encode(text, length)
            else:
                encoded = fullwidth.encode(text)
                length = len(encoded)
        else:
            encoded = font_encode(text) if encoding == "font" else text.encode(encoding)
            length = int(declared) if declared is not None else len(encoded)
        if length <= 0:
            raise ValueError(f"bad length at {offset:#x}")
        if len(encoded) > length:
            raise ValueError(
                f"text too long at {offset:#x}: {len(encoded)} bytes > {length} slot"
            )
        old = bytes(out[offset : offset + length])
        if encoding == "fullwidth":
            new = encoded
        else:
            new = encoded + bytes([fill]) * (length - len(encoded))
        out[offset : offset + length] = new
        used.append((offset, offset + length))
        report.append(
            {
                "offset": f"{offset:06X}",
                "length": length,
                "old_hex": old.hex(),
                "new_hex": bytes(out[offset : offset + length]).hex(),
                "text": text,
            }
        )
    return bytes(out), report


def selftest() -> int:
    rom = bytearray(b"\xff" * 0x1000)
    rom[0x100:0x110] = b"\x82\xb1\x82\xb1\x82\xcd\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    entries = [{"offset": "100", "length": 16, "text": "hello"}]
    out, report = apply_entries(bytes(rom), entries)
    expected = b"hello" + b" " * 11
    if out[0x100:0x110] != expected:
        print("FAIL selftest: padded bytes mismatch", file=sys.stderr)
        return 1
    if len(report) != 1 or report[0]["length"] != 16:
        print("FAIL selftest: report mismatch", file=sys.stderr)
        return 1
    # Font-code page: COMP -> 24 30 2E 31 (see font_codec.py).
    font_rom = bytearray(b"\x00" * 0x100)
    font_entries = [{"offset": "10", "length": 4, "text": "COMP"}]
    font_out, _ = apply_entries(bytes(font_rom), font_entries, encoding="font")
    if font_out[0x10:0x14] != bytes((0x24, 0x30, 0x2E, 0x31)):
        print("FAIL selftest: font encoding mismatch", file=sys.stderr)
        return 1
    # Full-width dialogue page: 26-byte slot, padded with U+3000.
    fw_rom = bytearray(b"\x00" * 0x100)
    fw_entries = [{"offset": "20", "length": 26, "text": "Which item?"}]
    fw_out, _ = apply_entries(bytes(fw_rom), fw_entries, encoding="fullwidth")
    if fw_out[0x20:0x3A] != fullwidth.encode("Which item?", 26):
        print("FAIL selftest: full-width encoding mismatch", file=sys.stderr)
        return 1
    print("ok selftest: in-place ASCII replacement and padding")
    print("ok selftest: font-code name replacement (COMP)")
    print("ok selftest: full-width dialogue replacement")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", help="ROM path; defaults to SNESRECOMP_ROM/rom.cfg")
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--translations", help="JSON file with replacement entries")
    ap.add_argument("--out", help="output ROM (default: decomp/build/rom/translated.sfc)")
    ap.add_argument("--patch", help="optional BPS patch output path")
    ap.add_argument("--encoding", choices=("ascii", "sjis", "font", "fullwidth"), default="ascii")
    ap.add_argument("--fill", default=None, help="padding byte in hex (default 20, or 01 for font)")
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
    entries = load_entries(pathlib.Path(args.translations))
    original = rom_path.read_bytes()
    fill = int(args.fill, 16) if args.fill is not None else (0x01 if args.encoding in ("font", "fullwidth") else 0x20)
    try:
        translated, report = apply_entries(
            original, entries, encoding=args.encoding, fill=fill
        )
    except (ValueError, UnicodeEncodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    out = pathlib.Path(args.out) if args.out else root / "decomp" / "build" / "rom" / "translated.sfc"
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
        metadata = json.dumps(
            {"name": "Kyuuyaku Megami Tensei text test", "encoding": args.encoding},
            ensure_ascii=False,
        ).encode("utf-8")
        patch = bps_create(original, translated, metadata)
        patch_path.write_bytes(patch)
        print(f"wrote {patch_path} ({len(patch)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
