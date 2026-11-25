#!/usr/bin/env python3
"""Verify a ROM against the project's rom_identity.txt.

This is the full-ROM matching gate: a decomp build is only accepted when its
bytes match the Japanese baseline (CRC32, SHA-256 and size). The original ROM
is never copied into the repository.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import pathlib
import sys
import zlib

DEFAULT_IDENTITY = pathlib.Path(__file__).resolve().parents[2] / "rom_identity.txt"
DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[2]


def parse_identity(path: pathlib.Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        values[key.strip()] = value
    return values


def resolve_rom(explicit: str | None, root: pathlib.Path) -> pathlib.Path | None:
    candidates: list[pathlib.Path] = []
    if explicit:
        candidates.append(pathlib.Path(explicit))
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", help="ROM to verify; defaults to SNESRECOMP_ROM/rom.cfg")
    ap.add_argument("--identity", default=str(DEFAULT_IDENTITY))
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    identity_path = pathlib.Path(args.identity)
    if not identity_path.is_file():
        print(f"missing identity file: {identity_path}", file=sys.stderr)
        return 1
    expected = parse_identity(identity_path)

    rom = resolve_rom(args.rom, pathlib.Path(args.root))
    if rom is None:
        print("no ROM found; pass --rom or set SNESRECOMP_ROM", file=sys.stderr)
        return 1

    data = rom.read_bytes()
    actual = {
        "rom_size": str(len(data)),
        "crc32": f"{zlib.crc32(data) & 0xFFFFFFFF:08x}",
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    wanted = {
        "rom_size": expected.get("rom_size", "?"),
        "crc32": expected.get("expected_crc32", "?"),
        "sha256": expected.get("expected_sha256", "?"),
    }
    mismatches = [
        (key, wanted[key], actual[key])
        for key in wanted
        if wanted[key].lower() != actual[key].lower()
    ]

    if not args.quiet:
        print(f"ROM: {rom}")
        print(f"size: {actual['rom_size']} (expected {wanted['rom_size']})")
        print(f"crc32: {actual['crc32']} (expected {wanted['crc32']})")
        print(f"sha256: {actual['sha256']} (expected {wanted['sha256']})")

    if mismatches:
        print("ROM MISMATCH", file=sys.stderr)
        for key, want, got in mismatches:
            print(f"  {key}: expected {want}, got {got}", file=sys.stderr)
        return 1

    print("ROM MATCH: full-ROM baseline is byte-identical.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
