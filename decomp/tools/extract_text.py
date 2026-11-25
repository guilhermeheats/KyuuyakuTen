#!/usr/bin/env python3
"""Extract Japanese text runs from the Kyuuyaku Megami Tensei ROM.

The main script lives in bank $10 (and a system-message pool in bank $11) as
Shift-JIS text interleaved with one-byte control codes. This tool is a first
pass: it finds decodable Shift-JIS runs and records their ROM offsets so the
translation pipeline can address them. It does not yet interpret the script
bytecode or group lines into messages.

Outputs are ROM-derived and must stay under decomp/build/ (ignored by git).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from dataclasses import dataclass

DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[2]
# Shift-JIS lead bytes, excluding 0x80/0xA0/0xFD-0xFF which are not valid here.
SJIS_LEAD = set(range(0x81, 0xA0)) | set(range(0xE0, 0xFD))
JAPANESE_RE = re.compile(r"[\u3000-\u303f\u3040-\u30ff\u3400-\u9fff\uff00-\uffef]")
KANA_RE = re.compile(r"[\u3040-\u30ff]")


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
    return byte in SJIS_LEAD


def decode_run(data: bytes, start: int, end: int) -> str | None:
    try:
        return data[start:end].decode("shift_jis")
    except UnicodeDecodeError:
        return None


def scan_bank(
    data: bytes,
    bank: int,
    min_chars: int,
    require_kana: bool,
    start: int = 0x8000,
    end: int = 0x10000,
    trim_operands: bool = True,
) -> list[dict]:
    base = lorom_offset(bank, 0x8000)
    bank_data = data[base : base + 0x8000]
    lo = max(0, start - 0x8000)
    hi = min(len(bank_data), end - 0x8000)
    runs: list[dict] = []
    i = lo
    while i < hi:
        if not is_sjis_lead(bank_data[i]):
            i += 1
            continue
        start_i = i
        end_i = i
        while end_i + 1 < hi:
            b = bank_data[end_i]
            if b < 0x20 or b == 0x7F:
                break
            if is_sjis_lead(b) and end_i + 1 < hi and 0x40 <= bank_data[end_i + 1] <= 0xFC:
                end_i += 2
            elif b in (0x20, 0x21, 0x2D, 0x2E, 0x30) or 0x30 <= b <= 0x39:
                # single-byte ASCII/punctuation inside a Japanese run
                end_i += 1
            else:
                break
        if end_i > start_i:
            text_start = start_i
            trimmed = ""
            # Many messages are preceded by `08 xx <lo> <hi> <lo> <hi>`:
            # the command's 16-bit operand is repeated immediately before the
            # actual inline text. Drop that duplicated operand so the dump
            # starts on the sentence rather than its pointer value.
            if (
                trim_operands
                and start_i >= lo + 2
                and bank_data[start_i - 2] == 0x08
            ):
                trimmed = bank_data[start_i : start_i + 2].hex()
                text_start = start_i + 2
            text = decode_run(bank_data, text_start, end_i)
            if text:
                jp = JAPANESE_RE.findall(text)
                kana = KANA_RE.findall(text)
                if len(jp) >= min_chars and (kana or not require_kana):
                    runs.append(
                        {
                            "bank": f"{bank:02X}",
                            "addr": f"{(0x8000 + text_start) & 0xFFFF:04X}",
                            "file_offset": f"{base + text_start:06X}",
                            "length": end_i - text_start,
                            "bytes_hex": bank_data[text_start:end_i].hex(),
                            "text": text,
                            "trimmed_operand": trimmed,
                        }
                    )
            i = max(end_i, start_i + 1)
        else:
            i += 1
    return runs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", help="ROM path; defaults to SNESRECOMP_ROM/rom.cfg")
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--banks", default="10,11", help="comma-separated bank hex list")
    ap.add_argument("--min-chars", type=int, default=2)
    ap.add_argument("--no-kana-filter", action="store_true", help="keep kanji-only runs too")
    ap.add_argument("--no-trim-operands", action="store_true", help="do not strip a duplicated 08xx operand")
    ap.add_argument("--out", default=None)
    ap.add_argument("--jsonl", action="store_true", help="also write a JSONL file")
    args = ap.parse_args()

    root = pathlib.Path(args.root)
    rom = resolve_rom(args.rom, root)
    if rom is None:
        print("no ROM found; pass --rom or set SNESRECOMP_ROM", file=sys.stderr)
        return 1
    data = rom.read_bytes()
    banks = [int(x, 16) for x in args.banks.split(",") if x.strip()]
    # Bank $10 holds the main script after the shared graphics block; bank $11
    # holds the system-message pool before the name pointer tables.
    ranges = {
        0x10: (0x81F0, 0x10000),
        0x11: (0x802A, 0xCDFD),
    }
    all_runs: list[dict] = []
    for bank in banks:
        start, end = ranges.get(bank, (0x8000, 0x10000))
        all_runs.extend(
            scan_bank(
                data,
                bank,
                args.min_chars,
                not args.no_kana_filter,
                start=start,
                end=end,
                trim_operands=not args.no_trim_operands,
            )
        )

    out = pathlib.Path(args.out) if args.out else root / "decomp" / "build" / "text" / "script_jp.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "rom": str(rom),
        "banks": [f"{b:02X}" for b in banks],
        "count": len(all_runs),
        "runs": all_runs,
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(all_runs)} runs)")
    if args.jsonl:
        jsonl = out.with_suffix(".jsonl")
        with jsonl.open("w", encoding="utf-8") as fh:
            for run in all_runs:
                fh.write(json.dumps(run, ensure_ascii=False) + "\n")
        print(f"wrote {jsonl}")

    by_bank: dict[str, int] = {}
    for run in all_runs:
        by_bank[run["bank"]] = by_bank.get(run["bank"], 0) + 1
    print("runs by bank:", ", ".join(f"{k}={v}" for k, v in sorted(by_bank.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
