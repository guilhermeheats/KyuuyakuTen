#!/usr/bin/env python3
"""BPS (Beat) patch creator/applier.

The encoder is intentionally simple and spec-correct: unchanged bytes at the
same offset become SourceRead, changed bytes become TargetRead. The applier
implements all four BPS modes and verifies the source/target/patch CRCs, so it
also accepts patches produced by other BPS tools.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import zlib
from pathlib import Path

MAGIC = b"BPS1"


def enc_varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("varint must be non-negative")
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def dec_varint(data: bytes, pos: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if pos >= len(data):
            raise ValueError("truncated varint")
        byte = data[pos]
        pos += 1
        value |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            return value, pos
        shift += 7
        if shift > 63:
            raise ValueError("varint too large")


def enc_svarint(value: int) -> bytes:
    return enc_varint((abs(value) << 1) | (1 if value < 0 else 0))


def dec_svarint(data: bytes, pos: int) -> tuple[int, int]:
    value, pos = dec_varint(data, pos)
    return (-(value >> 1) if (value & 1) else (value >> 1)), pos


def _u32(data: bytes) -> int:
    return int.from_bytes(data, "little")


def create(source: bytes, target: bytes, metadata: bytes = b"") -> bytes:
    commands = bytearray()
    pos = 0
    while pos < len(target):
        if pos < len(source) and target[pos] == source[pos]:
            length = 1
            while (
                pos + length < len(target)
                and pos + length < len(source)
                and target[pos + length] == source[pos + length]
            ):
                length += 1
            commands += enc_varint(((length - 1) << 2) | 0)  # SourceRead
            pos += length
            continue

        start = pos
        while pos < len(target):
            if pos < len(source) and target[pos] == source[pos]:
                break
            pos += 1
        run = target[start:pos]
        commands += enc_varint(((len(run) - 1) << 2) | 1)  # TargetRead
        commands += run

    out = bytearray(MAGIC)
    out += enc_varint(len(source))
    out += enc_varint(len(target))
    out += enc_varint(len(metadata))
    out += metadata
    out += commands
    out += (zlib.crc32(source) & 0xFFFFFFFF).to_bytes(4, "little")
    out += (zlib.crc32(target) & 0xFFFFFFFF).to_bytes(4, "little")
    out += (zlib.crc32(out) & 0xFFFFFFFF).to_bytes(4, "little")
    return bytes(out)


def apply(source: bytes, patch: bytes) -> tuple[bytes, bytes]:
    if not patch.startswith(MAGIC):
        raise ValueError("not a BPS patch")
    if len(patch) < 16:
        raise ValueError("BPS patch too short")
    if (_u32(patch[-4:]) != (zlib.crc32(patch[:-4]) & 0xFFFFFFFF)):
        raise ValueError("patch CRC mismatch")

    pos = 4
    source_size, pos = dec_varint(patch, pos)
    target_size, pos = dec_varint(patch, pos)
    metadata_size, pos = dec_varint(patch, pos)
    metadata = patch[pos : pos + metadata_size]
    pos += metadata_size
    source_crc = _u32(patch[-12:-8])
    target_crc = _u32(patch[-8:-4])
    if source_size != len(source):
        raise ValueError(f"source size mismatch: patch wants {source_size}, got {len(source)}")
    if (zlib.crc32(source) & 0xFFFFFFFF) != source_crc:
        raise ValueError("source CRC mismatch")

    out = bytearray()
    source_copy_pos = 0
    target_copy_pos = 0
    while len(out) < target_size:
        command, pos = dec_varint(patch, pos)
        length = (command >> 2) + 1
        mode = command & 3
        if mode == 0:  # SourceRead: source at the current output offset
            start = len(out)
            if start + length > len(source):
                raise ValueError("SourceRead out of range")
            out += source[start : start + length]
        elif mode == 1:  # TargetRead
            if pos + length > len(patch) - 12:
                raise ValueError("TargetRead out of range")
            out += patch[pos : pos + length]
            pos += length
        elif mode == 2:  # SourceCopy
            offset, pos = dec_svarint(patch, pos)
            source_copy_pos += offset
            if source_copy_pos < 0 or source_copy_pos + length > len(source):
                raise ValueError("SourceCopy out of range")
            out += source[source_copy_pos : source_copy_pos + length]
            source_copy_pos += length
        else:  # TargetCopy
            offset, pos = dec_svarint(patch, pos)
            target_copy_pos += offset
            if target_copy_pos < 0:
                raise ValueError("TargetCopy negative offset")
            for i in range(length):
                if target_copy_pos + i >= len(out):
                    raise ValueError("TargetCopy out of range")
                out.append(out[target_copy_pos + i])
            target_copy_pos += length
    if len(out) != target_size:
        raise ValueError(f"target size mismatch: wanted {target_size}, got {len(out)}")
    if (zlib.crc32(out) & 0xFFFFFFFF) != target_crc:
        raise ValueError("target CRC mismatch")
    return bytes(out), metadata


def info(patch: bytes) -> dict:
    if not patch.startswith(MAGIC):
        raise ValueError("not a BPS patch")
    if len(patch) < 16:
        raise ValueError("BPS patch too short")
    if (_u32(patch[-4:]) != (zlib.crc32(patch[:-4]) & 0xFFFFFFFF)):
        raise ValueError("patch CRC mismatch")
    pos = 4
    source_size, pos = dec_varint(patch, pos)
    target_size, pos = dec_varint(patch, pos)
    metadata_size, pos = dec_varint(patch, pos)
    metadata = patch[pos : pos + metadata_size]
    return {
        "source_size": source_size,
        "target_size": target_size,
        "metadata_size": metadata_size,
        "metadata": metadata.decode("utf-8", "replace"),
        "patch_size": len(patch),
        "sha256": hashlib.sha256(patch).hexdigest(),
    }


def selftest() -> int:
    cases = []
    src = b"hello world"
    cases.append(("insert", src, b"hello brave world"))
    cases.append(("identity", src, src))
    cases.append(("shorter", src, b"hello"))
    rng = random.Random(0xC0FFEE)
    src2 = bytes(rng.randrange(256) for _ in range(4096))
    dst2 = bytearray(src2)
    dst2[100:110] = b"ABCDEFGHIJ"
    dst2[2000:2000] = b"inserted block"
    cases.append(("random-edit", src2, bytes(dst2)))
    for name, source, target in cases:
        patch = create(source, target, b"test-meta")
        result, metadata = apply(source, patch)
        if result != target:
            print(f"FAIL {name}: output mismatch", file=sys.stderr)
            return 1
        if metadata != b"test-meta":
            print(f"FAIL {name}: metadata mismatch", file=sys.stderr)
            return 1
        print(f"ok {name}: patch={len(patch)} bytes target={len(target)}")
    print("BPS selftest passed")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    pc = sub.add_parser("create", help="create a BPS patch")
    pc.add_argument("source")
    pc.add_argument("target")
    pc.add_argument("patch")
    pc.add_argument("--metadata", default="")
    pa = sub.add_parser("apply", help="apply a BPS patch")
    pa.add_argument("source")
    pa.add_argument("patch")
    pa.add_argument("target")
    pi = sub.add_parser("info", help="print BPS header information")
    pi.add_argument("patch")
    sub.add_parser("selftest", help="run built-in tests")
    args = ap.parse_args()

    if args.command == "selftest":
        return selftest()
    if args.command == "create":
        patch = create(
            Path(args.source).read_bytes(),
            Path(args.target).read_bytes(),
            args.metadata.encode("utf-8"),
        )
        Path(args.patch).write_bytes(patch)
        print(f"wrote {args.patch} ({len(patch)} bytes)")
        return 0
    if args.command == "apply":
        result, metadata = apply(Path(args.source).read_bytes(), Path(args.patch).read_bytes())
        Path(args.target).write_bytes(result)
        if metadata:
            print(f"metadata: {metadata.decode('utf-8', 'replace')}")
        print(f"wrote {args.target} ({len(result)} bytes)")
        return 0
    if args.command == "info":
        print(json.dumps(info(Path(args.patch).read_bytes()), indent=2))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
