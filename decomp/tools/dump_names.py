#!/usr/bin/env python3
"""Decode the bank-$11 name tables into kana and emit a glossary template.

Tables:
  T1 $11:CDFD, 253 entries, strings $CFF7-$D5A7
  T2 $11:D5A8, 143 entries, strings $D6C6-$D9E3

Each byte is an 8x8 font code, not Shift-JIS. The katakana page and the
ASCII page are known; unknown codes are emitted as `{XX}` for review.

Output is ROM-derived and stays under decomp/build/text/ (ignored by git).
The generated CSV has empty `en`/`pt_br` columns so the glossary can be
filled without committing the original text.
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sys

DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[2]
T1 = (0xCDFD, 253)
T2 = (0xD5A8, 143)

KATAKANA = {
    0x8C: "ァ", 0x8D: "ア", 0x8E: "ィ", 0x8F: "イ", 0x90: "ゥ", 0x91: "ウ",
    0x92: "ェ", 0x93: "エ", 0x94: "ォ", 0x95: "オ",
    0x96: "カ", 0x97: "ガ", 0x98: "キ", 0x99: "ギ", 0x9A: "ク", 0x9B: "グ",
    0x9C: "ケ", 0x9D: "ゲ", 0x9E: "コ", 0x9F: "ゴ",
    0xA0: "サ", 0xA1: "ザ", 0xA2: "シ", 0xA3: "ジ", 0xA4: "ス", 0xA5: "ズ",
    0xA6: "セ", 0xA7: "ゼ", 0xA8: "ソ", 0xA9: "ゾ",
    0xAA: "タ", 0xAB: "ダ", 0xAC: "チ", 0xAD: "ヂ", 0xAE: "ッ", 0xAF: "ツ",
    0xB0: "ヅ", 0xB1: "テ", 0xB2: "デ", 0xB3: "ト", 0xB4: "ド",
    0xB5: "ナ", 0xB6: "ニ", 0xB7: "ヌ", 0xB8: "ネ", 0xB9: "ノ",
    0xBA: "ハ", 0xBB: "バ", 0xBC: "パ", 0xBD: "ヒ", 0xBE: "ビ", 0xBF: "ピ",
    0xC0: "フ", 0xC1: "ブ", 0xC2: "プ", 0xC3: "ヘ", 0xC4: "ベ", 0xC5: "ペ",
    0xC6: "ホ", 0xC7: "ボ", 0xC8: "ポ", 0xC9: "マ", 0xCA: "ミ", 0xCB: "ム",
    0xCC: "メ", 0xCD: "モ", 0xCE: "ャ", 0xCF: "ヤ", 0xD0: "ュ", 0xD1: "ユ",
    0xD2: "ョ", 0xD3: "ヨ", 0xD4: "ラ", 0xD5: "リ", 0xD6: "ル", 0xD7: "レ",
    0xD8: "ロ", 0xD9: "ワ", 0xDA: "ヲ", 0xDB: "ン", 0xDC: "ヴ", 0xDD: "ヵ",
    0xDE: "ヶ",
}

# The 8x8 font's low page is the ASCII page used by menu labels.
ASCII = {0x01: " "}
for _code in range(0x20, 0x60):
    ASCII[_code - 0x1F] = chr(_code)
ASCII[0x0E] = "ー"
ASCII[0x0F] = "゛"
ASCII[0x10] = "゜"


def lorom_offset(bank: int, addr: int) -> int:
    return (bank & 0x7F) * 0x8000 + (addr - 0x8000)


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


def decode_name(raw: bytes) -> str:
    out = []
    for code in raw:
        if code in KATAKANA:
            out.append(KATAKANA[code])
        elif code in ASCII:
            out.append(ASCII[code])
        else:
            out.append(f"{{{code:02X}}}")
    return "".join(out)


def table_strings(data: bytes, base: int, count: int) -> list[dict]:
    entries = []
    for index in range(count):
        off = lorom_offset(0x11, base + index * 2)
        target = data[off] | (data[off + 1] << 8)
        start = lorom_offset(0x11, target)
        end = start
        while end < len(data) and data[end] != 0:
            end += 1
        raw = data[start:end]
        entries.append(
            {
                "index": index,
                "target": f"{target:04X}",
                "file_offset": f"{start:06X}",
                "codes": raw.hex(),
                "jp": decode_name(raw),
            }
        )
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
    t1 = table_strings(data, *T1)
    t2 = table_strings(data, *T2)

    out = pathlib.Path(args.out) if args.out else root / "decomp" / "build" / "text" / "names.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {"rom": str(rom), "tables": {"t1": t1, "t2": t2}}
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    csv_path = out.with_suffix(".csv")
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["table", "index", "file_offset", "jp", "en", "pt_br", "notes"])
        for table, entries in (("t1", t1), ("t2", t2)):
            for entry in entries:
                writer.writerow([table, entry["index"], entry["file_offset"], entry["jp"], "", "", ""])

    print(f"wrote {out}")
    print(f"wrote {csv_path}")
    print(f"t1={len(t1)} t2={len(t2)}")
    for table, entries in (("t1", t1[:5]), ("t2", t2[:5])):
        print(f"{table}:", ", ".join(e["jp"] for e in entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
