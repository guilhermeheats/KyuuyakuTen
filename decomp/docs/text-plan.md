# Texto e fonte — plano inicial

## O que já sabemos

O recomp documenta o item-name builder em `$02:C87B` e as tabelas ROM em
`$11:CDFD`, `$11:D5A8` e `$11:C000` (ver o comentário removido do HLE em
`git show a068a25^:src/gen_stubs.c`).

O `tools/scan_text.py` já faz o dump inicial:

- tabela de ponteiros `$11:CDFD` (63 entradas);
- tabela de ponteiros `$11:D5A8` (63 entradas);
- strings brutas terminadas em `$00`, em `decomp/build/text/item_ptrs.json`.

Os bytes são **códigos de fonte**, não UTF-8/Shift-JIS. O próximo trabalho é
descobrir o mapa código → glifo/caractere e o layout dos menus.

## Próximos passos

1. Relacionar as strings das tabelas com os nomes conhecidos da fan
   translation (apenas referência; não copiar o texto).
2. Mapear os códigos de fonte por frequência/posição e pelas telas de
   menu/ITEM/STATUS.
3. Identificar a fonte (tiles) e os limites de largura por linha.
4. Criar extração/inserção de texto:
   - `extract_text` → JSON/CSV com offsets e códigos;
   - `insert_text` → rebuild com validação de tamanho;
   - glossary EN/PT-BR.
5. Validar no emulador/recomp e comparar com `snesref`.
6. Só então gerar o primeiro BPS patch EN.

## Regras

- Texto extraído do jogo **não** é commitado; fica em `decomp/build/text/`.
- A tradução EN é referência; PT-BR é traduzido do japonês.
- Nomes próprios seguem o estilo da fan translation.
- Nenhuma ROM traduzida é distribuída; só o patch BPS.
