#!/usr/bin/env python3
"""Export the recompiler's function graph as decomp labels.

Inputs (all local, no ROM bytes are written):
  - recomp/symbols.toml        named functions
  - recomp/bankXX.cfg          coverage roots / entry variants
  - src/gen/program_manifest.json  AOT nodes and roots

Outputs (ignored by git):
  build/symbols/symbols.csv
  build/symbols/symbols.json
  build/symbols/wla_symbols.inc

The WLA include is a convenience map of bank+address constants; decomp source
still defines its own labels as it is written.
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import re
import tomllib
from collections import defaultdict

DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[2]
CFG_FUNC_RE = re.compile(
    r"^\s*func\s+(\S+)\s+([0-9A-Fa-f]+)\s+entry_mx:(\d+)\s*,\s*(\d+)"
)


def pc24(bank: int, addr: int) -> int:
    return ((bank & 0xFF) << 16) | (addr & 0xFFFF)


def add_name(names: dict[int, set[str]], sources: dict[int, set[str]], p: int, name: str, source: str) -> None:
    names[p].add(name)
    sources[p].add(source)


def load_named(root: pathlib.Path, names, sources) -> None:
    path = root / "recomp" / "symbols.toml"
    if not path.is_file():
        return
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    for func in data.get("func", []):
        try:
            bank = int(func["bank"])
            addr = int(str(func["addr"]), 16)
        except (KeyError, ValueError):
            continue
        add_name(names, sources, pc24(bank, addr), func["name"], "symbols.toml")


def load_cfg(root: pathlib.Path, names, sources, cfg_variants) -> None:
    for cfg in sorted((root / "recomp").glob("bank*.cfg")):
        m = re.fullmatch(r"bank([0-9A-Fa-f]{2})\.cfg", cfg.name)
        if not m:
            continue
        bank = int(m.group(1), 16)
        for line in cfg.read_text(encoding="utf-8", errors="replace").splitlines():
            fm = CFG_FUNC_RE.match(line)
            if not fm:
                continue
            name, addr_s, em, ex = fm.groups()
            p = pc24(bank, int(addr_s, 16))
            add_name(names, sources, p, name, f"recomp/{cfg.name}")
            cfg_variants[p].add((int(em), int(ex)))


def load_manifest(root: pathlib.Path, names, sources, manifest_info, roots) -> None:
    path = root / "src" / "gen" / "program_manifest.json"
    if not path.is_file():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    for _key, node in data.get("nodes", {}).items():
        key = node.get("key") or {}
        try:
            p = int(key["pc24"])
        except (KeyError, TypeError, ValueError):
            continue
        bank, addr = p >> 16, p & 0xFFFF
        m, x = int(key.get("m", 0)), int(key.get("x", 0))
        manifest_info[p]["variants"].add((m, x))
        manifest_info[p]["instructions"] = max(
            manifest_info[p]["instructions"], int(node.get("instruction_count", 0) or 0)
        )
        manifest_info[p]["min_pc24"] = min(
            manifest_info[p]["min_pc24"], int(node.get("min_pc24", p) or p)
        )
        manifest_info[p]["max_pc24"] = max(
            manifest_info[p]["max_pc24"], int(node.get("max_pc24", p) or p)
        )
        disposition = node.get("disposition")
        if disposition:
            manifest_info[p]["dispositions"].add(str(disposition))
        if p not in names:
            add_name(names, sources, p, f"Coverage_{bank:02X}_{addr:04X}", "manifest")
    for root_node in data.get("roots", []):
        try:
            roots.add(int(root_node["pc24"]))
        except (KeyError, TypeError, ValueError):
            pass


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    root = pathlib.Path(args.root).resolve()
    out = pathlib.Path(args.out) if args.out else root / "decomp" / "build" / "symbols"
    out.mkdir(parents=True, exist_ok=True)

    names: dict[int, set[str]] = defaultdict(set)
    sources: dict[int, set[str]] = defaultdict(set)
    cfg_variants: dict[int, set[tuple[int, int]]] = defaultdict(set)
    manifest_info: dict[int, dict] = defaultdict(
        lambda: {
            "variants": set(),
            "instructions": 0,
            "min_pc24": 1 << 24,
            "max_pc24": 0,
            "dispositions": set(),
        }
    )
    roots: set[int] = set()

    load_named(root, names, sources)
    load_cfg(root, names, sources, cfg_variants)
    load_manifest(root, names, sources, manifest_info, roots)

    all_pc = sorted(set(names) | set(manifest_info) | set(cfg_variants) | roots)
    rows = []
    for p in all_pc:
        bank, addr = p >> 16, p & 0xFFFF
        label = f"{bank:02X}_{addr:04X}"
        human = " | ".join(sorted(names.get(p, set()))) or f"sub_{p:06X}"
        variants = sorted(cfg_variants.get(p, set()) | manifest_info[p]["variants"])
        rows.append(
            {
                "bank": f"{bank:02X}",
                "addr": f"{addr:04X}",
                "pc24": f"{p:06X}",
                "label": f"SYM_{label}",
                "name": human,
                "source": " | ".join(sorted(sources.get(p, set()))),
                "root": "yes" if p in roots else "",
                "variants": " ".join(f"{'M' if m else 'm'}{'X' if x else 'x'}" for m, x in variants),
                "instructions": manifest_info[p]["instructions"] or "",
                "min_pc24": f"{manifest_info[p]['min_pc24']:06X}"
                if manifest_info[p]["instructions"]
                else "",
                "max_pc24": f"{manifest_info[p]['max_pc24']:06X}"
                if manifest_info[p]["instructions"]
                else "",
                "disposition": " | ".join(sorted(manifest_info[p]["dispositions"])),
            }
        )

    csv_path = out / "symbols.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["bank"])
        writer.writeheader()
        writer.writerows(rows)

    json_path = out / "symbols.json"
    json_path.write_text(
        json.dumps(
            {
                "root_count": len(roots),
                "address_count": len(rows),
                "named_count": sum(1 for p in all_pc if names.get(p)),
                "rows": rows,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    inc_path = out / "wla_symbols.inc"
    with inc_path.open("w", encoding="utf-8") as fh:
        fh.write("; Generated by decomp/tools/export_symbols.py — do not edit.\n")
        fh.write("; SYM_<bank>_<addr> is the 24-bit bank:address; OFF_ is the 16-bit offset.\n\n")
        for row in rows:
            p = int(row["pc24"], 16)
            comment = row["name"].replace("\n", " ")
            fh.write(f".DEFINE {row['label']} ${p:06X} ; {comment}\n")
            fh.write(f".DEFINE OFF_{row['bank']}_{row['addr']} ${int(row['addr'], 16):04X}\n")

    print(f"wrote {csv_path}")
    print(f"wrote {json_path}")
    print(f"wrote {inc_path}")
    print(
        f"addresses={len(rows)} named={sum(1 for p in all_pc if names.get(p))} "
        f"roots={len(roots)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
