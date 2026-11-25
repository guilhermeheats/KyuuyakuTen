# Texto e fonte — plano

O detalhamento do que já foi decodificado está em
[`text-encoding.md`](text-encoding.md). Este arquivo guarda o plano de
execução.

## Estado

- Script principal localizado no banco **$10**, em Shift-JIS com códigos de
  controle; extrator inicial em `tools/extract_text.py`.
- Pool de mensagens de sistema no banco **$11** (`$8000` → 21 ponteiros).
- Tabelas de nomes em `$11:$CDFD` (253) e `$11:$D5A8` (143), com fonte 8x8
  em `$0F:AF6B`.
- Buffer/tilemap da janela de texto em `$7E:38E0`; base VRAM `0xF800`.
- Fonte da janela: base VRAM **palavra `0x6000`**, 2bpp, 8x8; o dump de
  VRAM do recomp é row-interleaved (palavra = plano 0 no byte baixo,
  plano 1 no byte alto).
- **ASCII de menu verificado**: `font_code = ASCII - 0x1F`; labels
  `COMP/MAGIC/ITEM/STATUS/ARMORS` vêm de ASCII puro em `$01:A940`.
- Ferramenta de inspeção de tiles: `tools/vram_tiles.py`.
- Ferramenta de substituição in-place + BPS em `tools/replace_text.py`.

## Próximos passos

1. Confirmar se o **renderizador do script Shift-JIS** aceita ASCII direto
   (teste com um diálogo limpo; o menu já usa a mesma janela).
2. Mapear a **tabela Shift-JIS → código de fonte** para kana/kanji.
3. Interpretar o bytecode do script (comandos `04`-`08`) para agrupar
   mensagens e evitar operandos no dump.
4. Extrair o script completo e montar o glossário EN.
5. Gerar o primeiro BPS EN de uma cena curta.
6. PT-BR direto do japonês, com o inglês como referência.

## Regras

- Texto extraído do jogo **não** é commitado; fica em `decomp/build/text/`.
- A tradução EN da cena é referência de termos, não texto a copiar.
- Nomes próprios seguem o estilo da fan translation.
- Nenhuma ROM traduzida é distribuída; só o patch BPS.
