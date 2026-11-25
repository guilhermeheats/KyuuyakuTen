#!/usr/bin/env python3
"""Encode/decode the game's 8x8 ASCII font page.

The window renderer maps printable ASCII 0x20-0x5F to font tiles with
``font_code = ASCII - 0x1F``. The mapping was verified live by patching the
menu label COMP -> TEST at $01:A940: the text tilemap changed from
24 30 2E 31 to 35 26 34 35.

This page is uppercase-only (space, digits, punctuation, A-Z). Lowercase
ASCII would land in the kana page, so `encode` uppercases by default and
rejects characters outside the supported range.

Examples:
  python3 tools/font_codec.py encode "COMP"
  python3 tools/font_codec.py encode "TEST"
  python3 tools/font_codec.py decode 24 30 2E 31
"""
from __future__ import annotations

import argparse
import sys

LOW = 0x20
HIGH = 0x5F
BIAS = 0x1F


def encode(text: str, uppercase: bool = True) -> bytes:
    if uppercase:
        text = text.upper()
    out = bytearray()
    for char in text:
        code = ord(char)
        if not (LOW <= code <= HIGH):
            raise ValueError(f"character {char!r} (U+{code:04X}) is outside 0x20-0x5F")
        out.append(code - BIAS)
    return bytes(out)


def decode(data: bytes) -> str:
    out = []
    for byte in data:
        code = byte + BIAS
        if not (LOW <= code <= HIGH):
            raise ValueError(f"font code 0x{byte:02X} is outside the ASCII page")
        out.append(chr(code))
    return "".join(out)


def selftest() -> int:
    if encode("COMP") != bytes((0x24, 0x30, 0x2E, 0x31)):
        print("FAIL selftest: COMP", file=sys.stderr)
        return 1
    if encode("TEST") != bytes((0x35, 0x26, 0x34, 0x35)):
        print("FAIL selftest: TEST", file=sys.stderr)
        return 1
    if decode(bytes((0x22, 0x33, 0x2E, 0x30, 0x33, 0x34))) != "ARMORS":
        print("FAIL selftest: ARMORS", file=sys.stderr)
        return 1
    print("ok selftest: COMP/TEST/ARMORS")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    pe = sub.add_parser("encode", help="ASCII text -> font-code bytes")
    pe.add_argument("text")
    pe.add_argument("--no-uppercase", action="store_true")
    pd = sub.add_parser("decode", help="font-code bytes (hex) -> ASCII text")
    pd.add_argument("bytes", nargs="+")
    sub.add_parser("selftest", help="run built-in checks")
    args = ap.parse_args()

    if args.command == "selftest":
        return selftest()
    if args.command == "encode":
        data = encode(args.text, uppercase=not args.no_uppercase)
        print(" ".join(f"{b:02X}" for b in data))
        return 0
    if args.command == "decode":
        data = bytearray()
        for token in args.bytes:
            data.extend(bytes.fromhex(token))
        print(decode(bytes(data)))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
