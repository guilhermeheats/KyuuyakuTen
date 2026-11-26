#!/usr/bin/env python3
"""Point the generated AOT name copy at the relocated T1/T2 tables.

The recomp runs `bank_02_C87B_*` as native C, so patching the 65816
instructions in the ROM has no effect on it. The name copy reads the
original T1/T2 pointer tables and name bytes from bank $11:

    0x11CDFD  T1 pointers
    0x11D5A8  T2 pointers
    0x110000  name bytes

`tools/patch_names.py --in-place`/relocation writes the English names to
bank $2E and updates the 65816 code for emulators. This script applies the
same redirection to the generated native code, after `tools/regen.sh` has
recreated `src/gen`:

    0x2EB820  T1 pointers
    0x2EBA1A  T2 pointers
    0x2E0000  name bytes

It is idempotent and fails if the generated file no longer has the
expected constants.
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TARGET = ROOT / "src" / "gen" / "bank02_part09_v2.c"

REPLACEMENTS = {
    "0x11cdfd": "0x2eb820",
    "0x11d5a8": "0x2eba1a",
    "0x110000": "0x2e0000",
}


def main() -> int:
    if not TARGET.exists():
        print(f"patch-name-tables: {TARGET} absent (HLE/LLE build), skipping")
        return 0
    text = TARGET.read_text()
    old_counts = {old: text.count(old) for old in REPLACEMENTS}
    new_counts = {new: text.count(new) for new in REPLACEMENTS.values()}
    if not any(old_counts.values()):
        if all(new_counts.values()):
            print("patch-name-tables: already patched")
            return 0
        print(
            "patch-name-tables: old constants absent and new constants incomplete: "
            f"old={old_counts} new={new_counts}",
            file=sys.stderr,
        )
        return 1
    if not all(old_counts.values()):
        print(
            f"patch-name-tables: unexpected constant counts: {old_counts}",
            file=sys.stderr,
        )
        return 1
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    TARGET.write_text(text)
    print(f"patch-name-tables: redirected name tables in {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
