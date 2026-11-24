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
| `$7E0C72`–`$7E0C74` | Macca (3 bytes, little-endian) |
| `$7E0C75`–`$7E0C76` | Magnetita (2 bytes, little-endian) |
| `$7E0D02`–`$7E0D03` | P1 HP atual (16-bit) |
| `$7E0D04`–`$7E0D05` | P1 HP máximo (16-bit) |
| `$7E0D06`–`$7E0D07` | P1 MP atual/máximo (bytes) |
| `$7E0D08`–`$7E0D0D` | P1 stats: **力, 知, 攻, 速, 防, 運** |
| `$7E0D12`–`$7E0D13` | P2 HP atual (16-bit) |
| `$7E0D14`–`$7E0D15` | P2 HP máximo (16-bit) |
| `$7E0D16`–`$7E0D17` | P2 MP atual/máximo (bytes) |
| `$7E0D18`–`$7E0D1D` | P2 stats: **力, 知, 攻, 速, 防, 運** |

O chefe/party usa **seis** stats; o gerador de password do Pareido só
codifica cinco (強,知,攻,速,防) e o sexto (`運`) fica no último byte.
O cheat `P1/P2 Max Stats` do GameHacking.org lista só
`$0D09–$0D0D`/`$0D19–$0D1D` (cinco bytes) e **não inclui a força em
`$0D08`/`$0D18`**.

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

## TODO

- Confirmar quais endereços são de fato P1/P2 (os rótulos dos cheats podem estar trocados).
- Mapear coordenadas do jogador, direção, mapa atual e estado de encontro.
- Mapear ponteiros de party, inventário e demônios.
- Mapear o buffer de texto e o estado da caixa de diálogo.
