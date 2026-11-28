# Tela de status — mapa gráfico (parcial)

Registro da investigação da tela `ESTADO` (menu da dungeon → `A` →
`ESTADO` → `A`). O painel inferior com os cinco atributos é
pré-renderizado e redesenhado em runtime; este documento fixa os
endereços confirmados e o bloqueio atual.

## Layout

| Item | Endereço | Observação |
|---|---|---|
| Painel BG2 | VRAM `$6C00` | modo 1, 4bpp |
| Char base do painel | VRAM `$3000` | tiles 8x8, 4bpp |
| Rótulos | linhas 22-26, colunas 3-7 | `たいりょく`, `ちりょく`, `つよさ`, `はやさ`, `うん` |
| Fonte | DMA `$0F:AF6A` → VRAM `$6000` | frame 358996, 0x1000 bytes |
| Tilemap | DMA `$7F:2100` → VRAM `$6C00` | frame 359018, 0x800 bytes |

O render direto de BG2 `$6C00` + char base `$3000` reproduz o painel
inteiro, incluindo os rótulos e as barras.

## Rotina do DMA

O DMA do tilemap é iniciado em `$05:9788`:

```
19771: LDX #$6C00 ; STX $2116
19777: LDX #$2100 ; STX $4322
1977D: LDA #$7F   ; STA $4324
19782: LDX #$0800 ; STX $4325
19788: LDA #$04   ; STA $420B
```

Logo depois, a rotina também envia o font page `$0F:DF6A` para a VRAM
`$4000` (0x1000 bytes).

## Trace do renderizador

O buffer `$7F:2100` é temporário, mas no frame **359016** ele contém os
rótulos corretos:

```
$7F:2686: 05 2C 06 2C 07 2C 1E 2C 00 2C 00 2C 00 2C 08 2C ...
```

Esses bytes são escritos pelo **decompressor** (`$01:D5DF/D5EB/D66F/D536`)
entre os frames 359016 e 359020. O DMA do tilemap em `$05:9788` roda no
frame 359018 e copia essa versão para a VRAM.

O painel de detalhe, porém, é redesenhado pelo executor
`bank_00_8760` (CPU `$00:8760`, file `0x0760`) nos frames
**359041/359042**. O executor lê descritores em `$7E:1800+` e copia
para a VRAM; a lista de descritores não é o buffer `$7F:2100`.

## Solução implementada

O asset do painel é **`$07:E998`**, descomprimido para `$7F:0000` pela
chamada em **`0x19720`** (`JSL $01D61B`). Os rótulos ficam em
`$7F:2686` (linhas 22-26) e a página de fonte em `$7F:0100` (tiles
`0x05-0x11`).

`tools/patch_status.py` substitui o `JSL` em `0x19720` por um wrapper
no banco `$2C` que:

1. chama o decompressor original;
2. grava 13 glifos latinos (4bpp) em `$7F:01A0`;
3. grava as cinco linhas de rótulos em `$7F:2686`.

O loader seguinte preenche os bytes altos do tilemap com `$2C` e faz
os DMAs para a VRAM, então os rótulos traduzidos aparecem.

| Item | Endereço |
|---|---|
| Tabela de rótulos | `$2C:BA00` (file `0x163A00`) |
| Glifos 4bpp | `$2C:BA40` (file `0x163A40`) |
| Wrapper | `$2C:BC00` (file `0x163C00`) |
| `JSL` patcheado | `0x19720` |

EN: `VIT / INT / STR / AGI / LUK`.
PT-BR: `VIT / INT / FOR / AGI / SOR`.

Validado no recomp nativo nas duas builds. O layout 4bpp correto é
8 linhas de word0 (16 bytes) seguidas de 8 linhas de word1; o layout
intercalado por linha produz glifos listrados.

