# Texto e fonte — o que já foi decodificado

Atualizado em 2026-11-25 durante o M1. Nada aqui é texto extraído do jogo:
os dumps ficam em `decomp/build/text/` (ignorado pelo git).

## 1. Script principal (banco $10)

O diálogo do jogo está no banco **$10**, a partir de `$10:$81F0`, em
**Shift-JIS**, intercalado com códigos de controle de 1 byte.

- arquivo: `0x80000 + (addr - 0x8000)`;
- exemplo: `$10:$81F7` → `シェルター内に入りますか？`;
- `0x0F` = quebra de linha dentro da caixa;
- `0x01 0x02` / `0x01 0x03` = início/fim de mensagem (hipótese forte);
- comandos `04`, `05`, `06`, `07`, `08`, `03` etc. têm operandos de tamanho
  variável (ponteiros de 16 bits, flags, ids). O extrator ainda **não
  interpreta o bytecode**; ele separa runs de Shift-JIS por bytes < 0x20.

Ferramenta:

```bash
make text-extract        # decomp/build/text/script_jp.json (+ .jsonl)
```

O extrator:
- varre `$10:$81F0-$FFFF` e `$11:$802A-$CDFD`;
- exige kana para descartar operands que decodificam como kanji aleatório;
- remove o operando duplicado de comandos `08 xx <lo> <hi>` quando o run
  começa exatamente no `<lo> <hi>` repetido (ex.: `父しばらく...` → `しばらく...`).

Limitação conhecida: alguns runs ainda começam no meio de um operando. O
próximo passo é interpretar a tabela de comandos do motor de script.

### Buffer de texto em RAM (descoberto)

Com o save de Valhalla carregado, pressionar **A** abre uma mensagem. O dump
de WRAM mostra:

- `$7E:1FB9-$1FE8` — estado/ponteiros do script;
- `$7E:38E0-$3FFF` — **tilemap da janela de texto** (pares
  `tile, 0x20`); ex.: `f3 20 01 20 24 20 30 20 2e 20 31 20 01 20 e3 20`;
- o mesmo tilemap aparece na VRAM em `0xF8EE`, então a base do mapa é
  `0xF800`.

Os índices de tile da mensagem (`0x24`, `0x30`, `0x2E`, `0x31`) são
**códigos da fonte principal**, não Shift-JIS. A base VRAM da fonte foi
fechada em `0x6000` **em palavras** (word address), 2bpp:

- o dump `*.vram.bin` do recomp é uma lista de palavras de 16 bits; cada
  linha de tile é uma palavra, com **byte baixo = plano 0** e
  **byte alto = plano 1** (formato interno do PPU, não o layout bruto
  byte-a-byte da VRAM);
- tile `N` começa na palavra `base + N*8` (2bpp) ou `base + N*16` (4bpp);
- nessa base, `0x24` = `C`, `0x30` = `O`, `0x2E` = `W`, `0x31` = `P`.
  O save state usado no teste tem uma **janela de teste "COWP"**, então
  ele não serve como diálogo limpo para validar a tradução.

A fonte 8x8 de `$0F:AF6B` também contém ASCII nos códigos baixos:
`0x24 C`, `0x30 O`, `0x2E W`, `0x31 P`, `0x96 A`, `0x8A B` (confirmado
renderizando os tiles). O que falta é a **tabela Shift-JIS → código de
fonte** usada pelo renderizador da caixa de diálogo; é ela que dirá se
podemos escrever ASCII direto no script ou se precisamos reencodar para
os códigos baixos da fonte.

Para inspecionar tiles de um dump:

```bash
python3 tools/vram_tiles.py --vram state.vram.bin --base 6000 \
  --bpp 2 --start 0x24 --count 1
python3 tools/vram_tiles.py --vram state.vram.bin --base 6000 \
  --bpp 2 --count 0x100 --bmp build/text/font_6000.bmp --scale 4
```

Para renderizar a janela inteira (tilemap de `$7E:3800`) de um estado:

