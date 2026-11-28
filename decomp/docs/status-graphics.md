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

## Bloqueio

O buffer `$7F:2100` é temporário: depois do DMA ele é sobrescrito com
`0x086E` repetido. Os rótulos não ficam no tilemap vivo; eles são
redesenhados dinamicamente depois do upload do painel. Um hook no DMA
de `$7F:2100` grava os glifos latinos na VRAM, mas os rótulos são
apagados/redesenhados em seguida.

O display-list em `$07:3ED29` contém os códigos do primeiro rótulo
(`05 00 06 00 07 00 1E 00` = `たいりょく`), mas trocar esses bytes por
`60 00 61 00 62 00 00 00` não alterou a tela de detalhe. O caminho
certo é rastrear o renderizador que escreve os rótulos **depois** do
frame 359018, ou localizar o display-list específico do painel de
status.

## Próximo passo

1. Capturar os writes de VRAM em `$D800-$D9FF`/`$6000-$67FF` com a
   pilha completa (`trace_vram`/`get_vram_trace`) para identificar a
   função que redesenha os rótulos após o DMA.
2. Se for um display-list, localizar a tabela usada pelo painel e
   trocar os códigos dos cinco rótulos por tiles latinos.
3. Caso contrário, hookar a rotina de desenho e substituir os códigos
   no ponto de consumo.
