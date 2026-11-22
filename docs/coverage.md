# Cobertura estática e decompilação

Este documento registra a virada do foco para a **decompilação estática**:
aumentar o grafo que o `snesrecomp` descobre e emite em `src/gen/*.c`, em vez
de continuar validando cenas de gameplay. Gameplay e save states continuam
úteis, mas como **regressão**, não como objetivo.

## Linha de base (2026-11-18, antes)

- 9 funções nomeadas em `recomp/symbols.toml`; 7 pedidos AOT.
- 51 entradas no dispatch principal; 54 variantes AOT.
- 8 bancos emitidos; `src/gen` com ~1,3 MB.
- No boot, `interp_stats` mostrava **99,43%** dos ciclos no interpretador
  (LLE) e 0,57% em AOT.

## Captura de cobertura

Build de debug com captura de cobertura:

```bash
SNESRECOMP_TIER2_MANIFEST=/tmp/opencode/coverage/kyuuyaku-tier2.json \
SNESRECOMP_TIER2_JOURNAL=/tmp/opencode/coverage/kyuuyaku-tier2.jsonl \
./build-debug/KyuuyakuTen --no-launcher --coverage-capture=on \
  "$HOME/roms/kyuuyaku.sfc"
```

Foi capturado o boot/título e depois carregados os save states de 8F, 7F,
batalha de Basim e tela de level-up. O `tier2_ingest.py` foi usado para
auditar a captura contra `src/gen/program_manifest.json`:

```bash
python3 snesrecomp/tools/tier2_ingest.py \
  /tmp/opencode/coverage/kyuuyaku-tier2.json \
  --cfg-dir recomp \
  --program-manifest src/gen/program_manifest.json \
  --json > /tmp/opencode/coverage/report.json
```

O relatório do boot mostrou 67 descobertas e 2.270 PCs de instrução
interpretada, com destaque para:

| PC | Interpretações | Uso |
|---|---:|---|
| `$00:93C2/93C5` | 6,3M cada | espera de frame |
| `$3F:C41A/C41D` | 1,64M cada | loop de VBlank/joypad |
| `$38:8145/8148` | 255K cada | espera de acknowledge da APU |
| `$01:D5B3` | 4.557 | helper de texto/menu |
| `$01:D419` | 2.110 | helper de texto/menu |
| `$01:D581` | 2.156 | helper de texto/menu |

## Roots permanentes

Foram adicionadas ao `recomp/symbols.toml` (com `emit = true`) as rotinas
identificadas no caminho quente:

- `MainFrameWait` (`$3F:C411`), `FrameUpdate` (`$3F:C4AA`),
  `PPUUpdate` (`$3F:C4C7`), `APUUpdate` (`$3F:C5B8`);
- `CopyBlock` (`$01:D61B`);
- `TextHelperD419` (`$01:D419`), `TextHelperD581` (`$01:D581`),
  `TextHelperD5B3` (`$01:D5B3`);
- `ScreenOff` (`$01:8066`), `InitPPU` (`$01:80C9`);
- `AddLongCounter` (`$01:8E92`), `ApuCommand` (`$01:EBA5`);
- `FrameWaitWrapper` (`$01:8EAB`), `FrameWait` (`$00:9397`).

Além disso, os roots descobertos pela captura foram gravados como diretivas
`func Coverage_<bank>_<addr>_V<mx>` nos `recomp/bank*.cfg` (fora do bloco
gerado). Eles são placeholders até a função ser nomeada; a lista está nos
bancos `$00`, `$01`, `$02`, `$03`, `$30`, `$38` e `$3F`.

## Resultado

Com `tools/regen.sh` (agora com `--cfg-roots` por padrão):

| Métrica | Linha de base | Depois dos contratos |
|---|---:|---:|
| Roots | 11 | 72 |
| Variantes exatas | 60 | 1417 |
| Variantes AOT-eligible | 54 | 1417 |
| Variantes LLE-only | 6 | 0 |
| Bancos emitidos | 8 | 12 |
| Entradas de dispatch | 51 | 1103 |
| Entradas com AOT | 46 | 1103 |
| Variantes AOT no dispatch | 54 | 1417 |

No mesmo build, após carregar os save states de 8F/7F/batalha/level-up, o
`interp_stats` acumulado mostrou **~94,7% AOT / ~5,3% interpretado** (o boot
isolado fica mais baixo porque a inicialização de APU/PPU é dominada por
esperas de hardware). O `dispatch_total` ficou na casa dos 60 mil, com
`found1` em 100% e zero dispatch misses.

Antes dos contratos de saída, o teste carregando `save4` (level-up) e `save9`
(pós-Basim) ficava em **98,8% AOT / 1,2% interpretado**. Os dois dispatchers
de HDMA (`$00:86C0`/`$00:88CE`) estão em LLE, então o
`unresolved_stub_get` retorna **zero**: o fallback AOT que registrava
`dispatch_oob` não é mais usado. Os dois destravamentos abaixo levaram o
mesmo teste a **99,4–99,9% AOT**.

### Destravamento 1: contrato de saída de `$00:9397`

`$00:9397` é a primitiva de espera de frame. Ela empilha `PHP` na entrada e
restaura com `PLP` em `$93F0`; `PLX` restaura o X do chamador. Portanto a
largura de saída **espelha a largura de entrada**, embora o corpo use
`REP/SEP` internamente. O cfg declara as quatro variantes:

```text
exit_mx_variant 009397 0 0 0 0
exit_mx_variant 009397 0 1 0 1
exit_mx_variant 009397 1 0 1 0
exit_mx_variant 009397 1 1 1 1
```

Isso prova o retorno para todos os chamadores e destrava a análise que antes
parava em `unproven_callee_exit`. O `$02:B0B6` (que chama `$00:9397`) passou
a AOT nas variantes M1X0/M1X1, e o `LevelUp_Apply` (`$01:B3C6`, que chama
`$9397` em M0X1) também foi promovido. O grafo passou de **118 para 339
variantes exatas** e de **105 para 292 AOT**.

### Destravamento 2: `$02:AFF9` e a fronteira de `$05:E5DB`

`$02:AFF9` também começa com `PHP` e seus RTLs em `$B1A7`/`$B1AB` restauram
com `PLP`; `PLX` restaura X. As três variantes de entrada (M0X1/M1X0/M1X1)
retornam com a mesma largura. O contrato:

```text
exit_mx_variant 02AFF9 0 0 0 0
exit_mx_variant 02AFF9 0 1 0 1
exit_mx_variant 02AFF9 1 0 1 0
exit_mx_variant 02AFF9 1 1 1 1
```

Isso permitiu ao decoder continuar depois do `JSL $02AFF9` em `$05:D731`.
A continuação chega a `$05:E556 JMP $E5D9`: no caminho M=1, o terceiro byte
do imediato `LDA #$0001` em `$E5D9` é lido como `BRK` em `$05:E5DB`. O
analyzer trata qualquer `BRK` como `structural_poison` e **descarta todas as
demandas do nó**, o que derrubava o SCC inteiro de 590 para 153 nós.

A correção é uma fronteira de decode de 1 byte em `recomp/bank05.cfg`:

```text
data_region 05 e5db e5dc
```

Ela marca só o byte do `BRK` como não-código. O caminho M=0 válido em
`$E5D9` (`LDA #$0001`, continuação em `$E5DC`) permanece; o caminho M=1 de
erro não contamina o resto do nó. Não é HLE: o runtime AOT/LLE continua
executando os bytes reais; só a análise estática deixa de seguir o caminho
de erro.

Validação de runtime com o build de debug:

- `save4` (level-up): **99,40% AOT / 0,60% interpretado**, zero stubs;
- `save9` (pós-Basim): **99,75% AOT / 0,25% interpretado**, zero stubs;
- título contra o `snesref`: mesmos **6 bytes** de WRAM, SRAM idêntica e
  framebuffer AE 2353 / RMSE 30,29;
- level-up completo + retorno à dungeon: zero stubs;
- `$02:B0B6` tem variantes AOT M1X0/M1X1 no manifesto.

Os nós do ciclo de boot continuam LLE: `$00:9397`, `$00:8014` e `$01:8EAB`
(o `$00:820E` foi promovido). O caminho `$9397 → $8EAB → $8014` é terminal
(o `$8014` termina em `BRA $8113`), então não há contrato de retorno a
inventar para ele.

### Destravamento 3: `$01:8613` (`018613`)

`$01:8613` salva/restaura P e X; o `RTL` em `$8702` restaura ambos. As três
variantes de entrada (M0X1/M1X0/M1X1) retornam com a largura de entrada:

```text
exit_mx_variant 018613 0 1 0 1
exit_mx_variant 018613 1 0 1 0
exit_mx_variant 018613 1 1 1 1
```

O contrato promoveu `$02:D13B` (M1X0/M1X1) e outros chamadores, sem tocar no
caminho de menu do 983C. O A/B com `save9`/`step 60` mostrou **529 AOT / 614
nós / 85 LLE**, AOT **99,89%** e `step 60` em **1,03–1,04s** — o mesmo tempo
do baseline 511. Zero stubs; `save4` em 99,80% AOT e título com os mesmos
6 bytes/SRAM/AE 2353/RMSE 30,29.

### Destravamento 4: cluster `$03:E91A`/`$03:E9B1`

Contratos de saída para `$03:E91A` (M1X0), `$03:E9B1` (M1X1) e para os
callees de folha `$03:EAEE`/`$03:EAFA`/`$03:F415` (M0X0). O cluster promoveu
`$03:E91A` e `$03:E9B1`; `$03:EAEE`/`$03:EAFA`/`$03:F415` continuam LLE
porque ainda chamam `$03:EB06`/`$03:80CA`, mas as larguras de retorno estão
documentadas. O grafo ficou em **615 nós / 532 AOT / 83 LLE**. O A/B de
`step 60` no save9 ficou em **1,03–1,04s**, 99,89% AOT, zero stubs; `save4`
em 99,79% e título com os mesmos 6 bytes/SRAM/AE 2353/RMSE 30,29.

### Destravamento 5: cluster `$03:EB06`/`$03:EEE4` e `$02:AFF9 M0X0`

Contratos para `$03:EB06` (M1X1), `$03:EEE4` (M0X0) e `$03:80CA`
(M1X0/M1X1), mais a variante que faltava no bloco de `$02:AFF9`:
`exit_mx_variant 02AFF9 0 0 0 0`. Sem essa linha, `$03:EEE4` continuava
bloqueado em `unproven_call_at_03EF25_to_02AFF9_m0x0`; com ela, `$03:EEE4`
foi promovido e abriu **71 novos nós**.

Resultado: **690 nós / 603 AOT / 87 LLE**. O A/B de `step 60` no save9 ficou
em **99,90–99,91% AOT**, **1,06–1,09s** (cerca de 3–5% acima do baseline,
não os 12,4x do 983C), zero stubs. `save4` em 99,80% AOT; título com os
mesmos 6 bytes/SRAM/AE 2353/RMSE 30,29.