```bash
python3 tools/window_dump.py --wram state.wram.bin --vram state.vram.bin \
  --tilemap-base 3800 --font-base 1000 --bpp 2 \
  --out build/text/window.bmp --scale 2
```

### ASCII verificado nos menus

A tabela de labels do menu em `$01:A940` (arquivo `0xA940`) guarda
**ASCII puro**: `COMP`, `MAGIC`, `ITEM`, `STATUS`, `ARMORS`, `WEAPON`.
O renderizador da janela converte ASCII para código de fonte com:

```text
font_code = ASCII - 0x1F
```

Exemplos confirmados no recomp:

| ASCII | Código | Tile |
|---|---|---|
| `C` 0x43 | 0x24 | C |
| `O` 0x4F | 0x30 | O |
| `M` 0x4D | 0x2E | M |
| `P` 0x50 | 0x31 | P |
| `T` 0x54 | 0x35 | T |
| `E` 0x45 | 0x26 | E |
| `S` 0x53 | 0x34 | S |
| espaço 0x20 | 0x01 | vazio |

Teste: trocar `COMP` por `TEST` em `0xA940` mudou o tilemap da janela de
`24 30 2E 31` para `35 26 34 35`. O menu principal (`COMP/MAGIC/ITEM/
STATUS`) e o label da loja de armaduras (`ARMORS`) usam o mesmo caminho.
Letras minúsculas **não** estão nessa página (0x61 → 0x42 cai na página de
kana), então a primeira tradução usa **maiúsculas**.

Falta confirmar se o **renderizador do script Shift-JIS** usa a mesma
conversão para bytes ASCII. O menu usa uma tabela de labels separada; o
script ainda precisa de um diálogo limpo para o teste definitivo.

### Diálogo real e fonte 16x16 (save 8)

O save de debug `build-debug/saves/save8.sav` abre uma janela de diálogo
em `$7E:3B00-$7E:3EFF` (primeira pessoa, 3F). A janela tem uma linha de
texto em **fonte 16x16** composta por 4 tiles 8x8:

```text
topo-esquerda = 0x160   topo-direita = 0x161
baixo-esquerda = 0x1C0  baixo-direita = 0x1C1
```

A fonte 8x8 correspondente está na VRAM em **palavra `0x1000`**, 2bpp.
Lendo os tiles esquerdos (`0x160`, `0x162`, ...) chega-se a
`ありがとうござ`; a string correspondente no script é
`$10:$AD34` = `ありがとうございました`. A mensagem seguinte é
`$10:$AD59` = `お礼といってはなんじゃが` e
`$10:$AD72` = `「塔のカギ」を差し上げましょう`.

Teste importante: patchar `$10:$AD59/$AD72` para ASCII e recarregar o
save 8 **não** alterou o tilemap. O estado salvo já tem o texto do
diálogo em WRAM (cache); o motor não relê a ROM ao avançar. Para validar
ASCII no script é preciso um save **antes** do diálogo, ou fechar e
reengajar o NPC do zero. O save 8 está no meio da conversa e os botões
B/A movem o jogador, então o teste ficou pendente.

### Varredura de saves e teleporte

Varri 29 saves únicos de `build*/saves`. Só os saves em
`(112,19) view=117` (save8 do build-debug e duplicata do build) têm a
janela de diálogo aberta. Não há save **antes** dessa conversa.

Teleportar o save de `(5,13) view=117` para `(112,19) view=117` via
`pokefor $0877/$0878/$080F` funcionou (a posição mudou), mas o A não
reabriu o diálogo: o flag de evento dessa conversa já estava avançado.
O caminho para o teste definitivo é achar/limpar esse flag ou usar um
save anterior ao evento.

### Fonte dinâmica do diálogo

Os códigos `0x160`, `0x162`, ... na tilemap **não são uma página fixa de
fonte**: são slots de tile preenchidos em ordem para a mensagem atual.
Cada caractere 16x16 usa 4 tiles (N, N+1, N+0x60, N+0x61), e o glyph 8x8
é composto a partir da fonte. Isso significa que a conversão
Shift-JIS→código é dinâmica; o que importa para ASCII é o **lookup de
glyph** da fonte de origem, não uma tabela fixa de códigos. A fonte 8x8
conhecida (`$0F:AF6B`) tem ASCII em `0x22-0x3B` (A-Z), então há chance
real de o renderizador aceitar ASCII direto.

