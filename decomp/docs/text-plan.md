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
- **Pool `$11` extraído com controles**: `tools/extract_messages.py` lê a
  tabela `$11:$97C0` (66 ponteiros, 63 alvos únicos, 55 mensagens limpas),
  separa texto/controle/raw e grava `build/text/messages.json`. As mensagens
  vão de `$A021` (save) a `$A5A4`; os dois primeiros alvos (`$9844`,
  `$9BFE`) são scripts de evento com bytecode.
- **BPS EN de UI validado ao vivo**: `translations/menu_en.json` tem 73
  entradas (63 fullwidth + 10 font) cobrindo save/load, magia, itens,
  COMP, erros, nomes de cinco itens e o fluxo da loja JUNKS.
- **Loja JUNKS validada ao vivo**: `Welcome`, `WHAT`, `BUY`, `SELL`,
  `STATUS`, `EXIT` e `Later` aparecem no recomp. As opções da loja são
  strings NUL-terminated em `$11:$8FEB`; para caber `SELL` e `STATUS` foi
  preciso remanejar duas strings e atualizar a tabela de ponteiros em
  `$11:$8ECB`. Os patches crus ficam em `translations/raw_en.json`.
- **Lista de compra da loja**: os nomes `PARA`, `PETRA` e `MUSCLE` também
  aparecem na loja (mesma tabela de itens do banco `$06`). O primeiro item,
  `ポイズン`, e a descrição `ポイズンの回復` ainda estão em japonês.
- **Página 8x8 não é ASCII puro na pontuação**: `0x1B` (seria `:`) renderiza
  um glifo parecido com "10"; o label de equipamento usa `EQ` + espaços.
  Letras e dígitos seguem `ASCII - 0x1F`.
- Ferramentas: `tools/vram_tiles.py`, `tools/window_dump.py`,
  `tools/replace_text.py` (ASCII/SJIS/font/fullwidth/raw + BPS),
  `tools/fullwidth.py`, `tools/extract_messages.py`,
  `tools/dump_names.py`.

## Próximos passos

1. Traduzir o restante da loja: nome `ポイズン`, descrições de item e
   prompts de compra/venda/confirmação; validar ao vivo pelo save 8.
2. Traduzir as mensagens de batalha que concatenam nome + verbo
   (`$A433`, `$A4E3`, `$A558`) — o slot não comporta o espaço separador;
   validar ao vivo se o controle `01 0D`/`01 05` insere espaço.
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