### Destravamento 6: `$03:8834` e helpers `$00:90EB`/`$00:F160`

Contratos para `$03:8834` (M1X0/M1X1), `$00:90EB` (M1X0/M1X1) e
`$00:F160` (M1X1). Eles promoveram `$03:80CA` (2 variantes) e `$03:F415`,
que eram os dois últimos bloqueios daquele subcluster. Os próprios
`$03:8834`/`$00:90EB`/`$00:F160` continuam LLE com apenas
`truncated_call_continuation`, mas seus chamadores ficaram AOT.

Resultado: **700 nós / 616 AOT / 84 LLE**. A/B de `step 60` no save9:
**99,91% AOT**, **1,05–1,06s**, zero stubs. `save4` em 99,80% AOT; título
com os mesmos 6 bytes/SRAM/AE 2353/RMSE 30,29.

### Destravamento 7: `noreturn_jsl` e o frame wait AOT

`$01:8EAB` tem um `JSL $00:8014` em `$8EBE`; `$00:8014` é o main loop e
**nunca retorna**. O cfg agora declara `noreturn_jsl 8ebe` (bank01) e
`noreturn_jsl 93b4` (bank00, o call site do `JSL $01:8EAB`). A ferramenta
ganhou suporte a `terminal_jsl`/`noreturn_jsl` no cfg_loader, decoder e
emissor Python e no cfg/analyzer/decoder Rust; o delta está em
`patches/snesrecomp-noreturn-jsl.patch` e é aplicado por
`tools/apply-snesrecomp-patch.sh`.

Um atalho anterior (`exit_mx_variant 018EAB 1 0 1 1`) promoveu `$9397`, mas
**quebrou o boot**: o jogo parava em ~795 frames e o título não aparecia. O
`noreturn_jsl` correto mantém o caminho de init terminal e o boot passa.

Resultado: `$00:9397` AOT nas quatro variantes, `$01:8EAB` AOT e `$02:DBB7`
AOT. Com o frame wait AOT, o contrato `$03:983C` deixou de ser lento e foi
adotado: **849 nós / 784 AOT / 65 LLE**. A/B save9: **99,91% AOT**,
`step 60` **1,04–1,06s**; save4 fresco **99,80% AOT**; boot até o título sem
off-rails; título idêntico ao `snesref` (6 bytes/SRAM/AE 2353/RMSE 30,29);
zero stubs.

### Destravamento 8: dispatch `$00:9B04`

Um soak longo no título (frame 666.606) bateu em
`dispatch_oob_$009B04[00FFFF]`, com stack top `bank_00_9A85_M1X1`; o
fallback abandonou a execução e o processo abortou no frame 681.188. O site
é um `JMP ($0000)` com tabela de **32 palavras** em `$9B08`, indexada por
`($0875 & $1F) * 2`. O cfg agora autoriza a tabela:

```text
indirect_dispatch 9b04 32 ptrtail targets:9c59,9b97,...,9c59
```

O `dispatch_oob` nesse site desapareceu do C gerado. O grafo ficou **856
nós / 771 AOT / 85 LLE**; o AOT caiu de 784 porque os 32 destinos incluem
handlers LLE — a prioridade foi eliminar o trap, não inflar o número. O A/B
save9 ficou em **99,91% AOT** e **1,03–1,09s**; boot/título/save4/save9
passaram, zero stubs. O soak de 666k frames não foi repetido (leva horas); a
autorização estática remove o trap e o interpretador executa o dispatch real.

### Destravamento 9: contrato de `$03:A630`

`$03:A630` retorna **M1X0 nas duas variantes** (RTL em `$A7DC`, X limpo).
Contratos:

```text
exit_mx_variant 03A630 1 0 1 0
exit_mx_variant 03A630 1 1 1 0
```

Isso provou o retorno para `$03:983C`, que passou a AOT nas três variantes
(M0X1/M1X0/M1X1). O próprio `$03:A630` continua LLE porque chama
`$00:9077` e `$30:D226`. O grafo ficou **860 nós / 782 AOT / 78 LLE**; A/B
save9 em **99,91% AOT** e **1,02–1,03s**, zero stubs. Boot/título/save4/save9
passaram; título com os mesmos 6 bytes/SRAM/AE 2353/RMSE 30,29.

### Destravamento 10: bloco `$30` e a ponte `$00:9077`

Contratos de saída para `$00:9188`, `$00:947D`, `$00:9077`,
`$30:D226`/`D237`/`D4BF`/`8BF0`/`95CA`/`A20D`/`DD34`/`ECF4` (M1X0),
`$30:D586`/`$30:AFA0` (M0X0), `$05:96A0`, `$01:91DA` e `$02:AFB6`
(M0X0/M1X0), mais `noreturn_jsl b10e` para o `$02:DC53` terminal.

Resultado: `$00:9188`, `$00:947D`, `$00:9077` e `$30:D226` viraram AOT; o
grafo foi para **952 nós / 876 AOT / 76 LLE**. A/B save9 em **99,91% AOT** e
**~1,08s** (um trial inicial 1,27s), zero stubs; boot/título/save4/save9
válidos.