O teste de patch da cena de abertura (`$10:$824A-$8395`, 15 linhas) gerou
um BPS de 423 bytes, mas o script de input do recomp não chegou a exibir
essas linhas (a tela de título/entrada de nome consome os botões). O
próximo teste precisa de um save state limpo dentro de uma cena com
diálogo.

## 2. Pool de mensagens de sistema (banco $11)

`$11:$8000` tem uma tabela de **21 ponteiros de 16 bits** para textos em
`$11:$802A+`. Exemplos:

| Endereço | Texto |
|---|---|
| `$11:$8038` | `エレベーターは整備中だ` |
| `$11:$804F` | `もうしばらくかかるぞ` |
| `$11:$80C8` | `ご利用の階を指定して下さい` |
| `$11:$80FD` | `１Ｆへまいります` |

O pool vai até `$11:$CDFD`, onde começam as tabelas de nomes.

## 3. Nomes de demônios (banco $11) e itens (banco $06)

### 3.1 Demônios — duas tabelas no banco `$11`

Duas tabelas de ponteiros de 16 bits:

| Tabela | Endereço | Entradas | Strings | Uso |
|---|---|---|---|---|
| T1 | `$11:$CDFD` | 253 (0..252) | `$CFF7-$D5A7` | `$0CE8 & 0xFF == 0` |
| T2 | `$11:$D5A8` | 143 (0..142) | `$D6C6-$D9E3` | `$0CE8 & 0xFF != 0`, índice limitado a 142 |

O construtor em `$02:C87B`:

1. `A` = id; se `id >= 0xFD`, lê 8 bytes de `$7E:0C40 + (id-0xFD)*8`;
2. senão `X = id*2`;
3. `$0CE8` seleciona T1 ou T2;
4. copia até 8 bytes da string para `$7E:0022`, terminando com `0x00`.

As strings são **códigos de fonte de 1 byte**, não Shift-JIS. A fonte é
1bpp 8x8 em `$0F:AF6B`, 16 bytes por glifo: bytes pares = bitmap, bytes
ímpares = `0xFF` (máscara). Mapa de katakana derivado dos nomes:

```text
0x0E ー   0x0F ゛
0x8C ァ 0x8D ア 0x8E ィ 0x8F イ 0x90 ゥ 0x91 ウ 0x92 ェ 0x93 エ 0x94 ォ 0x95 オ
0x96 カ 0x97 ガ 0x98 キ 0x99 ギ 0x9A ク 0x9B グ 0x9C ケ 0x9D ゲ 0x9E コ 0x9F ゴ
0xA0 サ 0xA1 ザ 0xA2 シ 0xA3 ジ 0xA4 ス 0xA5 ズ 0xA6 セ 0xA7 ゼ 0xA8 ソ 0xA9 ゾ
0xAA タ 0xAB ダ 0xAC チ 0xAD ヂ 0xAE ッ 0xAF ツ 0xB0 ヅ 0xB1 テ 0xB2 デ 0xB3 ト 0xB4 ド
0xB5 ナ 0xB6 ニ 0xB7 ヌ 0xB8 ネ 0xB9 ノ
0xBA ハ 0xBB バ 0xBC パ 0xBD ヒ 0xBE ビ 0xBF ピ 0xC0 フ 0xC1 ブ 0xC2 プ
0xC3 ヘ 0xC4 ベ 0xC5 ペ 0xC6 ホ 0xC7 ボ 0xC8 ポ
0xC9 マ 0xCA ミ 0xCB ム 0xCC メ 0xCD モ
0xCE ャ 0xCF ヤ 0xD0 ュ 0xD1 ユ 0xD2 ョ 0xD3 ヨ
0xD4 ラ 0xD5 リ 0xD6 ル 0xD7 レ 0xD8 ロ
0xD9 ワ 0xDA ヲ 0xDB ン 0xDC ヴ 0xDD ヵ 0xDE ヶ
```

