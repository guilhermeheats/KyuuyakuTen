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
> removidas para liberar ~875 MB. `src/gen/` (C gerado) e `decomp/build/`
> (ROMs/BPS/dumps) também foram removidos; regenere com `tools/regen.sh` e
> com os alvos `make` conforme necessário. `build-debug/` foi mantida por ser
> a build jogável e guardar os saves.
>
> Também foram removidos **2.805 BMPs de teste** da raiz de `build-debug/`
> (~687 MB). Uma seleção de 16 capturas de rota/comparação foi preservada em
> `reference/screenshots/debug/`; a árvore jogável ficou com o binário,
> assets, configs e saves.

## Referência local (não versionada)

- `/home/heats-guilherme/roms/kyuuyaku.sfc` — ROM japonesa.
- `/home/heats-guilherme/Games/Snes/Kyuuyaku Megami Tensei/` — fan
  translations EN/PT e ROM japonesa, usadas só como referência de termos e
  grafia.
- `reference/saves/` — cópia dos save states de teste.
- `reference/screenshots/` — capturas de rota/comparação.
- `reference/logs/crash/` — relatórios de crash.
- `reference/` está no `.gitignore` e não vai para o GitHub.

## Patches de build AOT

`tools/regen.sh` aplica dois ajustes depois de gerar `src/gen`:

- `tools/patch-window-text.py` — força o caminho de glyph style-0 do texto
  da janela;
- `tools/patch-name-tables.py` — redireciona o copy AOT de nomes de
  `$11:CDFD/$11:D5A8/$11:0000` para as tabelas T1/T2 em
  `$2E:B820/$2E:BA1A/$2E:0000`.

O segundo é necessário porque o recomp executa `bank_02_C87B` como código
nativo e não enxerga o patch 65816 do BPS. Depois do regen, rebuilde o
recomp para aplicar.

As mensagens de batalha (`$11`) e os prefixos de raça (`$02:BC8E`) são
dados lidos diretamente da ROM pelo recomp. Os alvos `battle-en` e
`races-en` não precisam de patch no C gerado; o único redirecionamento de
código para texto é o das tabelas T1/T2 em `$2E`.

O alvo `full-names` vai além: adiciona rotinas 65816 novas em `$2E` para
mostrar a raça completa e o nome completo na mesma linha, ambos em 8x8, e
um wrapper em `$2D:F980` que copia 26 tiles minúsculos da tabela
`$2D:FA00` para a VRAM `$C410` antes de desenhar a raça. A janela de
batalha tem uma linha só; a variante de duas linhas exigiria redesenhar a
janela e não é usada. Nesse caso o
`src/gen` deve ser gerado a partir de
`decomp/build/rom/full_names.sfc`, que já contém o patch de código, usando
`tools/regen.sh --rom ... --no-verify`. O baseline japonês continua sendo
verificado separadamente; o BPS final é diffado contra a ROM original.

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
