#!/usr/bin/env python3
"""Point the $01:DFCE window-text style branches at the faithful glyph path.

The window text rasterizer at $01:DFCE branches on $0250:

  * $0250 == 0 -> expand the 1bpp glyph source directly (works);
  * $0250 != 0 -> two-pass solid/shadow path (renders scrambled tiles here:
    fragments and solid blocks instead of the message text).

The window frame, position and palette are prepared by the caller and keep
using $0250; only the glyph rasterizer is affected.  The generated body is
patched to take the style-0 branch unconditionally.

This runs after tools/regen.sh, which overwrites src/gen.  It is intentionally
a no-op when the branches already point at the style-0 labels, and fails
loudly if the expected code shape changes.
"""
from __future__ import annotations

import pathlib
import sys

GEN = pathlib.Path(__file__).resolve().parent.parent / "src" / "gen" / "bank01_part0b_v2.c"

# Exact emitted shape: the branch guards for the even and odd style paths.
TARGETS = {
    "L_E03D_M0X0": "window-text even style branch",
    "L_E137_M0X0": "window-text odd style branch",
}
GUARD = "if (cpu->_flag_Z == 1)"


def main() -> int:
    try:
        text = GEN.read_text()
    except FileNotFoundError:
        print(f"patch-window-text: {GEN} absent (HLE/LLE build), skipping")
        return 0
    changed = 0
    for label, what in TARGETS.items():
        marker = f"goto {label};"
        hits = [line for line in text.splitlines() if marker in line]
        if not hits:
            print(f"patch-window-text: no AOT {what} (HLE/LLE build), skipping")
            continue
        if len(hits) != 1:
            print(
                f"patch-window-text: expected exactly one {what} ({marker}), "
                f"found {len(hits)}",
                file=sys.stderr,
            )
            return 1
        old = hits[0]
        if "if (1)" in old:
            continue
        if GUARD not in old:
            print(
                f"patch-window-text: {what} has an unexpected guard: {old.strip()}",
                file=sys.stderr,
            )
            return 1
        new = old.replace(GUARD, "if (1)", 1)
        text = text.replace(old, new, 1)
        changed += 1
    if changed:
        GEN.write_text(text)
        print(f"patch-window-text: patched {changed} branch(es) in {GEN}")
    else:
        print(f"patch-window-text: already patched ({GEN})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
