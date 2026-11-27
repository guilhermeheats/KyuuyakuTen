#!/usr/bin/env python3
"""Repack the bank-$11 battle message pool into free space in bank $29.

The battle message table is a 144-entry pointer table at ``$11:A5A4`` in
the Japanese ROM. Each pointer targets a message in ``$11:A6C6-$B13D``.
Messages mix Shift-JIS text with one-byte control codes and two-byte
``01 xx`` commands. The display routine follows the pointer and stops at
the message terminator, so the pool can be repacked as long as every table
entry is updated.

The original pool is only 2679 bytes and is almost full. This tool moves
the table and messages to free space in bank ``$29`` and patches the
battle-message setup at ``$01:A9B0``/``$01:A9C0`` to use the new bank and
table. A second reader at ``$01:A9E5`` does not set ``$44``, so a small
wrapper at ``$2E:C000`` sets the bank and jumps back to ``$01:A9EC`` while
preserving the message index in A. The messages are packed into two free
holes in bank $29:

* ``$29:B940-$BFFF`` (after the new 288-byte table at ``$29:B820``);
* ``$29:F820-$FFFF``.

Input JSON is a list of entries::

    {"index": 11, "runs": ["'s attack"], "jp": "の攻撃", "en": "'s attack"}

``runs`` replaces the text runs of the message in order. Control and raw
bytes are kept byte-for-byte; only the text between them is replaced. The
number of runs must match the original message. Messages without an entry
keep the bytes from ``--rom``. An optional ``insert`` object inserts raw
control bytes at a byte offset after the runs are rebuilt, e.g.
``{"at": 2, "bytes": "0F"}`` to put a line break after the race command.

Apply this after ``script_en.json`` so the existing in-place battle
translations are carried into the repacked pool. The output BPS is built
against ``--base-rom``, defaulting to the resolved Japanese ROM.

With ``--encoding byte`` the text runs are written as one ASCII byte per
character. A small codec at ``$11:A6C6`` expands each byte through a
full-width table at ``$11:A740`` and reuses the stock glyph writer, so the
pool can hold roughly twice as much text. A dispatcher at ``$11:A6E6``
checks the current message pointer (``$42/$43``) and bank (``$44``): only
pointers inside the repacked battle holes (``$29:B940-$BFFF`` and
``$29:F820-$FFFF``) use the codec; COMP, story and menu text keep the stock
two-byte path. All codec code/data lives in the old bank-$11 battle pool
(``$A6C6-$B13D``), which was message data, not dialogue-font source. The
codec saves and restores X, calls ``$01:DFAD``, and then resumes the stock
``$02:B037`` continuation. The stock path is reproduced exactly: it reads
the second byte, calls the glyph writer, increments the pointer, and jumps
to ``$02:B037``. The 1-byte path only skips the extra second-byte increment
because ``$02:B01B`` already consumed its byte. ``$02:B027`` is replaced by a
``JML`` (not ``JSL``), so the dispatcher owns the continuation and no return
frame leaks on the stack. This mode is intended for PT-BR and for future
lowercase support; it patches ``$02:B027`` and must be regenerated for the
AOT build. Lowercase is folded to uppercase until a lowercase 8x8 page is
installed.

Outputs are ROM-derived and must stay under decomp/build/ unless the caller
chooses another path.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import OrderedDict

HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from bps import create as bps_create  # noqa: E402
import fullwidth  # noqa: E402
from extract_messages import resolve_rom, text_run_length  # noqa: E402

DEFAULT_ROOT = HERE.parents[1]

# Original table/pool in the Japanese ROM.
BANK = 0x11
TABLE_ADDR = 0xA5A4
COUNT = 144
POOL_START = 0xA6C6
POOL_END = 0xB13D

# New table and message holes in bank $29.
DST_BANK = 0x29
DST_TABLE_ADDR = 0xB820
DST_TABLE_SIZE = COUNT * 2
DST_HOLES_FULL = (
    (DST_TABLE_ADDR + DST_TABLE_SIZE, 0xC000),
    (0xF820, 0x10000),
)
# The 1-byte codec uses the old bank-$11 message pool, so the battle text
# still goes in the same bank-$29 holes.
DST_HOLES_BYTE = DST_HOLES_FULL
DST_HOLES = DST_HOLES_FULL

# LLE wrapper at $2E:C000: the A9E5 entry does not set $44 itself, so the
# wrapper sets the message bank to $29 before continuing at $01:A9EC. A is
# the message index at entry, so it is saved/restored around the LDA #$29.
DST_WRAPPER = (0x2E, 0xC000)
DST_WRAPPER_BYTES = bytes.fromhex(
    "08e220c210da5a48a9298544685ceca901"
)

# (file offset, expected bytes, replacement)
CODE_PATCHES = (
    (0x00A9B0, bytes.fromhex("a911"), bytes.fromhex("a929")),
    (0x00A9C0, bytes.fromhex("69a4a5"), bytes.fromhex("6920b8")),
    (0x00A9E5, bytes.fromhex("08e220c2"), bytes.fromhex("5c00c02e")),
    (0x00A9F3, bytes.fromhex("69a4a5"), bytes.fromhex("6920b8")),
)

# 1-byte text codec in the old bank-$11 battle pool. The code maps ASCII
# 0x20-0x7F to a full-width Shift-JIS pair in the table and reuses the stock
# $01:DFAD glyph writer, so the pool stores one byte per char.
BYTE_BANK = 0x11
BYTE_CODE_ADDR = 0xA6C6
BYTE_TABLE_ADDR = 0xA740
BYTE_TABLE_SIZE = 0x60 * 2
BYTE_CODE_BYTES = bytes.fromhex(
    "da38e9200aaabf40a7118501bf41a7118500fa22addf015c37b002"
)
BYTE_DISPATCH_ADDR = 0xA6E6
BYTE_DISPATCH_BYTES = bytes.fromhex(
    "48a544c929d00ea543c9b99004c9c09019c9f8b015688501a742850022addf01e642d002e6435c37b002685cc6a611"
)
BYTE_PATCH_OFFSET = 0x013027
BYTE_PATCH_EXPECTED = bytes.fromhex("8501a742850022addf01")
BYTE_PATCH_REPLACEMENT = bytes.fromhex("5ce6a611eaeaeaeaeaea")
if len(BYTE_PATCH_REPLACEMENT) != len(BYTE_PATCH_EXPECTED):
    raise ValueError("byte codec patch must preserve the interpreter window")

TEXT_ENCODING = "fullwidth"


def lorom_offset(bank: int, addr: int) -> int:
    return (bank & 0x7F) * 0x8000 + (addr - 0x8000)


def load_entries(path: pathlib.Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("entries", [])
    if not isinstance(data, list):
        raise ValueError("battle JSON must be a list or {'entries': [...]}")
    return data


def split_message(raw: bytes) -> list[tuple[str, bytes]]:
    """Split a message into ('text'|'raw', bytes) runs, preserving all bytes."""
    segments: list[tuple[str, bytes]] = []
    i = 0
    while i < len(raw):
        if raw[i] >= 0x20:
            length = text_run_length(raw, i, len(raw))
            if length:
                segments.append(("text", raw[i : i + length]))
                i += length
                continue
        segments.append(("raw", raw[i : i + 1]))
        i += 1
    return segments


def decode_text(raw: bytes) -> str:
    try:
        return raw.decode("shift_jis")
    except UnicodeDecodeError as exc:
        raise ValueError(f"text run is not valid Shift-JIS: {raw.hex()}") from exc


def encode_text(text: str) -> bytes:
    if TEXT_ENCODING == "byte":
        try:
            return text.upper().encode("ascii")
        except UnicodeEncodeError as exc:
            raise ValueError(
                f"1-byte battle text only supports ASCII: {text!r}"
            ) from exc
    return fullwidth.encode(text)


def apply_entry(index: int, raw: bytes, entry: dict) -> bytes:
    runs = entry.get("runs")
    if not isinstance(runs, list):
        raise ValueError(f"battle[{index}] needs a 'runs' list")
    segments = split_message(raw)
    text_segments = [bytes for kind, bytes in segments if kind == "text"]
    if len(runs) != len(text_segments):
        raise ValueError(
            f"battle[{index}] has {len(text_segments)} text run(s), "
            f"but the translation supplies {len(runs)}"
        )
    out = bytearray()
    text_index = 0
    for kind, data in segments:
        if kind == "raw":
            out += data
            continue
        text = str(runs[text_index])
        encoded = encode_text(text)
        out += encoded
        text_index += 1
    insert = entry.get("insert")
    if insert:
        at = int(insert["at"])
        data = bytes.fromhex(str(insert["bytes"]))
        if not (0 <= at <= len(out)):
            raise ValueError(f"battle[{index}] insert offset out of range: {at}")
        out[at:at] = data
    return bytes(out)


def allocate_blob(
    blob: bytes,
    blob_offsets: OrderedDict[bytes, int],
    hole_index: int,
    cursor: int,
) -> tuple[int, int, int]:
    """Return (offset, hole_index, cursor) for a blob in the bank-$29 holes."""
    offset = blob_offsets.get(blob)
    if offset is not None:
        return offset, hole_index, cursor

    while hole_index < len(DST_HOLES):
        hole_start, hole_end = DST_HOLES[hole_index]
        if cursor < hole_start:
            cursor = hole_start
        if cursor + len(blob) <= hole_end:
            offset = cursor
            blob_offsets[blob] = offset
            cursor += len(blob)
            return offset, hole_index, cursor
        hole_index += 1
        if hole_index < len(DST_HOLES):
            cursor = DST_HOLES[hole_index][0]

    raise ValueError(
        "translated battle pool does not fit in the bank-$29 holes "
        f"({sum(end - start for start, end in DST_HOLES)} bytes)"
    )


def build_pool(
    rom: bytes, entries: list[dict]
) -> tuple[list[int], OrderedDict[bytes, int], int, list[dict]]:
    base = lorom_offset(BANK, TABLE_ADDR)
    pointers = []
    for index in range(COUNT):
        offset = base + index * 2
        target = rom[offset] | (rom[offset + 1] << 8)
        if not (POOL_START <= target <= POOL_END):
            raise ValueError(f"battle pointer {index} is outside the pool: {target:04X}")
        pointers.append(target)

    by_index = {int(entry["index"]): entry for entry in entries}
    if len(by_index) != len(entries):
        raise ValueError("duplicate battle message index")

    messages: list[bytes] = []
    translated: list[dict] = []
    for index, target in enumerate(pointers):
        end = pointers[index + 1] if index + 1 < COUNT else POOL_END
        if end < target:
            raise ValueError(f"battle pointer {index} is not monotonic")
        start_file = lorom_offset(BANK, target)
        end_file = lorom_offset(BANK, end)
        raw = rom[start_file:end_file]
        entry = by_index.get(index)
        if entry is not None:
            new = apply_entry(index, raw, entry)
            translated.append(
                {
                    "index": index,
                    "pointer": f"{target:04X}",
                    "old_length": len(raw),
                    "new_length": len(new),
                    "runs": entry["runs"],
                    "jp": entry.get("jp", ""),
                    "en": entry.get("en", ""),
                }
            )
        else:
            new = raw
        messages.append(new)

    # Allocate non-empty messages in table order, deduplicating exact blobs.
    # Empty entries point at the next non-empty message, matching the original
    # table (some unused IDs share the following message's address).
    blob_offsets: OrderedDict[bytes, int] = OrderedDict()
    new_pointers = [0] * COUNT
    hole_index = 0
    cursor = DST_HOLES[0][0]
    used = 0
    for index, blob in enumerate(messages):
        if not blob:
            continue
        offset, hole_index, cursor = allocate_blob(
            blob, blob_offsets, hole_index, cursor
        )
        used += len(blob)
        new_pointers[index] = offset

    next_pointer = DST_HOLES[0][0]
    for index in range(COUNT - 1, -1, -1):
        blob = messages[index]
        if blob:
            next_pointer = new_pointers[index]
        else:
            new_pointers[index] = next_pointer

    return new_pointers, blob_offsets, used, translated


def build_byte_table() -> bytes:
    """Return 96 full-width Shift-JIS pairs for ASCII 0x20-0x7F.

    Lowercase input is folded to uppercase because the stock 8x8 page has no
    lowercase glyphs. The table stores [first byte, second byte] per code.
    """
    table = bytearray()
    for code in range(0x20, 0x80):
        char = chr(code)
        if "a" <= char <= "z":
            char = char.upper()
        if code == 0x7F:
            char = " "
        encoded = fullwidth.encode(char)
        if len(encoded) != 2:
            raise ValueError(
                f"byte table code {code:#x} ({char!r}) is not 2 bytes"
            )
        table += encoded
    if len(table) != BYTE_TABLE_SIZE:
        raise ValueError(f"byte table is {len(table)} bytes, want {BYTE_TABLE_SIZE}")
    return bytes(table)


def install_byte_codec(out: bytearray, rom: bytes) -> None:
    code_start = lorom_offset(BYTE_BANK, BYTE_CODE_ADDR)
    table_start = lorom_offset(BYTE_BANK, BYTE_TABLE_ADDR)
    end = table_start + BYTE_TABLE_SIZE
    # Bank $11 is the old battle message pool, now unused; its bytes are
    # the original messages, so no zero check here.
    if BYTE_BANK != 0x11 and any(rom[code_start:end]):
        raise ValueError(
            f"byte codec target ${BYTE_BANK:02X}:{BYTE_CODE_ADDR:04X}-"
            f"${BYTE_TABLE_ADDR + BYTE_TABLE_SIZE:04X} is not zero"
        )
    if rom[BYTE_PATCH_OFFSET : BYTE_PATCH_OFFSET + len(BYTE_PATCH_EXPECTED)] != BYTE_PATCH_EXPECTED:
        raise ValueError(
            f"unexpected bytes at {BYTE_PATCH_OFFSET:#x}: "
            f"{rom[BYTE_PATCH_OFFSET:BYTE_PATCH_OFFSET + len(BYTE_PATCH_EXPECTED)].hex()} "
            f"(want {BYTE_PATCH_EXPECTED.hex()})"
        )
    out[code_start : code_start + len(BYTE_CODE_BYTES)] = BYTE_CODE_BYTES
    dispatch_start = lorom_offset(BYTE_BANK, BYTE_DISPATCH_ADDR)
    out[dispatch_start : dispatch_start + len(BYTE_DISPATCH_BYTES)] = (
        BYTE_DISPATCH_BYTES
    )
    out[table_start:end] = build_byte_table()
    out[
        BYTE_PATCH_OFFSET : BYTE_PATCH_OFFSET + len(BYTE_PATCH_REPLACEMENT)
    ] = BYTE_PATCH_REPLACEMENT


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", help="input ROM (normally script_en.sfc)")
    ap.add_argument("--base-rom", help="ROM for the BPS diff; defaults to --rom")
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--translations", default="translations/battle_en.json")
    ap.add_argument(
        "--encoding",
        choices=("fullwidth", "byte"),
        default="fullwidth",
        help="fullwidth: 2-byte Shift-JIS; byte: 1-byte ASCII via $11 codec",
    )
    ap.add_argument("--out", help="output ROM (default: build/rom/script_battle_en.sfc)")
    ap.add_argument("--patch", help="optional BPS output path")
    ap.add_argument("--patch-name", default="Kyuuyaku Megami Tensei English battle text")
    ap.add_argument("--report", help="optional JSON report path")
    args = ap.parse_args()

    global TEXT_ENCODING, DST_HOLES
    TEXT_ENCODING = args.encoding
    DST_HOLES = DST_HOLES_BYTE if TEXT_ENCODING == "byte" else DST_HOLES_FULL

    root = pathlib.Path(args.root)
    rom_path = pathlib.Path(args.rom) if args.rom else None
    if rom_path is None:
        rom_path = resolve_rom(None, root)
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

    for offset, expected, _ in CODE_PATCHES:
        actual = rom[offset : offset + len(expected)]
        if actual != expected:
            print(
                f"unexpected bytes at {offset:#x}: {actual.hex()} (want {expected.hex()})",
                file=sys.stderr,
            )
            return 1

    entries = load_entries(pathlib.Path(args.translations))
    try:
        pointers, blob_offsets, pool_used, translated = build_pool(rom, entries)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    out = bytearray(rom)
    table_file = lorom_offset(DST_BANK, DST_TABLE_ADDR)
    for index, pointer in enumerate(pointers):
        out[table_file + index * 2] = pointer & 0xFF
        out[table_file + index * 2 + 1] = pointer >> 8
    for blob, offset in blob_offsets.items():
        start = lorom_offset(DST_BANK, offset)
        out[start : start + len(blob)] = blob

    wrapper_start = lorom_offset(*DST_WRAPPER)
    if any(rom[wrapper_start : wrapper_start + len(DST_WRAPPER_BYTES)]):
        print("battle wrapper target $2E:C000 is not zero", file=sys.stderr)
        return 1
    out[wrapper_start : wrapper_start + len(DST_WRAPPER_BYTES)] = DST_WRAPPER_BYTES

    for offset, _, replacement in CODE_PATCHES:
        out[offset : offset + len(replacement)] = replacement

    if TEXT_ENCODING == "byte":
        try:
            install_byte_codec(out, rom)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    out_path = pathlib.Path(args.out) if args.out else root / "decomp" / "build" / "rom" / "script_battle_en.sfc"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(out)
    print(f"wrote {out_path} ({len(out)} bytes)")

    pool_size = sum(end - start for start, end in DST_HOLES)
    report_payload = {
        "source": str(rom_path),
        "base": str(base_path),
        "encoding": TEXT_ENCODING,
        "table_bank": f"{DST_BANK:02X}",
        "table_addr": f"{DST_TABLE_ADDR:04X}",
        "holes": [
            {"start": f"{start:04X}", "end": f"{end:04X}", "size": end - start}
            for start, end in DST_HOLES
        ],
        "pool_size": pool_size,
        "pool_used": pool_used,
        "entries": translated,
    }
    if args.report:
        report_path = pathlib.Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report_payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {report_path}")

    if args.patch:
        patch_path = pathlib.Path(args.patch)
        patch_path.parent.mkdir(parents=True, exist_ok=True)
        metadata = json.dumps(
            {"name": args.patch_name, "encoding": "shift_jis/fullwidth + controls"},
            ensure_ascii=False,
        ).encode("utf-8")
        patch = bps_create(base_rom, bytes(out), metadata)
        patch_path.write_bytes(patch)
        print(f"wrote {patch_path} ({len(patch)} bytes)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
