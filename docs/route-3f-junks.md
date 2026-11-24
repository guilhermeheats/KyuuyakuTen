# Rota do JUNKS — Torre de Daedalus, 3F 2ª seção

Validação feita em **2026-11-21** no build all-AOT `d7c2043a`, com a ROM
japonesa `crc32 c8d286c9` / SHA-256 `ffdc7f…de3b`. Nenhum teleporte foi
usado para chegar à loja; a rota abaixo foi caminhada com o controle.

## Rota a partir da descida do 4F

A descida do 4F em `(22,4)` cai no 3F em `(119,20)`, área `02`.

```text
(119,20)  S  (119,21)
(119,21)  W  (118,21)
(118,21)  S  (118,22)
(118,22)  S  (118,23)
(118,23)  W  (117,23) → (116,23) → (115,23) → (114,23)
              → (113,23) → (112,23)
(112,23)  N  (112,22)
(112,22)  N  (112,21)
(112,21)  E  (113,21)
(113,21)  E  (114,21)
(114,21)  N  (114,20)
(114,20)  W  (113,20)
(113,20)  N  (113,19)
(113,19)  W  (112,19)  ← JUNKS
```

O quarto do Tiamat fica em `(113,22)` e é um beco; a rota acima o
contorna. As salas `(112,20)` e `(113,20)` são quartos vazios: `A` abre o
menu de campo, não a loja.

## Entrada e menu

Entrando em `(112,19)` **de `(113,19)` virado para oeste**, o jogo mostra o
balcão e a saudação:

```text
いらっしゃい・・・
```

O menu é:

```text
何の用？
買う
売る
ステイタスを見る
外に出る
```

## Estoque

| Item | Preço | Descrição |
|---|---:|---|
| ポイズノン | 400 | ポイズンの回復 |
| パララノン | 450 | — |
| ペトラノン | 1000 | — |
| マッスルドリンコ | 1500 | — |
| まりょくのもと | 2000 | 一時的にMPを増幅させる |

Nomes, preços e descrições batem com o guia do teh_lvler (GameFAQs 54063)
e com a referência do snes9x registrada nos Addenda 15/30/31 do log
`2026-11-19-junks-bug.md`: **0 diff** na região de texto.

## Cheats de navegação

Para atravessar os encontros aleatórios foram usados, via debug server:

- HP atual/máximo `999/999` nos dois personagens;
- MP `99/99` na Yumiko;
- stats legítimos de level-up, todos abaixo do teto `35`;
- HP dos inimigos em `1` em `$10B2/$10B4/$10B6/$10B8` (e
  `$10C2/$10C4/$10C6/$10C8`).

O level-up continuou normal e os BONUS foram alocados sem ultrapassar 35.
Nenhuma alteração de EXP, nível ou tabela de upgrade foi feita.

## Checkpoints

- `build-debug/saves/save8.sav` — menu do JUNKS.
- `build-debug/saves/save10.sav` — lista de itens.
- Capturas: `logs/kyuuyaku/junks-2026-11-21/` (fora do repositório).

## Crash separado — instrumentação e race do screenshot

Uma sessão longa teve `signal 11` em uma batalha no 3F. O log original está
em `logs/kyuuyaku/2026-11-21-3f-battle-crash.log` e o relatório em
`build-debug/crash_report_20261121_183909.json`. A mesma batalha, em sessão
nova e sem o cheat de HP dos inimigos, não crashou.

O crash foi instrumentado e a corrida mais provável foi corrigida:

- handler POSIX com `SA_SIGINFO`: `signo`, `code`, `si_addr`, thread e
  `backtrace()` nativo no relatório;
- breadcrumbs de comando do debug server (`debug cmd: ...`), connect/disconnect
  e fases de `savestate begin/done`;
- `cmd_screenshot` agora pausa a main thread no frame boundary, copia o
  render buffer com a thread parada e retoma; fallback com timeout para fases
  modais.

Validação: drill de crash com `signal.signo=11`, `addr=0x0` e backtrace
simbolizado; stress de **1.800+ savestates/loadstates/screenshots** e
reconnects, incluindo **600 screenshots pausados com 0 timeouts**, sem crash.
O RSS estabilizou em ~1,98 GB em idle. O crash original não foi reproduzido;
se recorrer, o novo relatório mostra o último comando e o backtrace nativo.

