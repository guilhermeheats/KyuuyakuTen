# Texto e fonte — plano

O detalhamento do que já foi decodificado está em
[`text-encoding.md`](text-encoding.md). Este arquivo guarda o plano de
execução.

## Estado

- Script principal localizado no banco **$10**, em Shift-JIS com códigos de
  controle; extrator inicial em `tools/extract_text.py`.
- Pool de mensagens de sistema no banco **$11**; a tabela de ponteiros em
  `$11:$97C0` tem 66 entradas conhecidas e aponta para mensagens contíguas
  separadas por `01 01`.
- Tabelas de nomes em `$11:$CDFD` (253 demônios) e `$11:$D5A8` (143
  demônios); itens/equipamentos em `$06:$EAFE` (299 ponteiros,
  strings em `$06:$ED54-$F59E`), com fonte 8x8 em `$0F:AF6B`.
- Buffer/tilemap da janela de texto em `$7E:38E0`; base VRAM `0xF800`.
- Fonte da janela: base VRAM **palavra `0x6000`**, 2bpp, 8x8; o dump de
  VRAM do recomp é row-interleaved (palavra = plano 0 no byte baixo,
  plano 1 no byte alto).
- **ASCII de menu verificado**: `font_code = ASCII - 0x1F`; labels
  `COMP/MAGIC/ITEM/STATUS/ARMORS` vêm de ASCII puro em `$01:A940`.
- **Diálogo real decodificado**: save 8 abre `ありがとうございました`
  (`$10:$AD34`) numa janela 16x16; fonte 8x8 na VRAM base `0x1000`.
  Patch da mensagem seguinte não mudou a tela porque o save tem o texto
  em cache na WRAM; falta um save antes do diálogo.
- **Texto EN no script validado**: o renderizador lê 2 bytes por caractere
  (Shift-JIS), então ASCII puro vira kanji. A fonte 16x16 tem o bloco
  Latin full-width; traduzir com caracteres full-width mantém o slot e
  renderiza corretamente. Teste ao vivo: `$11:$A187`
  (`どのアイテムを使いますか？`, 26 bytes) → `Which item?` + padding
  `U+3000`, exibido como "Which item?" no recomp.
- **Nome de item validado ao vivo**: `$06:$37216`
  (`マッスルドリンコ`, 8 bytes) → `MUSCLE` com `--encoding font` apareceu
  no menu ITEM do save 11.
- Ferramentas: `tools/vram_tiles.py`, `tools/window_dump.py`,
  `tools/replace_text.py` (ASCII/SJIS/font/fullwidth + BPS),
  `tools/fullwidth.py`, `tools/dump_names.py`.

## Próximos passos

1. Extrair as mensagens do pool `$11` com os controles preservados
   (`01 04` = nome de demônio, `01 05` = item, `0F` = quebra) e montar um
   JSON/CSV de tradução por slot.
2. Traduzir os prompts/menus visíveis no save 11 e gerar o primeiro BPS EN
   de menu.
3. Resolver o evento do save 8 ou obter um save anterior para validar um
   diálogo de história traduzido.
4. Interpretar o bytecode do script (comandos `04`-`08`) para agrupar
   mensagens e evitar operandos no dump.
5. Extrair o script completo e montar o glossário EN.
6. PT-BR direto do japonês, com o inglês como referência.

## Regras

- Texto extraído do jogo **não** é commitado; fica em `decomp/build/text/`.
- A tradução EN da cena é referência de termos, não texto a copiar.
- Nomes próprios seguem o estilo da fan translation.
- Nenhuma ROM traduzida é distribuída; só o patch BPS.
- Mensagens do script: caracteres full-width (2 bytes), padding `U+3000`;
  nunca ASCII puro no meio de uma mensagem.
- Nomes/menus 8x8: `font_code = ASCII - 0x1F`, padding `0x01`, maiúsculas.
