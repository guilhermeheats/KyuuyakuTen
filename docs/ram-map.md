# RAM map — rascunho

Este arquivo reúne âncoras iniciais para comparar o recomp com o emulador. Os endereços abaixo vêm de cheats públicos do GameHacking.org; eles servem para localizar variáveis, não como documentação definitiva da engine.

| Endereço | Uso relatado | Observação |
|---|---|---|
| `$7E0C72`–`$7E0C74` | dinheiro / makka (3 bytes) | cheat “999,999 Yen/Makka” |
| `$7E0C75`–`$7E0C76` | magnetita (2 bytes) | cheat “9,999 Magnetite” |
| `$7E0420` | flag de encontros aleatórios | `00` = sem encontros |
| `$7E0D04`–`$7E0D05` | HP do personagem 1 | cheat “P1 Always Has Max 999 HP” |
| `$7E0D09`–`$7E0D0D` | stats do personagem 1 | cheat “P1 Max Stats” |
| `$7E0D14`–`$7E0D15` | HP do personagem 2 | cheat “P2 set max HP to 999” |
| `$7E0D16` | MP do personagem 2 | cheat “P2 Infinite MP” |
| `$7E0D19`–`$7E0D1D` | stats do personagem 2 | cheat “P2 Max Stats” |

## Party struct — confirmado (2026-11-24)

Os cheats acima acertam o **estado**, mas os offsets de stats/HP são
estes (leitura direta na WRAM dos processos de 1F/4F/6F):

| Faixa | Uso |
|---|---|
| `$7E0C72`–`$7E0C74` | Macca (3 bytes, little-endian); a tela mostra 6 dígitos, então o máximo útil é **999.999** |
| `$7E0C75`–`$7E0C76` | Magnetita (2 bytes, little-endian); máximo **9.999** |
| `$7E0D02`–`$7E0D03` | P1 HP atual (16-bit) |
| `$7E0D04`–`$7E0D05` | P1 HP máximo (16-bit) |
| `$7E0D06`–`$7E0D07` | P1 MP atual/máximo (bytes) |
| `$7E0D08` | **P1 LV** (nível, não é stat) |
| `$7E0D09`–`$7E0D0D` | P1 stats: **体, 知, 力, 速, 運** |
| `$7E0D12`–`$7E0D13` | P2 HP atual (16-bit) |
| `$7E0D14`–`$7E0D15` | P2 HP máximo (16-bit) |
| `$7E0D16`–`$7E0D17` | P2 MP atual/máximo (bytes) |
| `$7E0D18` | **P2 LV** (nível, não é stat) |
| `$7E0D19`–`$7E0D1D` | P2 stats: **体, 知, 力, 速, 運** |

Os stats pedidos ficam em:

- **força**: P1 `$0D0B`, P2 `$0D1B`;
- **inteligência**: P1 `$0D0A`, P2 `$0D1A`;
- **sorte/運**: P1 `$0D0D`, P2 `$0D1D`.

A tela STATUS **limita a exibição em 35**: gravar 99 (`0x63`) mostra
35. O cheat salvo usa **35 (`0x23`)**. O `$0D08`/`$0D18` é o **LV**;
não grave stats ali (gravar 30 ali faz o LV virar 30).

### HP dos inimigos

Os slots de HP dos inimigos são **16-bit** em:

```text
$7E10B0 $7E10B2 $7E10B4 $7E10B6 $7E10B8
$7E10C0 $7E10C2 $7E10C4 $7E10C6 $7E10C8
```

O **primeiro inimigo** é `$10B0`/`$10C0`; a lista antiga começava em
`$10B2`/`$10C2` e deixava o primeiro com HP cheio. Gravar `01 00` em
todos os slots durante a batalha mata a todos em um golpe.

## Como usar

1. Abra o jogo no MesenCE/Mesen2.
2. Confira o valor no memory viewer.
3. Faça a mesma leitura no recomp (via debugger ou log).
4. Se os valores não baterem, o problema está antes da variável: banco, ponteiro, DMA ou rotina de menu.

## Confirmado em 2026-11-25

- **P1/P2**: P1 começa em `$7E0D00` (HP `$0D02/$0D04`, MP `$0D06/$0D07`,
  nível `$0D08`, stats `$0D09–$0D0D`); P2 em `$7E0D10` (HP `$0D12/$0D14`,
  MP `$0D16/$0D17`, nível `$0D18`, stats `$0D19–$0D1D`).
- **Jogador**: x `$7E0877`, y `$7E0878`, direção `$7E080F`
  (0=N, 1=L, 2=S, 3=O), área/view em `$7E0865`/`$7E0867`
  (layout exato ainda a confirmar).
- **Batalha**: `$7E0253` diferente de zero durante a batalha; zero no campo.
- **Inventário**: `$7E0C80` em diante; o formato de 1/2 bytes por item ainda
  precisa ser fechado antes de escrever direto.
- **Equipamento**: candidato em `$7E0E15–$7E0E1B` (7 slots). Trocar o BODY
  de Breastplate para Chainmail alterou `$7E0E16/$0E17`; **não escrever**
  nesses bytes até mapear cada slot.
- **Texto/ITEM**: rotinas AOT; nomes e descrições validados no build limpo
  de 2026-11-25.

## TODO

- [x] Confirmar quais endereços são de fato P1/P2.
- [x] Mapear coordenadas, direção e estado de batalha/encontro.
- [ ] Mapear ponteiros de party, inventário e demônios (party e inventário
  parciais; demônios pendente).
- [ ] Mapear o buffer de texto e o estado da caixa de diálogo.