Ainda restam `$03:A630`, `$02:AFF9` e `$02:AFB6` com apenas
`truncated_call_continuation`: o analyzer não trata como terminal uma chamada
a um callee sem saída (por exemplo `$02:DC53` e o JSL `$03:A754`), mesmo com
`noreturn_jsl`. É um falso positivo de ferramenta; o próximo passo é corrigir
esse critério no analyzer.

### Destravamento 11: diagnóstico de chamada truncada

O analyzer passou a emitir a razão detalhada
`truncated_call_at_<site>_to_<alvo>`. Isso revelou dois bloqueios reais:

- `$03:A630` → `$03:A6BE` JSL `$01:8EAB`, que nunca retorna; adicionado
  `noreturn_jsl a6be`.
- `$02:AFF9`/`$02:AFB6` → `$02:B66A` JSL `$04:BE39`; o BRK em `$04:BEC6`
  era o terceiro byte de `LDA #$000B` no caminho M=0. Um
  `data_region 04 bec6 bec7` removeu o falso poison.

Resultado: `$03:A630`, `$02:AFF9`, `$02:AFB6` e `$04:BE39` viraram AOT. O
grafo foi para **1020 nós / 954 AOT / 66 LLE**. A/B save9 em **99,92% AOT** e
**1,05–1,11s** (trial 1 1,64s), zero stubs; boot/título/save4/save9 válidos.

### Destravamento 12: hub `$9A85` e `$94C3`

O `$00:9A85` é o hub de dispatch chamado por `$00:94C3` em três sites M1X1.
O contrato `exit_mx_variant 009A85 1 1 1 1` destravou os chamadores e elevou
o grafo para **1081 nós / 1019 AOT / 62 LLE**. Depois, o `$00:BF53`
(`exit_mx_set 00BF53 M0X0 M0X0,M1X1`) e o `noreturn_jsl 98b5` (`$00:80FB`
entra no main loop e não tem saída local) promoveram o `$00:94C3`, a função
de 616 instruções que o main loop chama.

Resultado final: **1081 nós / 1029 AOT / 52 LLE**. A/B save9 em **99,91%
AOT** e **1,03–1,12s**, zero stubs; boot/título/save4/save9 válidos; título
com os mesmos 6 bytes/SRAM/AE 2353/RMSE 30,29.

### Destravamento 13: handlers `$9A85`/`$A1D8`

`$00:A29D` é um `JSL $05:A718`; o `$05:A718` não tem **nenhuma** saída local
(é terminal). O `noreturn_jsl a29d` removeu o último truncamento dos handlers
`$9A85`/`$A1D8`, que passaram a AOT.

Resultado: **1081 nós / 1031 AOT / 50 LLE**. A/B save9 em **99,91% AOT** e
**1,03–1,04s**, zero stubs; boot/título/save4/save9 válidos.

### Destravamento 14: bloco `$30` (som/gráficos)

O bloco `$30` converge em três hubs: `$30:8770` (M0X0→M0X0) e
`$30:C13B`/`$30:F424` (M1X1→M1X1). Com os três contratos, a cadeia inteira
de handlers foi promovida em cascata. O grafo saltou para **1219 nós / 1197
AOT / 22 LLE**.

Depois, `exit_mx_variant 30877B 1 0 1 0` fechou o último nó: o `$30:8770`
passou a AOT e o bloco `$30` ficou **100% AOT**. Resultado final: **1219 nós
/ 1198 AOT / 21 LLE**. A/B save9 em **99,90–99,91% AOT** e **1,03–1,06s**,
zero stubs; boot/título/save4/save9 válidos; título com os mesmos 6 bytes/
SRAM/AE 2353/RMSE 30,29.

### Destravamento 15: cadeia do banco `$03`

O frame wait `$03:983C` também é chamado com **M0X1** por `$03:B43B` e
`$01:AE08`; os contratos existentes só cobriam M1X0/M1X1. O contrato
`exit_mx_variant 03983C 0 1 0 1` (P/X preservados) liberou a cadeia:

```text
exit_mx_variant 039DBD 0 0 0 0
exit_mx_variant 039DBD 1 0 1 0
exit_mx_variant 03AD87 1 0 1 0
exit_mx_variant 03B3AB 1 1 1 1
exit_mx_variant 03B43B 1 1 1 1
```

A promoção de `$03:B43B` destravou também o cluster `$01` (`$01:91DA`,
`$01:979C`, `$01:97C6`, `$01:986D`, `$01:99B8`, `$01:AE08`, `$01:EE96`)
e o `$00:BF53`. O grafo cresceu para **1228 nós / 1222 AOT / 6
LLE** (+24 AOT e +9 nós). A/B save9 em **99,90–99,91% AOT** e **1,03–1,04s**,
zero stubs; boot/título/save4/save9 válidos.

### Destravamento 16: main loop e fim da fase 1

O `$01:91DA` M1X1 tem duas saídas reais: o RTL normal em `$01:9797` retorna
**M1X1**, e o caminho de cauda em `$01:9582`/`$01:9677` salta para `$01:9798`
em **M1X0** e retorna pelo RTS `$01:97C5`. O contrato
`exit_mx_set 0191DA M1X1 M1X0,M1X1` liberou `$05:931F`, `$05:962D` e
`$05:8CB1`. Depois, `exit_mx_variant 0094C3 1 0 1 1` fechou o `$00:94C3`
M1X0 e o main loop.

