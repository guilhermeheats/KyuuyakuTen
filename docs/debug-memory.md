# Perfil de memória do build de debug

O build de debug tem rings de instrumentação always-on. Eles não são um
leak: são alocados no boot e o RSS cresce conforme as páginas são tocadas.
O heap real do jogo é pequeno (~51 MB).

## Medição do perfil cheio (antes)

| Item | Tamanho |
|---|---:|
| Frame history (6000 frames) | ~1,16 GB |
| VRAM trace (8M entradas) | ~1,28 GB + 64 MB oracle |
| CPU trace (16M entradas) | 640 MB |
| Boundary audit (1M) | 88 MB |
| OAM write ring (512K) | 32 MB |
| BSS estático (`s_wram_trace` + `s_call_trace`) | ~239 MB |
| Rewind | 21 MB |
| Heap | 51 MB |

RSS observado: **~3,63 GiB**; VmSize ~5,16 GiB; heap ~51 MB.

## Defaults de gameplay (atuais)

| Item | Default |
|---|---:|
| `FRAME_HISTORY_DEFAULT` | 256 frames (~49 MB) |
| `VRAM_TRACE_DEFAULT_ENTRIES` | 256K (~40 MB + ~2 MB oracle) |
| `CPU_TRACE_RING_DEFAULT_ENTRIES` | 1M (~40 MB) |
| `BOUNDARY_RING_DEFAULT_ENTRIES` | 128K (~11 MB) |
| `OAM_WRITE_RING_ENTRIES` | 128K (~8 MB) |

O boot loga o total:

```text
[debug_server] always-on rings total: ~156 MB
```

RSS medido com os defaults: **315 MB em 3 s**, **463 MB em 12 s**,
**489 MB em 24 s**; VmSize ~1,98 GiB.

## Perfil cheio opt-in

Para investigações profundas, os rings antigos continuam disponíveis:

```bash
SNESRECOMP_FRAME_HISTORY=6000 \
SNESRECOMP_VRAM_RING_ENTRIES=8388608 \
SNESRECOMP_CPU_TRACE_RING_ENTRIES=16777216 \
SNESRECOMP_BOUNDARY_RING_ENTRIES=1048576 \
./build-debug/KyuuyakuTen --no-launcher "$HOME/roms/kyuuyaku.sfc"
```

Os rings estáticos de reverse-debug (`s_wram_trace` ~128 MB e
`s_call_trace` ~104 MB) continuam no BSS; são o próximo alvo se for
necessário reduzir ainda mais o RSS de gameplay.

## Stress all-AOT `04f3a5e1` (2026-11-22)

Com o perfil low-memory default, o processo iniciado no `save10` ficou em
**636 MB** de RSS. Após 72.000 frames de campo, estabilizou em **676 MB**
(bloco 30) e permaneceu em **678 MB** depois de 28.800 frames de turn
stress e de uma batalha. Não houve crescimento monotônico depois do
bloco 30 nem OOM.
