# Toolchain

## Pin

- WLA-DX **10.9a**;
- commit `86fe2067d6f99cf7b4a765fb8a07d37180ecac92`;
- binários: `wla-65816`, `wla-spc700`, `wlalink`.

O toolchain não é versionado. `tools/bootstrap_toolchain.sh` clona o commit e
compila em `decomp/.toolchain/` (ignorado). Também é possível apontar
`WLA_BIN` para uma instalação existente.

```bash
./tools/bootstrap_toolchain.sh
export WLA_BIN="$PWD/.toolchain/wla-dx/build/binaries"
make toolchain-test
```

## Spike validado

`make toolchain-test` monta e linka:

- `hello65816.s` → ROM de 32 KB, começando com `sei/clc/xce/...`;
- `hello_spc700.s` → binário de 32 KB, começando com `nop/bra`.

Os símbolos exportados (`build/symbols/wla_symbols.inc`) também foram
incluídos num assembly de teste e aceitos pelo WLA-65816.