Os deltas grandes do `stack_balance` são majoritariamente caminhos
NLR/yield/`interp@` (falsos positivos do auditor), não a causa do `signal 11`;
ficam como follow-up de precisão do diagnóstico.

Binário validado: `build-debug/KyuuyakuTen` SHA-256
`f44576c794c73f1a852ea9f22b5415950f0cc0d4c95e76ad132a600a7f35452a`.

## Rota para 2F/1F — em andamento

A escada do 2F não está no bloco do JUNKS (3F bloco #2); ela fica no 3F
bloco #1. A rota normal encontrada até o 4F bloco #1 é:

- checkpoint da 5F em `(8,11)`:
  `E (9,11) → N (9,10) → E (10,10) → S (10,11) → S (10,12) → S (10,13)`;
- em `(10,13)` o jogo pergunta **「階段を降りますか？」**; YES leva ao
  **4F `(19,5)` área 01** (bloco #1);
- a escada em `(8,12)` da 5F é **subida** para o 6F, não a descida;
- no 4F bloco #1:
  `(19,5) → S (19,6) → S (19,7) → W (18,7) → W (17,7) → W (16,7)
  → N (16,6) → … → N (16,1) → E (17,1)`;
- a descida `(18,1)` está sendo testada como tile de evento; a tabela do
  4F diz que ela leva ao 3F `(26,1)`, que é o **bloco #2**. A escada do
  2F (`3F 27,6 → 2F 19,14`) fica no bloco #1, alcançável pelo lado do
  2F/1F ou pelo elevador (parado até o Minotauro).

Checkpoints: `save10` no 4F bloco #1; `save8` no JUNKS; `save11` no 6F.

### Tabela de escadas do ROM (fonte pública)

A tabela derivada do ROM em
<https://pareido.jp/cyber-newtown/megaten-daedalus/nam-mt-dg-0/>
lista as escadas do Daedalus:

```text
4F (18,1) → 3F (26,1)
4F (23,5) → 3F (31,5)
3F (27,6) → 2F (19,14)
2F (18,14) → 1F (26,14)
5F (15,8) → 4F (23,0)
5F (12,15) → 4F (20,7)
```

O 4F tem **dois componentes desconectados**: o #2 é só a sala-escada
`(23,0)`–`(23,5)`, sem o elevador nem a batalha fixa da Harpia; o #1 tem
o elevador `(21,5)`, a Harpia `(18,3)` e as escadas `(18,1)`/`(20,7)`.
O 3F também tem dois componentes: o #2 tem a escada `(26,1)`, a conversa
`(31,0)` e os dois portões; o #1 tem o elevador `(29,5)`, a batalha fixa
do Bug `(28,5)` e a descida do 2F `(27,6)`.

Consequência prática: a sala do JUNKS pertence ao 3F #2. Dá para subir
ao 5F pela sala-escada do 4F #2 (`3F 31,5 ↔ 4F 23,5 ↔ 4F 23,0 ↔ 5F
15,8`), atravessar o 5F e descer em `5F (12,15) → 4F (20,7)`, que cai no
4F #1 — onde ficam o elevador e a rota para o 3F #1.

Validação em jogo (2026-11-21): `3F (118,20)` subiu para `4F (22,5)`;
`4F (23,0)` subiu para `5F (12,8)` (WRAM; offset de -3 em x em relação
às coordenadas da tabela). O binário atual registra o `SIGPIPE` e a flag
de batalha `$7E:0253` no Addendum 50 do log.

### Resultado da tentativa 3F → 2F (2026-11-21)

- `5F (10,13)` desce para `4F (19,5)` (componente #1); a volta é
  `4F (20,5)` → `5F (10,12)`.
- `5F (13,8)` desce para `4F (23,1)` (componente #2); a descida
  `4F (23,5)` não abre prompt nem por A nem por passo sul. O caminho
  até ela é `(23,1) → (22,1) → (22,2) → (22,3) → (23,3) → (23,4) →
  (23,5)`.
- `4F (18,1)` desce para **3F `(113,17)`**, a sala-escada do
  componente #2 (offset local `+87,+16`). A sala só tem a escada de
  volta ao 4F; não conecta ao corredor do JUNKS.
- O elevador do 5F `(11,13)` (WRAM; offset -2 da tabela) e o do 4F
  estão parados: 「邪悪な力によりエレベーターは停止している」.
- O componente #1 do 3F (elevador `(116,21)`, Bug `(115,21)`, escada do
  2F `(114,22)`) está separado por paredes. Chegamos a `(114,22)` pelo
  corredor inferior, mas a célula não responde a A nem a passo sul.
- O seam `(118,18)` não é alcançável a partir de `(118,21)`; a tabela
  do ROM diz que ele só funciona entrando do 1F `(32,2)` para oeste.
- Conclusão: a rota 2F/1F **não foi validada** por esta seção; a
  hipótese anterior (elevador parado até o Minotauro) continua de pé.

### Correção de mapa: JUNKS = 3F #1, escada do 2F perto

A tabela do ROM divide o 3F em dois componentes:

- **#1 (35 células)**: escada do 2F `(27,6)`, elevador `(29,5)`,
  Bug `(28,5)`, conversas `(25,6)/(28,6)` e a subida `(31,5)`.
- **#2 (29 células)**: subida `(26,1)`, conversa `(31,0)` e os dois
  portões `(31,2)/(31,4)` (que só funcionam entrando do 1F).

A seção do JUNKS (WRAM `112..119, 17..23`) é o **#1**, não o #2.
O offset observado é ~`(+87,+15)`:

| Tabela | WRAM provável |
|---|---|
| subida `(31,5)` | `(118,20)` (já usada para o 4F) |
| subida `(26,1)` | `(113,17)` (a sala selada do #2; offset y=+16) |
| Bug `(28,5)` | `(115,20)` |
| elevador `(29,5)` | `(116,20)` |
| escada 2F `(27,6)` | **(114,21) ou (115,21)** |

Ou seja: a escada do 2F deve estar na sala a leste de `(114,21)`,
não em `(114,22)` (a célula testada antes). Próximos testes, a partir
do `save8`:

1. `(114,20) E (115,20) E (116,20)` — sala do Bug/elevador do 3F.
2. `(114,22) E (115,22) N (115,21)` — entrada sul da escada do 2F.
3. Em `(115,21)`/`(116,20)`, A e passo nas quatro direções; o prompt
   de escada/elevador deve aparecer.
4. Se a escada do 2F abrir, descer para 2F `(19,14)` e mapear o 2F/1F.

O elevador do 3F, se operacional, leva a `4F (21,5)`/`2F (21,13)`;
o do 5F já respondeu 「邪悪な力により…停止している」. Testar o do 3F
antes de assumir que todos estão parados.

### 2F encontrado e pouso selado (2026-11-22)

A escada do 2F está em **`(115,22)`**: descer de `(115,21)` abre o
prompt 「階段を降りますか？」 e leva a **2F `(19,13)`**. O pouso
`(19,13)` é selado (N/W/E paredes); S em `(19,14)` volta ao 3F. O
labirinto do 2F — escada do 1F `(18,14)`, elevador `(21,13)` — não é
acessível por esse pouso; deve ser alcançado pelo lado do 1F (subida
`1F (26,14) → 2F (18,14)`) ou pelo elevador.

O elevador do 4F #1 `(21,5)` está atrás do tile da escada do 5F
`(20,5)`; o elevador do 3F #1 `(116,20)` está atrás de paredes a
partir do JUNKS. O 2F/1F continua sem rota validada por enquanto.

### Auditoria da rota 2F (2026-11-22)

- A partir do `save8` (JUNKS, `(113,19)`), a rota até `(114,22)` foi
  refeita: `S (113,20) → E (114,20) → S (114,21)`, depois
  `W (113,21) → W (112,21) → S (112,22) → S (112,23) → E (113,23) →
  E (114,23) → N (114,22)`.
- Em `(114,22)`, Leste é parede; `S (114,23) → N (114,22)` é uma
  passagem de mão única que entra numa área 3 (view `0x11`) sem saída
  para a escada. `N` de `(114,22)` e `E` de `(114,20)` também são
  bloqueados.
- O auto-map local mostra o quarto do Bug/elevador/escada do 2F
  (`(115,20)`, `(116,20)`, `(115,21)`, `(115,22)`) no lado isolado,
  separado por parede do corredor do JUNKS. A única ligação visível é
  a passagem de mão única que leva ao fundo cego.
- Teleporte diagnóstico para `(19,13)` e `(115,21)` não carregou o
  contexto do 2F (o HUD permaneceu 3F e a view não mudou); escrever a
  área `0x865` para forçar a seção corrompeu o estado
  (`(3,0)`, flag `0x03`) e foi revertido com `load_state`.
- Teste de controle no 4F `(20,5)` (escada do 5F): o prompt abre e
  `B`, `down+A` ou esperar mantêm a posição em `(20,5)`. Leste continua
  parede, então o elevador `(21,5)` não é alcançável por esse lado. Isso
  confirma que o NO deixa o jogador no tile de escada; o mesmo pode
  valer para o tile `(19,14)` do 2F, mas o teste ainda depende de um
  estado real do 2F.
- Conclusão: o teste do prompt NO em `(19,14)` continua **pendente**.
  Para fazê-lo é preciso um estado real do 2F (obtido pelo 1F ou por
  um emulador de referência) ou encontrar o evento que abre o quarto
  do Bug/elevador a partir do 3F.

### Tentativa 4F `(18,1)` e emulador de referência (2026-11-22)

- A rota documentada até a escada do 4F `(18,1)` para em `(17,1)`:
  Leste é bloqueado; Norte leva a `(17,0)` e o loop do auto-map mostra
  seções/áreas sobrepostas. Sul de `(18,0)` e de `(19,0)` também é
  bloqueado. A escada não foi alcançada pelo lado oeste/norte testado.
- Uma batalha aleatória em `(16,3)` foi encerrada sem crash; o `save10`
  foi restaurado em `(19,5)`.
- O `snesref` foi montado em `/tmp/opencode/snesref` com o core
  Snes9x 1.63 (não versionado) e o `save.srm` do recomp. O título é a
  seleção I/II; o SRAM **não** é carregado no título — o load é pelo NPC
  de save in-game. O core e o binário do snesref continuam fora do
  repositório.

### BFS do 4F #1 e novo teste do snesref (2026-11-22)

- BFS com savestates de slot no processo temporário: **81 estados**,
  cobrindo `x=16..22`, `y=0..7`. A escada `(18,1)` **não foi
  alcançada**; Leste de `(17,1)`, Sul de `(18,0)`/`(19,0)` e Sul de
  `(18,3)` são bloqueados. A batalha disparada em `(18,3)` foi
  encerrada e o Sul continuou parede.
- Conclusão provável: o tile `(18,1)` é uma **subida de mão única** do
  3F para o 4F; a rota documentada de descida pelo 4F não existe.
- No `snesref`, o novo jogo foi levado até a cidade (`(0,0)`) com
  nome/stats scriptados. O Elder em `(0,2)` abre apenas o menu de campo
  em N/S/E/W; a interação de save/load do NPC ainda não foi localizada.
- O teste do prompt NO em `(19,14)` continua pendente; a rota 2F/1F
  precisa de um mapa/vídeo de referência ou de um trace da transição
  de escada.

### 5F/6F e o caminho para o 4F #2 (2026-11-22)

- O prompt do 4F `(20,5)` funciona: o primeiro `A` abre
  `階段を昇りますか？` e o segundo confirma YES → 5F `(10,12)`.
- BFS do 5F: 36 estados no lado oeste (`x=8..11`, `y=9..13`); a escada
  `(15,8)` não foi alcançada. O lado direito do 5F está separado por
  paredes/batalhas fixas.
- O 4F `(20,7)`/`(21,7)` é um corredor sem subida utilizável; a porta
  escura em `(21,7)` leva a `(22,7)` e não ao 5F. A rota
  `4F (20,7) → 5F (12,15)` parece ser só descida.
- `save11` (6F `(2,11)`) carrega; HP foi elevado para 999 no processo
  temporário. A rota `E,E,S,S` para em `(5,11)`; o caminho
  `W,S,S,E` chega a `(5,13)`, onde há um **NPC azul** com a mensagem
  sobre as 4 raças de demônios, não o elevador. O elevador do 6F
  `(5,13)` ainda não foi acionado; testar as células/direções ao redor.

### 2F — pouso (19,13) não é selado e NO em (19,14) (2026-11-23)

- O `save6` carrega no **2F `(19,13)`** área `01`, view `209`,
  facing N. **N → `(19,12)`** é aberto: o pouso **não** é selado; a
  rota do 2F começa por N, não pela escada S.
- **S → `(19,14)`** abre o prompt da escada para o 3F. **B** ou
  **Down+A (NO)** cancelam e voltam a `(19,13)`; **A (YES)** desce
  para **3F `(115,21)`**. O NO não abre caminho alternativo.
- Mapa do 2F (SVG Pareido): escada do 1F **`(18,14) → 1F (26,14)`**,
  escada do 3F `(19,14)`, elevador `(21,13)`, batalha fixa Nekomata
  `(23,10)`, baú `(18,11)`, conversas `(18,12)`/`(20,14)`.
- O 2F é um labirinto dependente de **área/view/facing**, não um grid
  simples. A rota estática do mapa (a mesma do `2f_path`) falha em
  `(23,9)` W (parede na área 3). O BFS com snapshots L3 não restaura o
  cursor do beam driver; o BFS com **savestate de slot** restaura, mas
  ainda não fechou a rota do 1F (muitos estados view/facing).
- Conclusão: o pouso do 2F é acessível e o NO está validado; a rota
  `2F (18,14) → 1F (26,14)` continua aberta. Próximo passo: BFS de slot
  com mais estados (ou referência em vídeo) a partir do `save6`, ou
  entrar no 2F pelo lado do 1F.

### 2F — detour da rota estática e limites (2026-11-23)

- A partir do `save6` (`19,13`), a rota do mapa vai por
  `N,N,N,E,N,E,N,E,E,S` até `(23,9)`. O **W** em `(23,9)` é parede
  (área 3), como já observado.
- O desvio **S `(23,10)` → W `(22,10)` → W `(21,10)` → S `(21,11)` →
  E `(22,11)`** funciona; as batalhas no caminho (incluindo a célula
  `(22,11)`) foram vencidas com HP inimigo 1.
- Em `(22,11)`, o **E para `(23,11)` continua bloqueado** (também
  depois da batalha). O **W para `(21,11)`** abre (área 2), mas o
  **S em `(21,11)`** é parede. Com isso, o trecho
  `(23,11) → S (23,12) → W ...` do mapa não é alcançável por esse
  lado, e a rota do 1F não fechou.
- O 2F depende de **área/view/facing e das batalhas**; a rota
  estática do SVG não basta. Continuam como próximos alvos a escada
  do 1F `(18,14)`, o elevador `(21,13)` e, como alternativa, o
  elevador do 3F #1 `(116,20)` ou a entrada pelo lado do 1F.

### 3F #1 — acesso pelo pouso do 2F (2026-11-23)

- O `save6` no 2F `(19,13)` desce pelo prompt S com **YES** para
  **3F `(115,21)`**, o pouso de trás do 3F #1.
- **N → `(115,20)`** (célula do Bug) abre; **E → `(116,20)`** é parede.
  O **A** em `(115,20)`/`(115,21)` abre o menu de campo (COMP), não o
  Bug nem o elevador. **S** volta a `(115,21)`; **E** em `(115,21)`
  também é parede.
- A escada do 2F fica em **`(115,22)`**. O elevador `(116,20)` está
  **atrás da parede leste** quando se vem do pouso do 2F: a frente do
  ～3F #1 é o lado da escada do 4F (`31,5` / WRAM `118,20`), alcançável
  pelo 4F #2/5F, não pelo pouso do 2F.
- A batalha fixa do Bug **não** disparou por esse lado. O elevador do
  3F #1 continua sem confirmação; a rota do 1F segue aberta.

### Tentativas 4F (20,7) e 5F leste (2026-11-23)

- `4F (20,7)`: o **A** abre o menu de campo (COMP); **N/E/S/W** não
  abrem escada. O `5F (12,15) → 4F (20,7)` é uma **descida de mão
  única** (5F→4F); não serve para entrar no 5F pelo 4F.
- `5F (10,12) E` é **parede**; o lado direito do 5F não é alcançável
  pelo oeste/elevador do 5F. O lado direito continua ligado ao ciclo
  **4F #2 (23,0) ↔ 5F (12,8) ↔ 4F (23,5) ↔ 3F (31,5)**, e os elevadores
  seguem parados.
- No 3F #1 pelo pouso do 2F, o **E** de `(115,20)`/`(115,21)` é parede;
  a frente é a escada do 4F `(31,5)`/WRAM `118,20`, e a descida
  `4F (23,5) → 3F (31,5)` não abre (a escada é subida 3F→4F).
- A rota do **1F** continua aberta. Próximo passo recomendado: vídeo/guia
  de referência do Daedalus (2F/1F/5F) ou BFS completo de estados com
  savestates de slot, incluindo as batalhas fixas e o Minotauro.

### 2F → 1F validado (2026-11-23)

- Rota completa a partir do `save6` (2F `19,13`):
  `N,N,N,E,N,E,N,E,E,S` → `(23,9)`;
  `S,S,S` → `(23,12)`;
  `W,W,W` → `(20,12)`;
  `S,S,S` → `(20,15)`;
  `W,W,W,W` → `(16,15)`;
  `N,N` → `(16,13)`;
  `E,E` → `(18,13)`;
  `W` → `(17,13)`;
  `N` → `(17,12)` (prompt 「階段を降りますか？」).
- O corredor leste `x=23` (`y=9→12`) é a passagem correta: `(23,9) S`,
  `(23,10) S` e `(23,11) S` abrem no jogo, embora o SVG do Pareido
  marque parede nesses trechos. A tentativa antiga de `(22,11) E` é
  beco sem saída e não é necessária.
- A descida para o 1F é em **`(17,12)`**, não em `(18,14)` como no
  Pareido/FC. No prompt, **A sozinho / Up+A / Down+A / B** escolhem
  **NO** e voltam a `(17,13)`; **Right+A** (ou Left+A, Up+Up+A,
  Down+Down+A) escolhe **YES** e desce para **1F `(25,9)`**.
- O pouso do 1F é **`(25,9)`**, HUD `1F`, view `241`. O primeiro
  movimento pode parecer travado: pressione **B** (abre o COMP),
  **Start/Select** e então **Up**; o primeiro passo vai para `(25,11)`
  (segure pouco para não andar duas células).
- Em `(25,11)`: `N→(25,10)`, `E→(26,11)`, `W→(24,11)`; `S` é parede.
  A rota ao Minotauro segue o corredor oeste/topo do mapa Sion:
  `W (24,11) → N,N (24,9) → ...`; validação em andamento.
- O `save6` permanece intacto; o estado de 1F é mantido só no processo
  temporário (porta `4415`), sem tocar nos saves do usuário.

### 1F — layout real e rota ao Minotauro (em andamento)

- O pouso do 2F em **`(25,9)`** não é um grid simples: o primeiro
  movimento pode exigir limpar o estado de menu (B/Start/Select). A partir
  dele, `S` leva a `(25,10)`; `E` a `(26,10)`; `N` de `(25,10)` volta ao
  pouso.
- Becos sem saída já validados: coluna oeste `(24,8)–(24,11)` (N até
  `(24,8)`, E/W bloqueados), `(27,10)` (E/N bloqueados; S leva a
  `(27,11)`, que é beco), e `(26,11)`/`(24,11)` para S.
- O 1F também tem **arestas de mão única/estado**: `(26,11) → (27,11)`
  abre, mas `(27,11) → (26,11)` é parede; `(24,10) → (24,11)` abre, mas
  `(24,10) → E/W` não.
- A rota que está funcionando segue o corredor superior:
  `(25,9) E → (26,9) → (27,9) → N (27,8) → E` em direção a `x=31`
  (em validação). A linha azul do BFS do Sion pela coluna oeste não
  corresponde ao collision real do SNES; use a exploração empírica.
- O Minotauro ainda não foi acionado; a célula-alvo do Pareido é
  `(31,10)`, mas o offset SNES é local. O processo temporário segue no
  1F; o principal continua pausado no `save10`.

### 1F — auto-map e componente noroeste (2026-11-23)

- O auto-map do COMP é aberto com **A → A → Down×4 → A**
  (`COMP → オートマッピング`). A tela do mapa aparece mesmo com
  `0x1800 = 0`; use screenshot, não o flag de UI.
- O mapa local confirma que o pouso `(25,9)` e o corredor superior são
  um componente fechado. Rota explorada até o noroeste:
  `(25,9) E (26,9) E (27,9) N (27,8) N (27,7) W (26,7) W (25,7)
  N (25,6) N (25,5) W (24,5) S (24,6) S (24,7)`.
- Becos: `(27,7)` N/E; `(24,6)` W/E; `(24,5)` N/W; `(25,6)` W;
  `(25,5)` E; `(24,7)` W? (não fechado). O componente tem arestas
  dependentes de **view/area** e de mão única; o BFS de slot é o
  método correto.
- Checkpoint local do 1F: `savestate 9` em `(24,6)` restaura
  corretamente (`/tmp/opencode/route5/saves/save9.sav`, fora do repo).
  O processo temporário pode ser encerrado; o principal segue pausado
  no `save10` (4F `19,5`).
- **Minotauro e Valhalla continuam pendentes.** Próximo passo: BFS de
  slot a partir do checkpoint 1F, incluindo as células pretas a
  leste/sul do mapa, ou usar o auto-map para localizar a escada/
  elevador antes de tentar `(31,10)`.

### 4F → 3F #2 e portões (2026-11-23)

- **Rota alternativa que evita o labirinto do 1F:** a partir do `save10`
  em 4F `(19,5)`, o BFS de slot encontrou o caminho até `(18,4)`/`(17,3)`
  (trail registrado no log do BFS: `S S W N W W N N N N E`). O trecho
  final foi validado andando:
  - `(17,3) E → (18,3)` dispara a **Harpy fixa** (`何かが潜んでいた！`);
  - após a batalha, `N → (18,2)`, `N → (18,1)`;
  - em `(18,1)`, o prompt da escada abre com `028c=1`; **Right+A**
    desce para **3F #2 `(113,17)`** (HUD 3F, area 1, view 209).
- Checkpoint local do 3F #2: `savestate 7` em `(113,17)`; o arquivo
  `/tmp/opencode/route5/saves/save7.sav` restaura o estado.
- O 3F #2 é o componente selado de 29 células. O BFS de slot está
  explorando a partir de `(112,17)`/`(113,16)` em direção aos portões:
  `継1 (118,18) → 1F (31,10)` e `継2 (118,20) → 1F (31,12)`. O BFS já
  chegou a `(117,16)`.
- Quando o portão abrir, o passo oeste deve warpar para a célula do
  **Minotauro** no 1F. O próximo marco é o しず玉 e a rota leste para
  Valhalla.
- O `save9` do 1F `(24,6)` e o `save10` do 4F continuam intactos; o
  processo principal segue pausado no `save10`.

### 3F #2 — portões fechados e calibração do mapa Sion (2026-11-24)

- O 3F #2 foi novamente alcançado via 4F `(19,5) → (18,4)` (BFS de slot,
  trail `S S W W W N N N E E`), Harpy `(18,3)` derrotada e escada
  `(18,1)` → **3F #2 `(113,17)`**.
- **継1 `(118,18)`:** andar W não warpa; **継2 `(118,20)`:** inacessível
  a partir de `(118,19)` S, `(117,20)` E e `(119,19)` S. Os dois portões
  são **atalhos 1F → 3F #2**, não saídas do 3F #2. O desvio não leva ao
  Minotauro.
- **Correção do mapa Sion 1F:** a imagem tem **24 colunas** (`x=24..47`,
  células de ~19,3 px), não 32. O bloco oeste é `x=24..31`; o Minotauro
  fica em `(31,10)`, na borda leste; a escada do 2F em `(26,13/14)`.
  A rota vermelha usa a coluna esquerda `x=24`, a linha inferior `y=15`
  e a borda direita `x=31`.
- A parede do 1F em `x=26/27` (WRAM) continua bloqueando o componente
  oeste; a rota do Sion não fecha com a colisão real. O próximo passo
  confiável é a wall table do ROM, não outro BFS cego.