Resultado: **1229 nós / 1229 AOT / 0 LLE-only**. A/B save9 em **99,91%
AOT** e **1,033–1,036s**, zero stubs/tier; boot 3728 sem off-rails, título
com os mesmos 6 bytes/SRAM, save4/save9 corretos; campo (`save2`) com 12 mil
frames e zero off-rails/stubs. Restam **4 entradas `force_lle` intencionais**
(reset, NMI, dois HDMA); o LLE quente de campo está em `$00:9300` (0,41% dos
ciclos), fora do grafo AOT. A captura dinâmica não alcançou o `$01:91DA` nos
menus; o contrato veio das duas saídas estáticas e foi validado pelo campo.

### Destravamento 17: as quatro tabelas indiretas

| Site | Tabela | Count | Forma |
|---|---|---:|---|
| `$02:DC74` | `$DC35` | 15 | `idx:X`; a 16ª entrada (`$8B08`) é padding/BRK |
| `$01:C72B` | `$C74E` | 30 | `ptrtail`; o ponteiro é carregado antes do JSR `$C78E` |
| `$01:CD9C` | `$CDB6` | 127 | `idx:X`; a entrada 127 (`$3828`) é inválida |
| `$01:EF15` | `$ED47` | 129 | `idx:X`; as entradas 129/130 (`$8B08`/`$AB4B`) são meio de função/dados |

O `$01:EE49` é o wrapper comum de mensagem e também usa a tabela `$ED47`
em `$01:EE93`; ele é terminal (tail dispatch). Os 12 wrappers do `$C74E`
fazem `JSL $01:EE49` e depois `JMP $C740`; como o `JSL` nunca retorna,
cada site recebeu `noreturn_jsl` (`c81f`…`c98a`). Com os counts corretos,
o veneno dos BRKs `$018B99`/`$018BC5`/`$01ABA1` desapareceu.

Resultado: **+154 nós, todos AOT**. O grafo foi para **1383 nós / 1383 AOT
/ 0 LLE**, com 1089 entradas de dispatch (todas com AOT). A/B save9 em
**99,90–99,91% AOT** e **1,032–1,038s**, zero stubs/tier; boot/título/
save4/save9/batalha/menus válidos.

### Destravamento 18: HDMA `$00:86C0`/`$00:88CE`

Os dois dispatchers de HDMA usam `JMP ($0100)` com o ponteiro montado a
partir de tabelas ROM: `$86FE` (8 alvos: `870E`, `8721`, `8760`, `8782`,
`8791`, `87B8`, `87F3`, `883E`) e `$88EC` (4 alvos: `8916`, `8908`,
`8910`, `88F4`). Declarei os dois sites com `ptrtail targets:` e removi o
`force_lle` de `$86C0`/`$88CE`.

Resultado: **+14 nós, todos AOT**; o grafo foi para **1397 nós / 1397 AOT /
0 LLE**, com 1103 entradas de dispatch. Restam só **2 `force_lle`**
intencionais (reset e NMI). A/B save9 em **99,9064–99,9079% AOT** e
**1,026–1,036s**; boot 3727 sem off-rails/stubs, save4/save9/batalha/menus
válidos. O título ficou com **2353 pixels diferentes (4,10%)**, exatamente
o mesmo framebuffer de referência, e a SRAM idêntica.

### Destravamento 19: variantes reais dos handlers de som

Os seis handlers de som (`$30:9686`, `$30:A326`, `$30:C03F`, `$30:C176`,
`$30:D24D`, `$30:D67D`) tinham só as variantes M1X0/M0X0 no grafo; o
runtime executa **M0X1/M1X1**. Declarei as seis entradas reais como roots,
o que adicionou 20 variantes AOT: **1417 nós / 1417 AOT / 0 LLE**.

As seis instruções `JMP ($80AE,X)` continuam no interpretador porque a
tabela é de ponteiros **16-bit** e o emitter ainda a lê como descritor de
24 bits; o código AOT só casa quando o descritor coincide, senão cai no
interpretador, sem stub. O mesmo vale para `$02:DC53`/`$02:ED38`. São
**8 nós AOT com borda interpretada**, não nós LLE-only. A/B save9 em
**99,9094–99,9109% AOT** e **1,050–1,060s**, zero stubs/tier; boot 3722,
título com os mesmos 2353 pixels/SRAM, save4/save9/batalha/menus válidos.

### Validação de rota: 6F (2026-11-19)

O checkpoint do 6F (slot 12/QUICK, SHA-256
`5e44d02fb4e3d60e7bbc62c461293fe24fca015102d6ccf7faa4f439ac913958`)
foi carregado no build AOT e rodou **780 frames** (600 + 180) com **zero
stubs** e **zero off-rails**. O `step 60` ficou em **1,034–1,039s** e o AOT
acumulado em **98,25–98,59%**.

A captura tier-2 do **estado parado** registrou **7.958.086 instruções** e
**27.808.236 ciclos** interpretados, mas retornou **`discoveries: []`**: o
state em si estava coberto pelo grafo então em **1417 variantes**. O perfil
interpretado do processo é dominado por `$00:9300` (26,4M ciclos, 1,20% da
CPU), seguido dos wrappers do main loop em `$3F:C4xx`; não há site novo de
campo.

Conclusão: o checkpoint parado não é fonte de roots; a **exploração a
partir dele** é (ver o destravamento abaixo). O próximo ganho de cobertura
está na rota do 6F e nos oito `JMP ($80AE,X)`/bancos `$02`.

### Destravamento 20: exploração do 6F (2026-11-19)

A exploração a partir do checkpoint do 6F (slot 12/QUICK) e as batalhas
aleatórias revelaram **quatro variantes ausentes** em `$00`:

| Variante | Origem | Observação |
|---|---|---|
| `$00:8993:M1X0` | call gap em `$00:82DB` | rotina nova do caminho NMI/PPU |
| `$00:86C0:M1X1` | call gap em `$00:82E5` | variante M1X1 do dispatcher HDMA |
| `$00:845B:M1X1` | call gap em `$00:82E8` | variante M1X1 de `$845B` (já tinha M1X0) |
| `$00:8608:M1X0` | call gap em `$00:82C4` | rotina nova de setup |

As capturas foram feitas durante a exploração e as batalhas:

- `/tmp/opencode/coverage-6f-explore/…`: 3 descobertas, 69.858.454
  instruções interpretadas;
- `/tmp/opencode/coverage-6f-roots/…`: 1 descoberta (`$8608`), 306.774.016
  instruções, durante as batalhas longas;
- `/tmp/opencode/coverage-6f-roots2/…` e `coverage-6f-final/…`:
  **`discoveries: []`** depois da promoção.

Resultado: **1421 nós / 1421 AOT / 0 LLE**, **84 roots** e **1106 entradas
de dispatch**. O `step 60` no 6F ficou em **1,036–1,042s**, com AOT
acumulado em **97,83–98,16%** e zero stubs/off-rails. O estado carrega com
o analisador aberto; **B três vezes** volta ao campo.

**Nota de estabilidade:** os primeiros processos de exploração morreram sem
core, stub ou off-rail depois de batalhas longas. A hipótese atual é
**SIGHUP do shell que os lançou**; a validação final usa `setsid nohup` e
ficou estável.

### Destravamento 21: tabela 16-bit `$02:ED4F`

O site `$02:ED4C` é um `JMP ($0000)` depois de montar o ponteiro em DP a
partir de duas leituras `LDA $ED4F,X` / `LDA $ED50,X`, com
`X = (cmd & $1F) * 2`. A tabela é de palavras de 16 bits em `$02:ED4F`,
com **17 entradas válidas** (`$ED71`…`$EDE1`). A diretiva é:

```text
indirect_dispatch 2ed4c 17 idx:X tables:ed4f
```

O emitter divide X por 2 (`entry_size=2`) e emite o switch de 17 casos;
cada stub M0X0 chama `$05:D2CF` e cai no tail comum `$02:EBB9`. Resultado:
os nós `$02:DC53` e `$02:ED38` deixaram de ter `has_lle_indirect_edge`; o
grafo foi para **1460/1460 AOT**, 84 roots e **1142 entradas de dispatch**.

Os seis `$30:*` continuam com `JMP ($80AE,X)`. A investigação mostrou que
`$80AE` **não é uma tabela estática**: no ROM `$30:80AE` o decoder lê
código (`60 00 85 A2…`), a cópia em `$7E:80AE` está zerada nos estados
testados e os valores de X dos seis sites não formam um conjunto
consistente de ponteiros. O dispatch runtime foi implementado no
destravamento 22.

### Destravamento 22: dispatch runtime `$80AE`

Os seis sites foram marcados em `recomp/bank30.cfg` com o helper reservado
`__runtime_indirect__`:

```text
hle_dispatch 969c __runtime_indirect__
hle_dispatch a33c __runtime_indirect__
hle_dispatch c078 __runtime_indirect__
hle_dispatch c19b __runtime_indirect__
hle_dispatch d266 __runtime_indirect__
hle_dispatch d6db __runtime_indirect__
```

O emitter reconhece o marcador e emite, em vez do fallback para o
interpretador:

```c
uint16 _disp_ptr = cpu_read16(cpu, cpu->PB,
    (uint16)(0x80AEu + (uint16)(cpu->X & 0xFFFFu)));
uint32 _disp_target = ((uint32)cpu->PB << 16) | _disp_ptr;
RecompReturn _r = cpu_dispatch_tail_pc(cpu, _disp_target,
    0x30xxxxu, _entry_s, _hrv);
RecompStackPop();
return _r;
```

O helper novo `cpu_dispatch_tail_pc` (em `runner/src/cpu_state.c`):

- se existe corpo AOT para o alvo vivo, herda `_entry_s`/`_hrv` via
  `cpu_tailcall_inherit_return_context` e faz tail-call do corpo;
- se não existe, executa o alvo real com
  `interp_tier_dispatch_tail_ex`, mantendo o mesmo contexto de retorno;
- registra o dispatch no `g_dispatch_log`.

Resultado: **0 nós com `has_lle_indirect_edge`**; o grafo continua
**1460/1460 AOT**, 84 roots e 1142 entradas de dispatch. O teste de emissão
`tests/v2/test_balanced_interp_dispatch.py` cobre o marcador e o código
gerado. O site runtime não foi atingido nas rotas testadas: boot/título, 6F,
menu/status, batalha e texto do 8F. O `func_snap` mostrou que o tick do
motor de som (`$30:95CA`/`$30:95E4`) e os seis handlers nunca são chamados
nessas rotas; o `dispatch_log` também não registra os seis sites. A
implementação foi validada no nível do helper (teste C AOT+LLE) e do
emissor; a execução em jogo fica pendente de uma rota/comando de som que
realmente alcance esse caminho.

## Correções no `tools/regen.sh`

O ganho depende de o regen realmente semear os `func` dos cfgs:

- `--cfg-roots` passou a ser o padrão;
- `--profile-manifest <path>` foi adicionado para semear roots a partir de
  uma captura tier-2;
- `--no-host-root-scan` evita que o `recomp/funcs.h` antigo vire fonte de
  roots duplicados;
