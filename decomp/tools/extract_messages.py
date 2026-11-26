#!/usr/bin/env python3
"""Extract the bank $11 message pool with its control codes preserved.

The system-message pool in bank $11 is addressed by a 16-bit pointer table
at $11:$97C0. Each unique target starts a message that runs until the next
target (or the pool end). Messages mix Shift-JIS text with one-byte control
codes and two-byte ``01 xx`` commands, so a plain Shift-JIS dump loses the
structure. This tool splits every message into typed segments:

* ``text``    - printable Shift-JIS/ASCII run;
* ``control`` - ``01 xx`` command or a one-byte code such as ``0F``;
* ``raw``     - a byte that is neither (only seen in event-script blobs).

Outputs are ROM-derived and must stay under decomp/build/ (ignored by git).

Usage:
    python3 tools/extract_messages.py [--rom ROM] [--out build/text/messages.json]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[2]
BANK = 0x11
TABLE_ADDR = 0x97C0
POOL_END = 0xA5A4  # the next pointer table starts here


def lorom_offset(bank: int, addr: int) -> int:
    return (bank & 0x7F) * 0x8000 + (addr - 0x8000)


def resolve_rom(explicit: str | None, root: pathlib.Path) -> pathlib.Path | None:
    candidates: list[pathlib.Path] = []
    if explicit:
        candidates.append(pathlib.Path(explicit))
    env = __import__("os").environ.get("SNESRECOMP_ROM")
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


def is_sjis_lead(byte: int) -> bool:
    return 0x81 <= byte <= 0x9F or 0xE0 <= byte <= 0xFC


def is_sjis_trail(byte: int) -> bool:
    return 0x40 <= byte <= 0xFC and byte != 0x7F


def text_run_length(data: bytes, start: int, end: int) -> int:
    """Length of a printable Shift-JIS/ASCII run starting at ``start``."""
    i = start
    while i < end:
        byte = data[i]
        if is_sjis_lead(byte) and i + 1 < end and is_sjis_trail(data[i + 1]):
            i += 2
        elif 0x20 <= byte <= 0x7E:
            i += 1
        else:
            break
    return i - start


def split_segments(data: bytes, base: int, start: int, end: int) -> list[dict]:
    """Split bank-relative offsets [start, end) into typed segments."""
    segments: list[dict] = []
    i = start
    while i < end:
        byte = data[base + i]
        if byte >= 0x20:
            length = text_run_length(data, base + i, base + end)
            if length:
                raw = data[base + i : base + i + length]
                try:
                    text = raw.decode("shift_jis")
                except UnicodeDecodeError:
                    text = raw.decode("shift_jis", errors="replace")
                segments.append(
                    {
                        "kind": "text",
                        "addr": f"{(0x8000 + i) & 0xFFFF:04X}",
                        "file_offset": f"{base + i:06X}",
                        "length": length,
                        "text": text,
                    }
                )
                i += length
                continue
        if byte == 0x01 and i + 1 < end:
            code = data[base + i : base + i + 2]
            segments.append(
                {
                    "kind": "control",
                    "addr": f"{(0x8000 + i) & 0xFFFF:04X}",
                    "file_offset": f"{base + i:06X}",
                    "length": 2,
                    "code": code.hex(),
                }
            )
            i += 2
            continue
        segments.append(
            {
                "kind": "control" if byte < 0x20 else "raw",
                "addr": f"{(0x8000 + i) & 0xFFFF:04X}",
                "file_offset": f"{base + i:06X}",
                "length": 1,
                "code": f"{byte:02x}",
            }
        )
        i += 1
    return segments


def annotate(segments: list[dict]) -> str:
    parts: list[str] = []
    for segment in segments:
        if segment["kind"] == "text":
            parts.append(segment["text"])
        else:
            parts.append(f"<{segment['code'].upper()}>")
    return "".join(parts)


def read_table(data: bytes) -> list[tuple[int, int]]:
    base = lorom_offset(BANK, TABLE_ADDR)
    entries: list[tuple[int, int]] = []
    for index in range(0x400):
        offset = base + index * 2
        target = data[offset] | (data[offset + 1] << 8)
        # The table is not sorted (entries 4/5 point back to $9BFE/$9844),
        # so it ends at the first word that is not a pool pointer.
        if not (0x8000 <= target <= POOL_END):
            break
        entries.append((index, target))
    if not entries:
        raise ValueError("empty message pointer table")
    return entries


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", help="ROM path; defaults to SNESRECOMP_ROM/rom.cfg")
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    root = pathlib.Path(args.root)
    rom = resolve_rom(args.rom, root)
    if rom is None:
        print("no ROM found; pass --rom or set SNESRECOMP_ROM", file=sys.stderr)
        return 1
    data = rom.read_bytes()
    if len(data) < lorom_offset(BANK, POOL_END):
        print("ROM is too small for bank $11", file=sys.stderr)
        return 1

    entries = read_table(data)
    refs: dict[int, list[int]] = {}
    for index, target in entries:
        refs.setdefault(target, []).append(index)
    targets = sorted(refs)
    base = lorom_offset(BANK, 0x8000)

    messages: list[dict] = []
    for position, target in enumerate(targets):
        end = targets[position + 1] if position + 1 < len(targets) else POOL_END
        raw = data[base + (target - 0x8000) : base + (end - 0x8000)]
        segments = split_segments(data, base, target - 0x8000, end - 0x8000)
        kinds = {segment["kind"] for segment in segments}
        messages.append(
            {
                "index": position,
                "addr": f"{target:04X}",
                "end": f"{end:04X}",
                "file_offset": f"{base + (target - 0x8000):06X}",
                "length": end - target,
                "refs": refs[target],
                "clean": kinds <= {"text", "control"}
                and all(
                    segment["kind"] == "text" or segment["code"].startswith("01") or segment["code"] == "0f"
                    for segment in segments
                ),
                "bytes_hex": raw.hex(),
                "text": annotate(segments),
                "segments": segments,
            }
        )

    out = pathlib.Path(args.out) if args.out else root / "decomp" / "build" / "text" / "messages.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "rom": str(rom),
        "bank": f"{BANK:02X}",
        "table_addr": f"{TABLE_ADDR:04X}",
        "pool_end": f"{POOL_END:04X}",
        "table_entries": len(entries),
        "unique_messages": len(messages),
        "clean_messages": sum(1 for message in messages if message["clean"]),
        "messages": messages,
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"wrote {out} ({len(messages)} messages from {len(entries)} pointers, "
        f"{payload['clean_messages']} clean)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
