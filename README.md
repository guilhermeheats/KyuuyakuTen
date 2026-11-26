# KyuuyakuTen

**KyuuyakuTen** is a native recompilation project for **Kyuuyaku Megami Tensei**
(JPN), built on
[snesrecomp](https://github.com/RetroPortingToolKit/snesrecomp).

- Repository: <https://github.com/guilhermeheats/KyuuyakuTen>
- Project name: **KyuuyakuTen**
- Game: **Kyuuyaku Megami Tensei** (SNES, Japan, 1995)


> **You must legally own a copy of the game.** No ROM data is distributed with
> this project, in the repository or in any release. The recompiled C is
> generated locally from your own copy and is never committed.

## Status

Scaffolded on 2026-11-16. The build **boots, reaches the title screen, plays
the opening story, accepts the two character names, allocates stats, enters
the first dungeon and the 7F floor**, and validates movement, chest looting,
the status menu, auto-mapping, random and fixed battles, negotiation, game
over, victory/EXP/level-up, equipment and in-game SRAM save/load. The current
focus is **decompilation coverage**: the static graph now emits 1417 AOT
variants across 12 banks (from 54 across 8), with 1417 exact variants and 0
LLE-only, and reaches **99.4–99.9% AOT** on the save4/save9 route. Two
entry points remain intentionally `force_lle` (reset and NMI); the sound
handlers have 8 AOT nodes with a bounded interpreted `JMP ($80AE,X)` edge. `docs/coverage.md` and
`docs/checkpoints.md`.

## ROM identity

| | |
|---|---|
| File | `kyuuyaku.sfc` |
| Publisher | Atlus |
| Developer | Opera House |
| Year | 1995 |
| Mapping | lorom |
| Region | JPN (Japan) |
| Coprocessor | none |
| CRC32 | `c8d286c9` |
| SHA-256 | `ffdc7f254c6d965d481918e7d53a451f94f6b1cb035383ae3dfc8f3b5895de3b` |

`tools/regen.sh` refuses to run against anything else, so a mismatched
revision fails immediately instead of producing subtly wrong output.

## Project docs

- [Development](docs/development.md) — ambiente, estado atual, ferramentas e testes.
- [Roadmap](docs/roadmap.md) — escopo, rotina semanal e primeiros 30 dias.
- [ROM identity](docs/rom-identity.md) — hashes, revisão escolhida e verificação.
- [ROM map](docs/rom-map.md) — vetores e primeiras entradas.
- [RAM map](docs/ram-map.md) — âncoras iniciais de RAM.
- [Checkpoints](docs/checkpoints.md) — cenas para comparar com o emulador.
- [Bring-up log](docs/bring-up-log.md) — o que já foi feito e o que bloqueia.
- [Route 8F](docs/route-8f.md) — rota até a escada para o 7F e a primeira batalha.
- [Debugging](docs/debugging.md) — build com servidor TCP, leitura de WRAM e screenshots.
- [Coverage](docs/coverage.md) — captura tier-2, roots estáticos e stubs de dispatch.
- [Input scripts](tools/scripts/README.md) — cadeia de save states e testes.
- [Linux build deps](docs/linux-build-deps.md) — pacotes no openSUSE Leap 16.
- [Sources](docs/sources.md) — links e projetos de referência.
- [Contributing](CONTRIBUTING.md) — regras para contribuir sem violar direitos autorais.
- [Notices](NOTICE.md) — licenças do projeto, do framework e do launcher.
- [Third-party attribution](THIRD_PARTY_ATTRIBUTION.md) — avisos MIT/ISC completos.

## Build

```sh
git submodule update --init --recursive
bash tools/apply-snesrecomp-patch.sh
PATH="$HOME/.cargo/bin:$PATH" bash tools/regen.sh --rom /path/to/kyuuyaku.sfc
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

`tools/apply-snesrecomp-patch.sh` applies the project's portable
`noreturn_jsl`/`terminal_jsl` patch to the pinned `snesrecomp` submodule; the
submodule itself stays at its public upstream commit. The regen rebuilds the
native analyzer, so the Rust toolchain (`cargo`) must be available.

The ROM does not have to live in the repository — keeping it on your own
drive is the better habit, and `SNESRECOMP_ROM` sets the path once for a
shell. Without either, `tools/regen.sh` finds `kyuuyaku.sfc` at the repo root,
then the path the setup wizard recorded in `rom.cfg`; `.gitignore` blocks
both from ever being committed.

`tools/regen.sh` verifies the ROM, generates `src/gen/*.c`, and re-syncs
`recomp/funcs.h`. Re-run it whenever you change anything under `recomp/`.

## Run

```sh
./build/KyuuyakuTen                     # launcher picks the ROM
./build/KyuuyakuTen /path/to/kyuuyaku.sfc # or name it and skip the launcher
```

With no ROM on the command line the build opens the recomp-ui launcher: a ROM
picker with a verification badge, plus display / audio / input settings. Your
choice is cached in `rom.cfg` beside the executable, so the next launch opens
on it and "Skip launcher on boot" makes it immediate. If the launcher is not
built in (`--no-recomp-ui`), the host falls back to a native file picker.

Either way the ROM is checked against the digests above before anything boots
— a dump that could not have produced this build is refused at the door rather
than mis-executing ten frames in.

## Layout

| Path | What lives there |
|---|---|
| `recomp/` | Analysis input: `bank*.cfg`, `symbols.toml`, generated `funcs.h` |
| `rom_identity.txt` | ROM digests — read by the build, `tools/regen.sh` and CI |
| `src/` | Host code you own: `main.c`, `game_rtl.c` |
| `src/gen/` | Generated C. Never committed — regenerate locally |
| `snesrecomp/` | Framework submodule (owns `lib/recomp-net`, `lib/retcomm-rbengine`) |
| `decomp/` | Decompilation tools, text/translation data, tests and docs |
| `docs/` | Research notes, routes, checkpoints and reference sources |
| `patches/` | Local submodule/build patches |
| `tools/` | `regen.sh`, `patch-window-text.py`, `patch-name-tables.py` and the ROM → C pipeline |
| `scripts/` | `package_release.sh` — player-facing zip |
| `reference/` | Local-only saves/screenshots/logs; ignored by git |
| `framework_pins.txt` | Exact framework commits this project was scaffolded against |

See [`docs/reference-material.md`](docs/reference-material.md) for the
source/generated/reference split and safe cleanup commands.

## Porting from here

The scaffold stops where the game-specific work starts. In rough order:

1. **Make it boot.** `src/game_rtl.c` holds the frame driver. It starts on
   the framework's beam-aligned driver (`snesrecomp/runner/src/beam_frame_driver.h`):
   one frame per PPU field, interrupts taken where the beam latches them,
   the field rasterized from the raster journal. A title whose main loop it
   does not fit replaces those calls with its own driver.
2. **Name things.** Add entries to `recomp/symbols.toml` as you identify
   routines, then re-run `tools/regen.sh`. Set `emit = true` to promote one
   into ahead-of-time analysis; leave it false to keep it interpreted.
   Regen synchronizes the marked blocks in each bank cfg, creating missing
   configs. Only proven variants become AOT code. See `recomp/README.md`.
3. **Resolve dispatch misses.** After every run, deal with unresolved
   indirect targets before anything else — they are the reason a port
   diverges, and they are cheap to fix early.
4. **Never synthesise a result** to get past uncovered code, and never edit
   `src/gen/` by hand. Fix the config or the framework and regenerate.

## Multiplayer

Single player.

## License

This project's own source is **source-available** under the PolyForm
Noncommercial License 1.0.0 in [`LICENSE`](LICENSE). It is **not** an OSI
open-source license and commercial use requires separate permission.

The framework and launcher carry their own terms — see [`NOTICE.md`](NOTICE.md),
[snesrecomp/LICENSE](https://github.com/RetroPortingToolKit/snesrecomp/blob/main/LICENSE),
[snesrecomp/PERMISSIONS.md](https://github.com/RetroPortingToolKit/snesrecomp/blob/main/PERMISSIONS.md)
and [`THIRD_PARTY_ATTRIBUTION.md`](THIRD_PARTY_ATTRIBUTION.md). None of these
licenses covers the game data, which is not distributed here.

## Disclaimer

This is an unofficial, non-commercial preservation and reverse-engineering
project. It is not affiliated with, endorsed by, or sponsored by Atlus, Namco,
Nintendo, Opera House, or any of their subsidiaries. Kyuuyaku Megami Tensei
and all related names and assets are trademarks or copyrights of their
respective owners. No game data is distributed.

## Credits

- [snesrecomp](https://github.com/RetroPortingToolKit/snesrecomp) by Matthew
  Stanley and contributors, which builds on the snesrev ports and LakeSnes.
- [recomp-ui](https://github.com/mstan/recomp-ui) for the launcher.
- The snesrecomp, LakeSnes, snesrev and ares communities for the emulation and
  reverse-engineering foundations.
- The fan translators and the Megami Tensei community for the documentation,
  text tables and test references.