Exemplos que fecham o mapa: `ダークヒーロー` (T1 0), `サタン` (2),
`ルシファー` (3), `ベルゼブブ` (4), `アスタロート` (5), `モロク` (7),
`アスモダイ` (9), `パズス` (11), `アシュラ` (12).

## 3.2 Itens — tabela no banco `$06`

Os nomes de **itens/equipamentos** ficam no banco `$06`:

- tabela de **299 ponteiros** de 16 bits em `$06:$EAFE-$ED54`;
- strings nulas-terminadas em `$06:$ED54-$F59E`;
- entrada 0 vazia; 1 = `ワルサーPPK`, 2 = `ガバメント`, ...
- exemplos: 52 `ケブラーベスト`, 143 `ポイズンダート`, 150
  `マッスルドリンコ`, 279 `ブレストプレート`, 293
  `ケブラーヘルメット`.

Os nomes usam a mesma fonte 8x8 de códigos de 1 byte; alguns itens
especiais usam uma página de kanji/ASCII ainda não mapeada (`{XX}`).
`tools/dump_names.py` gera `t1`, `t2` e `t3` no JSON/CSV do glossário.

## 4. O que a fan translation EN fez (referência)

A tradução EN/PT não traduziu o script no lugar. Ela:

- expandiu a ROM para 2,25 MB e usa o **banco $40** (`$40:8000+` = arquivo
  `0x200000+`) como banco novo;
- substituiu o construtor `$02:C87B` por chamadas a `$40:8850` / `$40:8A00`;
- pôs nomes traduzidos em `$40:9000` (T1) e `$40:9FD0` (T2), 16 bytes por
  entrada;
- realocou o script principal e o pool de mensagens para o banco $40 com
  uma codificação própria.

No banco $40, a fonte 8x8 **inglesa** usa:

```text
0x3C-0x55 = A-Z
0x56-0x6F = a-z
0x7A      = '-'
0x7B      = controle de espaçamento (aparece entre letras de "Y H V H")
```

Exemplo: `3F 56 67 60 7A 43 5A 67 64` = `Dark-Hero`;
`4E 58 6E 61 61 56` = `Scylla`.

Isso é referência de formato, **não texto a copiar**. Nossa tradução usa
nomes originais e texto próprio.

## 5. Estratégia de tradução

Caminho inicial: **substituição ASCII no lugar**, no próprio script japonês.

- Shift-JIS usa 2 bytes por caractere full-width; ASCII usa 1 byte. Uma
  linha de 16 kanji (32 bytes) cabe ~30 letras ASCII.
- O slot original é preservado; o resto é preenchido com espaços (`0x20`).
- Os códigos de controle (`0x0F`, `0x01 0x03` etc.) não são tocados.
- Falta validar que a **fonte principal** tem glifos ASCII. O teste planejado
  é aplicar um patch em uma linha do script (ex.: `$10:$824A`) e comparar o
  framebuffer do recomp antes/depois no mesmo frame.

Ferramenta:

```bash
python3 tools/replace_text.py \
  --translations sample.json \
  --out build/rom/translated.sfc \
  --patch build/rom/translated.bps
```

`sample.json`:

```json
[{"offset": "8024A", "length": 30, "text": "After a while, sleep..."}]
```

Para nomes da fonte 8x8, use `--encoding font` (ASCII → código de fonte,
maiúsculas; padding `0x01`):

```json
[{"offset": "8D6C6", "length": 7, "text": "PINK"}]
```

O tool valida o slot, codifica em ASCII ou Shift-JIS, preenche com espaços e
gera BPS com CRC. O self-test é `python3 tools/replace_text.py --selftest`.

## 6. Próximos passos do M1

1. Fechar a base VRAM e o mapa código→glifo da fonte principal (16x16).
2. Validar ASCII no recomp com um patch de uma linha e diff de framebuffer.
3. Interpretar os comandos do script para agrupar linhas em mensagens.
4. Extrair o script completo para JSON e montar o glossário EN.
5. Primeiro protótipo BPS EN em uma cena curta.
