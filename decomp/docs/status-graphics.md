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

## Hooks testados

- DMA em `0x19788` (fonte `$7F:2100`): o ring de WRAM mostra que esse
  hook **não dispara** no detalhe; o DMA das labels parte de outro
  ponto. Só o decompressor escreve `$7F:2686` (frames 359016-359020).
- Executor em `0x0760`: copia a tabela para `$7F:2100` antes do
  executor, mas os rótulos continuam ausentes — o descritor das linhas
  22-26 aponta para outro segmento.

O display-list em `$07:3ED29` contém os códigos do primeiro rótulo
(`05 00 06 00 07 00 1E 00` = `たいりょく`), mas trocar esses bytes não
alterou a tela de detalhe.

A sequência `05 2C 06 2C 07 2C 1E 2C` existe na WRAM em `$7F:2686`
somente até o frame 359020. No frame 359042 ela não está mais na WRAM;
o executor das linhas 22-26 lê os códigos de um descritor cuja origem
é ROM (ou um buffer já reciclado). É por isso que os hooks em
`$7F:2100` não seguram o texto.

A página de fonte da VRAM `$3000` vem do asset `$07:E998`,
descomprimido para `$7F:0000` e copiado por DMA (`$7F:0100` →
VRAM `$3000`, `0x1973B`). Os tiles `0x05-0x11` dessa página são os
glifos japoneses dos rótulos.

Hooks testados sem sucesso: `0x19788` (DMA do tilemap), `0x0760`
(executor), `0x1823B` (fonte `$7F:6000` → `$7000`) e `0x1973B`
(fonte `$7F:0100` → `$3000`). A tabela `$07:3ED29` também não é a
fonte do detalhe.

## Próximo passo

1. Decodificar os descritores em `$7E:1800+` (source/dest/size) no
   frame 359042 para achar o segmento que contém as linhas 22-26.
2. Se o source for `$7F:2100`, hookar o ponto exato da cópia; se for
   outro buffer/ROM, patchar a tabela de origem.
3. Alternativa: hookar o executor no ponto em que ele lê o descritor
   das linhas 22-26 e substituir os códigos ali.
