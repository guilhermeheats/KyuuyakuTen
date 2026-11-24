#!/usr/bin/env python3
"""Apply the validated KyuuyakuTen navigation cheats to a running game.

The values below are the ones used during the Daedalus/JUNKS exploration:
HP 999/999, MP 99/99, Macca 999,999, Magnetite 9,999, stats at the
game's displayed cap of 35 (force on both characters; intelligence and
luck on Yumiko), plus the enemy-HP slots for battles.

Usage:
    python3 tools/apply-cheats.py --port 4377
    python3 tools/apply-cheats.py --port 4416 --no-enemy-hp

Enemy HP slots are written only while a battle is active ($7E0253 != 0)
when --battle-only is given; otherwise they are written immediately
(harmless in the field).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "snesrecomp" / "tools"))

from sneslib.client import DebugClient  # noqa: E402

# $7E0C72-$7E0C74: Macca (3 bytes, little-endian).  The status screen
# shows six digits; 999,999 is the display max (9,999,999 overflows).
MACCA = ("0c72", "3f420f")  # 999,999
# $7E0C75-$7E0C76: Magnetite (2 bytes, little-endian)
MAGNETITE = ("0c75", "0f27")  # 9,999

# Character 1: HP current/max $0D02/$0D04 (16-bit), MP current/max
# $0D06/$0D07 (bytes). Character 2: HP $0D12/$0D14, MP $0D16/$0D17.
HP_MP = [
    ("0d02", "e703"), ("0d04", "e703"),
    ("0d12", "e703"), ("0d14", "e703"),
    ("0d06", "6363"), ("0d16", "6363"),
]

# $0D08/$0D18 is the LEVEL, not a stat.  The five stats are at
# $0D09-$0D0D (P1) and $0D19-$0D1D (P2): 体, 知, 力, 速, 運.
# The status screen clamps the displayed value at 35 (99 shows as 35),
# so 0x23 is the max.  Requested: force on both; intelligence and luck
# on Yumiko.
STATS = [
    ("0d0b", "23"),  # P1 力
    ("0d1a", "23"),  # P2 知
    ("0d1b", "23"),  # P2 力
    ("0d1d", "23"),  # P2 運
]

# Enemy HP: the first slot is $10B0/$10C0.  The old list started at
# $10B2/$10C2 and left the first enemy at full HP.
ENEMY_HP = [
    "10b0", "10b2", "10b4", "10b6", "10b8",
    "10c0", "10c2", "10c4", "10c6", "10c8",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=4377)
    ap.add_argument("--no-enemy-hp", action="store_true")
    ap.add_argument("--battle-only", action="store_true",
                    help="write enemy HP only when $7E0253 is nonzero")
    args = ap.parse_args()

    c = DebugClient(args.port, timeout=15)
    try:
        c.query(f"write_ram {MACCA[0]} {MACCA[1]}", retry=False)
        c.query(f"write_ram {MAGNETITE[0]} {MAGNETITE[1]}", retry=False)
        for addr, value in HP_MP:
            c.query(f"write_ram {addr} {value}", retry=False)
        for addr, value in STATS:
            c.query(f"write_ram {addr} {value}", retry=False)

        if not args.no_enemy_hp:
            battle = False
            if args.battle_only:
                raw = c.query("read_ram 253 1", retry=False)["hex"]
                battle = int(raw, 16) != 0
            if battle or not args.battle_only:
                for addr in ENEMY_HP:
                    c.query(f"write_ram {addr} 0100", retry=False)

        def read(addr: str, n: int) -> str:
            return c.query(f"read_ram {addr} {n}", retry=False)["hex"]

        print(f"port {args.port}: macca={read('0c72', 3)} "
              f"magnetite={read('0c75', 2)}")
        print(f"P1 lv+stats={read('0d08', 6)} P2 lv+stats={read('0d18', 6)}")
        print(f"P1 HP={read('0d02', 4)} P2 HP={read('0d12', 4)}")
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
