# M0 — status de execução (2026-11-25)

## Concluído

### Toolchain

- WLA-DX **10.9a**, commit `86fe2067d6f99cf7b4a765fb8a07d37180ecac92`.
- `wla-65816`, `wla-spc700` e `wlalink` compilados localmente.
- `hello65816.s` → ROM de 32 KB; `hello_spc700.s` → binário de 32 KB.
- `wla_symbols.inc` importado por um assembly WLA-65816 sem erro.

### ROM/full-ROM gate

- `make baseline` confere size, CRC32 e SHA-256 contra `rom_identity.txt`.
- ROM japonesa: `crc32 c8d286c9`, SHA-256 `ffdc7f25…`.
- Uma cópia com 1 byte alterado é rejeitada (`rc=1`), comprovando o gate.

### Símbolos

- `make symbols` exporta o grafo do recomp:
  - **1.143 endereços únicos**;
  - **69 roots únicos** (as 84 entradas do manifesto incluem variantes M/X);
  - CSV/JSON e `wla_symbols.inc` com `SYM_<bank>_<addr>` e
    `OFF_<bank>_<addr>`.

### Texto

- `make text` dumpa as tabelas `$11:CDFD` e `$11:D5A8` (63 entradas cada)
  e as strings brutas até `$00` em `decomp/build/text/item_ptrs.json`.
- Ainda é dump bruto: o mapa código→glifo/fonte e a extração/inserção
  completa ficam para o M1.

### BPS

- `bps.py` cria/aplica BPS com SourceRead, TargetRead, SourceCopy e
  TargetCopy, CRCs de source/target/patch e metadados.
- Self-test: insert, identity, shorter e random-edit passam.
- Teste em ROM real: mutação de 16 bytes → patch de **48 bytes**, apply
  roundtrip idêntico em ~0,7 s.

### Mod loader

- Auditoria em `docs/mod-loader-audit.md`: pacotes `.snesmod` são data-only,
  plugins confiáveis estáticos, sem código arbitrário; overlay geral de
  texto/assets ainda é trabalho futuro. Tradução inicial vai por BPS.

## Próximo (M1)

1. Decodificar a codificação de texto/fonte usando as tabelas dumpadas e as
   telas de menu/ITEM/STATUS.
2. Criar `extract_text`/`insert_text` com validação de tamanho e fonte.
3. Montar glossário EN inicial com termos da fan translation.
4. Fazer o build mínimo do decomp para boot/título/menus/texto.
5. Gerar o primeiro BPS EN e validar no recomp/emulador.