- o `funcs.h` é gerado em um caminho temporário **fora** da raiz do projeto
  e só é copiado para `recomp/funcs.h` após o generate. Sem isso, o scanner
  de roots readicionava as declarações antigas e o link-closure falhava com
  28 variantes pendentes.

## Dispatchers de HDMA (mitigados por LLE)

O build anterior registrava dois `dispatch_oob` no `unresolved_stub_get`:

| Site | Alvo | Frame | Stack top |
|---|---|---:|---|
| `$00:86E9` | `$00:FFFF` | 2689 | `Coverage_00_86C0_V10_M1X0` |
| `$00:88E9` | `$00:FFFF` | 3470 | `Coverage_00_88CE_V10_M1X0` |

Os dois sites são `JMP ($0100)` através de um ponteiro em WRAM:

- `$00:86C0` é o parser de tabela de HDMA; lê um índice em `$1800/Y` e uma
  tabela em `$86FE` (`$870E`, `$8721`, `$8760`, `$8782`, `$8791`, `$87B8`,
  `$87F3`, `$883E`);
- `$00:88CE` é o dispatcher de modo de HDMA; lê `$0901` e a tabela `$88EC`
  (`$8916`, `$8908`, `$8910`, `$88F4`).

O `dispatch_oob` era o **fallback estático** do emitter: o corpo AOT não
materializava o alvo vivo e caía no interpretador em `$86E9`/`$88E9`, com um
trace fixo em `$FFFF`. O ponteiro vivo podia ser válido; o aviso não era uma
prova de crash.

Para manter o build honesto e sem falso alarme, as duas funções foram
marcadas com `force_lle 0086C0`/`force_lle 0088CE` em `recomp/bank00.cfg`.
Agora o interpretador executa o `JMP ($0100)` com o ponteiro vivo,
`unresolved_stub_get` retorna **zero** e a rota save4/save9 fica em
**99,4–99,9% AOT / 0,1–0,6% interpretado**. O custo continua sendo duas
funções em LLE; o resto do grafo cresceu para 1417 variantes AOT com os
contratos de saída, as fronteiras `$04:BEC6`/`$05:E5DB`, o frame wait AOT,
o dispatch `$00:9B04`, os lotes do bloco `$30`/`$00:9077`, do hub
`$9A85`/`$94C3`, dos handlers `$9A85`/`$A1D8`, do bloco `$30`, da cadeia
do banco `$03`, do main loop, das quatro tabelas indiretas, dos HDMA e das
variantes reais dos handlers de som.

O próximo passo de decompilação é **modelar esse dispatch vivo no emitter**
(ou declarar `indirect_dispatch` de forma que o link-closure aceite os 8+4
alvos), comparar o caminho com `snesref`/MesenCE e então re-promover as duas
funções. Uma tentativa inicial de `indirect_dispatch ... ptrtail targets:...`
elevou a análise para 131 variantes, mas o link-closure rejeitou 28 variantes
chamadas e não definidas; as diretivas foram revertidas.

## Fronteira atual: 0 nós LLE-only

O grafo descoberto está **100% AOT-eligible: 1460/1460**. Não há mais nó
LLE-only e **nenhum nó com `has_lle_indirect_edge`**. O que resta são
**2 entradas `force_lle` intencionais** (reset e NMI). Os seis handlers de
som `$30:*` usam um **dispatch runtime** documentado: leem `PB:80AE+X` e
chamam `cpu_dispatch_tail_pc` (corpo AOT quando existe, interpretador
quando não). Os sites `$02:DC53`/`$02:ED38` foram resolvidos pela tabela
`$02:ED4F`.

Os HDMA `$00:86C0`/`$00:88CE` são AOT com `ptrtail targets:`; o framebuffer
do título ficou visualmente idêntico ao de referência (2256 pixels
diferentes, 3,93% no lote de 1421).
O perfil de campo (`save2`) mostrou **0,27% dos ciclos** em `$00:9300`, um
caminho LLE fora do grafo AOT (provavelmente ligado ao NMI/PPU/APU); não há
stubs nem off-rails. A tabela `$02:ED4F` foi resolvida e o dispatch runtime
de `$80AE` nos seis `$30:*` foi implementado; falta validá-lo numa rota que
atinja os handlers de som. A rota até o 6F já foi alcançada e validada
(2026-11-19), e a exploração inicial do andar achou 4 variantes novas em
`$00`, mas a rota completa continua pendente.

### Histórico: o gargalo do `$03:983C`

Antes do frame wait AOT, o contrato `$03:983C` subia o grafo para **596 AOT**,
mas o `step 60` ia de 1,03s para **12,79s** (12,4x); o `interp_profile`
mostrava 35M ciclos em `$00:9300` e 5 `tier_hits`. Isso motivou o
`noreturn_jsl` e a promoção de `$00:9397`. Depois do frame wait AOT, o mesmo
contrato foi adotado: **784 AOT** e `step 60` em **1,04–1,06s**. A lição:
AOT% sozinho não basta; o harness de parede e o perfil interpretado dizem
onde está o gargalo.

O próximo passo de maior alavancagem é `$03:A630` (promove `$03:983C`),
depois `$02:DC53`/`$01:91DA` (promovem `$02:AFF9`/`$02:AFB6`) e o bloco
`$30`. Cada contrato passa por `save4`/`save9`/`snesref`/tempo de parede;
BRKs de caminho de erro pedem uma fronteira `data_region`, como `$05:E5DB`.

