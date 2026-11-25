# Símbolos do decomp

O mapa de símbolos é **gerado** a partir do recomp:

```bash
make symbols
```

Saídas em `decomp/build/symbols/` (ignoradas pelo git):

- `symbols.csv` — banco, endereço, nome, origem, root, variantes M/X,
  instruções e faixa;
- `symbols.json` — o mesmo em JSON;
- `wla_symbols.inc` — constantes WLA-DX `SYM_<bank>_<addr>` (24-bit) e
  `OFF_<bank>_<addr>` (16-bit).

O mapa atual tem 1.143 endereços únicos e 69 roots únicos (as 84 entradas de
root do manifesto incluem variantes M/X). Use-o como referência para nomear
labels no assembly; o decomp define os labels reais no source.

O recomp é a semente, não a fonte final: o mapa mistura nomes de
`recomp/symbols.toml`, roots `Coverage_*` e funções descobertas.
