# O que fica, o que é gerado e o que é referência

Este projeto é **source-only**: o repositório guarda código, ferramentas,
documentação e dados de tradução originais. ROM, assets, C gerado, saves e
capturas ficam fora do git.

## Versionado (fonte)

| Caminho | Conteúdo |
|---|---|
| `src/`, `recomp/`, `recomp-ui/` | Host, configuração de análise e UI |
| `snesrecomp/` | Submódulo do framework, no commit fixado em `framework_pins.txt` |
| `decomp/` | Ferramentas, Makefile, testes, docs e traduções (JSON source-only) |
| `docs/` | Investigação, rotas, checkpoints e fontes de referência |
| `tools/`, `patches/`, `scripts/` | Pipeline e patches locais de build |
| `.github/` | Workflow de release (manual) |
| Raiz | `CMakeLists.txt`, `README.md`, licenças, `rom_identity.txt`, `VERSION` |

## Gerado / ignorado (pode apagar e reconstruir)

| Caminho | Por quê |
|---|---|
| `build/`, `build-aot/`, `build-clang/`, `build-debug/` | Árvores de build CMake |
| `src/gen/`, `recomp/funcs.h` | C gerado a partir da ROM |
| `decomp/build/`, `decomp/.toolchain/` | ROMs/BPS/relatórios e toolchain baixada |
| `*.sfc`, `*.smc`, `*.srm`, `*.sav` | ROM e saves |
| `saves/`, `rom.cfg`, `keybinds.ini`, `config.ini` | Estado local do runtime |
| `last_run_report.json`, `__pycache__/`, `*.pyc` | Artefatos de execução |

`build-debug/` é a árvore jogável atual e contém os saves do usuário; ela é
ignorada, mas **não deve ser apagada sem antes copiar `build-debug/saves/`**.
As demais árvores de build são reproduzíveis.

> Limpeza de 2026-11-26: `build/`, `build-aot/` e `build-clang/` foram
> removidas para liberar ~875 MB. `build-debug/` foi mantida por ser a build
> jogável e guardar os saves; `src/gen/` e `decomp/build/` continuam locais e
> podem ser regenerados.

## Referência local (não versionada)

- `/home/heats-guilherme/roms/kyuuyaku.sfc` — ROM japonesa.
- `/home/heats-guilherme/Games/Snes/Kyuuyaku Megami Tensei/` — fan
  translations EN/PT e ROM japonesa, usadas só como referência de termos e
  grafia.
- `reference/saves/` — cópia dos save states de teste.
- `reference/screenshots/` — capturas de rota/comparação.
- `reference/logs/crash/` — relatórios de crash.
- `reference/` está no `.gitignore` e não vai para o GitHub.

## Patches locais de submódulo

- `patches/snesrecomp-noreturn-jsl.patch` — correção de retorno/JSL.
- `patches/snesrecomp-snesref-state-bridge.patch` — ponte de save state e
  `SNESREF_RECOMP_IN` para o `snesref`.

Aplicar, se necessário:

```bash
git -C snesrecomp apply ../patches/snesrecomp-snesref-state-bridge.patch
```

## Limpeza segura

```bash
# opcional: remover árvores antigas, mantendo build-debug e reference/
rm -rf build build-aot build-clang src/gen

# opcional: limpar artefatos Python
find . -name __pycache__ -type d -prune -exec rm -rf {} +
```

Não remova `build-debug/` sem copiar antes `build-debug/saves/`.