## Sonda `v2_regen`: dispatches restantes

O pipeline `v2_regen.py` (com o fixpoint de auto-promote/reference-taint) é
rodado como sonda com `--tier-down-stubs`; ele não é o pipeline padrão do
projeto. O antigo overrun `max_insns=12000` em `$02:B0B6` **não era dados
lidos como código**: era uma variante fantasma **M0X1** promovida por um
caller de largura errada, que deslocava os imediatos e decodificava até
estourar. A correção no cfg é explícita:

```text
func Clamp_024E_TierWait b0b6 end:b0fa entry_mx:1,1
force_variant_at 02B0B0 1 1
force_variant_at 02BD87 1 1
```

Na última execução antes dos contratos de saída, o probe emitiu **7/7
bancos** e 797 entradas de dispatch. Ele lista 31 sites indiretos sem tabela
declarada (o banco `$02` contribui `$02:DC74`):

| Site | Forma | Ocorrências | Observação |
|---|---|---:|---|
| `$00:9B04` | JMP (abs) | 4 | banco `$00` |
| `$01:C72B` | JMP (abs) | 4 | banco `$01` |
| `$01:CD9C` | JMP (abs) | 4 | banco `$01` |
| `$01:EF15` | JMP (abs) | 4 | banco `$01` |
| `$02:DC74` | JMP (abs) | 4 | banco `$02`, dentro de `$02:DC53` |
| `$30:969C` | JMP [abs] | 2 | operand `$0080AE` |
| `$30:A33C` | JMP [abs] | 2 | operand `$0080AE` |
| `$30:C078` | JMP [abs] | 2 | operand `$0080AE` |
| `$30:C19B` | JMP [abs] | 2 | operand `$0080AE` |
| `$30:D266` | JMP [abs] | 2 | operand `$0080AE` |
| `$30:D6DB` | JMP [abs] | 1 | operand `$0080AE` |

Os sites `$30:*` compartilham o ponteiro `$0080AE`, provavelmente um
dispatcher comum do motor de som. O probe também rejeitou três alvos
JSR/JSL fora do LoROM (`$30:00A0`, `$30:00BD`, `$30:7EA9`) e registrou um
fold constante-Z em `$00:AA11` (BEQ → fall-through, alvo morto `$00:A998`).
Os dois sites de HDMA (`$00:86E9`/`$00:88E9`) não aparecem nessa lista porque
as diretivas `indirect_dispatch ... ptrtail` os resolvem no probe.

O build padrão (`v2_emit`) ainda usa o fallback LLE nesses 31 sites; eles são
os próximos candidatos a `indirect_dispatch`/tabela. Os caminhos com
`brk_at_*` (`$04:BE39`, `$05:DD6D`) são candidatos a separação código/dados,
não a promoção AOT.

## Rotas validadas — JUNKS 3F

Em 2026-11-21, o JUNKS da 3F 2ª seção foi alcançado caminhando (sem
teleporte) e validado no all-AOT `d7c2043a`: saudação, menu e estoque com
0 diff contra o guia e a referência snes9x. A rota e os dados estão em
`docs/route-3f-junks.md` e `docs/data/daedalus-junks.json`.

O crash `signal 11` de uma sessão longa está documentado à parte
(`logs/kyuuyaku/2026-11-21-3f-battle-crash.log`); a mesma batalha em sessão
nova, sem o cheat de HP dos inimigos, não crashou.

### Crash intermitente do `ApuCommand`

A causa raiz foi o frame de retorno do bounce interpretador → AOT em
`cpu_dispatch_pc_paired`: o bridge empilha o frame clássico, mas o
prólogo AOT amostrava o retorno no layout de tailcall. O fix PC-scoped
(`g_aot_host_return_override`) restaura o `FrameWait`/`ApuCommand` AOT
sem LLE e mantém os savestates. O build final
`04f3a5e1a2ff6770199203d30a8b2fd6d10ce52ee513010d012ab0ebbe592add`
tem **1460 variantes AOT / 0 LLE-only** e passou 72.000 frames de campo,
28.800 frames no padrão do crash antigo e batalha, sem crash. Detalhes em
`docs/crash-apu-command.md`.


## Perfil de memória

O build de debug agora aloca rings de gameplay (~156 MB) em vez de ~3,3 GB;
o perfil cheio continua opt-in. Ver `docs/debug-memory.md`.

## Próximos passos

1. Validar o dispatch runtime `$80AE` numa rota que use os handlers de som
   (`$30:96xx`); o código já está emitido e compila, mas o site não foi
   atingido na rota de 6F/batalha.
2. Validar a tabela `$02:ED4F` numa rota que use comandos de som e, se
   necessário, promover os 17 handlers M0X0 que hoje já têm AOT.
3. Investigar o caminho LLE quente `$00:9300` no campo e no idle (o
   processo longo mostrou 88,9% dos ciclos acumulados) e ver se ele pode
   virar root/AOT; manter o NMI/reset como `force_lle` se necessário.
4. Continuar a captura da rota **a partir do 6F**: o state parado não
   revelou roots, mas a exploração/batalhas já adicionaram 4 variantes em
   `$00`; seguir para o 5F, menus e level-up e ingerir cada captura.
5. Nomear os placeholders `Coverage_*`, principalmente nos bancos `$30`,
   `$38` e `$3F`, e continuar a separação código/dados (`$04:BEC6`,
   `$05:DD6D`).
6. Manter gameplay, save states e comparação com emulador como regressão.
