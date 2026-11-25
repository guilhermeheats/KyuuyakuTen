#!/usr/bin/env python3
"""Full-width Latin codec for the dialogue/menu text renderer.

The game's text engine decodes Shift-JIS two bytes at a time. Raw ASCII in a
script slot is therefore read as Shift-JIS pairs and renders as unrelated
kanji. The 16x16 dialogue font does contain the full-width Latin block
(U+FF01-U+FF5E), lower-case letters and Japanese punctuation, so English can
be written with full-width characters and still occupy exactly two bytes per
character, just like the original Japanese text.

`encode` converts normal ASCII to full-width forms, pads with U+3000 to the
requested byte length and returns Shift-JIS bytes. Existing Japanese text is
left untouched, so mixed strings work too.
"""
from __future__ import annotations

import sys

# ASCII punctuation that has a better typographic full-width equivalent than
# the mathematical U+FF0x block. U+FF0D (full-width hyphen) is not part of the
# original Shift-JIS set, so use U+2010 instead.
PUNCT = {
    "'": "\u2019",  # right single quotation mark
    '"': "\u201d",  # right double quotation mark
    "-": "\u2010",  # hyphen
}

FULLWIDTH_SPACE = "\u3000"


def to_fullwidth(text: str) -> str:
    """Convert ASCII printable characters to full-width forms."""
    out: list[str] = []
    for ch in text:
        code = ord(ch)
        if ch == " ":
            out.append(FULLWIDTH_SPACE)
        elif ch in PUNCT:
            out.append(PUNCT[ch])
        elif 0x21 <= code <= 0x7E:
            out.append(chr(code + 0xFEE0))
        else:
            out.append(ch)
    return "".join(out)


def encode(text: str, length: int | None = None) -> bytes:
    """Encode text as full-width Shift-JIS, optionally padded to `length` bytes.

    `length` is the original slot size in bytes. The converted text must fit;
    the remainder is padded with full-width spaces. Because every full-width
    character is two bytes, `length` must be even.
    """
    converted = to_fullwidth(text)
    encoded = converted.encode("cp932")
    if length is None:
        return encoded
    if length % 2:
        raise ValueError(f"full-width slot length must be even, got {length}")
    if len(encoded) > length:
        chars = len(converted)
        budget = length // 2
        raise ValueError(
            f"text too long: {len(encoded)} bytes / {chars} chars "
            f"> {length} byte slot ({budget} full-width chars): {converted!r}"
        )
    missing = length - len(encoded)
    if missing % 2:
        raise ValueError(f"text leaves an odd number of bytes: {missing}")
    return encoded + FULLWIDTH_SPACE.encode("cp932") * (missing // 2)


def selftest() -> int:
    if to_fullwidth("Which item?") != "\uff37\uff48\uff49\uff43\uff48\u3000\uff49\uff54\uff45\uff4d\uff1f":
        print("FAIL selftest: ASCII conversion", file=sys.stderr)
        return 1
    encoded = encode("Which item?", 26)
    if len(encoded) != 26:
        print("FAIL selftest: padding", file=sys.stderr)
        return 1
    if encoded[:22] != "Ｗｈｉｃｈ　ｉｔｅｍ？".encode("cp932"):
        print("FAIL selftest: encoded text", file=sys.stderr)
        return 1
    if encode("It's a-b.", 26)[:18] != "Ｉｔ’ｓ　ａ‐ｂ．".encode("cp932"):
        print("FAIL selftest: punctuation", file=sys.stderr)
        return 1
    try:
        encode("This text is much too long", 26)
    except ValueError:
        pass
    else:
        print("FAIL selftest: overlong text accepted", file=sys.stderr)
        return 1
    if encode("すでに日本語", 12) != "すでに日本語".encode("cp932"):
        print("FAIL selftest: Japanese passthrough", file=sys.stderr)
        return 1
    print("ok selftest: full-width Latin conversion and padding")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        raise SystemExit(selftest())
    print(encode(" ".join(sys.argv[1:])).hex(" "))
