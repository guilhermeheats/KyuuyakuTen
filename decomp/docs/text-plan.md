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
- **BPS EN de UI validado ao vivo**: `translations/menu_en.json` tem 93
  entradas (82 fullwidth + 11 font) cobrindo save/load, magia, itens,
  COMP, erros, nomes de cinco itens, as lojas JUNKS e ARMORS e os prompts
  de escada.
- **Loja JUNKS validada ao vivo**: `Welcome`, `WHAT`, `BUY`, `SELL`,
  `STATUS`, `EXIT` e `Later` aparecem no recomp. As opções da loja são
  strings NUL-terminated em `$11:$8FEB`; para caber `SELL` e `STATUS` foi
  preciso remanejar duas strings e atualizar a tabela de ponteiros em
  `$11:$8ECB`. Os patches crus ficam em `translations/raw_en.json`.
- **Compra e venda validadas**: a lista mostra `CURE`, `PARA`, `PETRA` e
  `MUSCLE`; as descrições saem de `$11:$C1F1+` (`Cure`, `Cure par`,
  `Cure`, `Temp HP up`). O prompt compartilhado de confirmação virou
  `Okay`, o rótulo de venda virou `Sell` e os erros viram `No cash` e
  `No items`. Compra e venda foram testadas ao vivo (Macca 1090 -> 690 ->
  890).
- **Prompts de escada validados**: `$11:$9846` (`Upstairs?`) e
  `$11:$985A` (`Go down?`) aparecem ao usar as escadas do 4F/5F. O save
  10 (4F `(19,5)`) sobe para o 5F `(10,12)` com `Upstairs?`; a escada de
  descida do 5F `(10,13)` mostra `Go down?`.
- **Loja ARMORS (1F) validada**: a saudação virou `Armor, gear` /
  `Fair armor shop`, e os prompts `Need help` e `May I?` aparecem ao
  abrir/voltar ao menu. Os nomes de armadura do banco `$0F` foram
  traduzidos (`CHAIN`, `BREAST`, `IRON`, `HELMET`), mas a lista da loja
  ainda mostra o japonês porque o save 11 tem a tabela de nomes em cache
  na WRAM; o patch da ROM está correto.
- **Rota do 5F**: o checkpoint `save10` + escada do 4F leva ao 5F; a
  exploração com o servidor de debug confirmou o corredor
  `(10,12) -> (10,11) -> (10,10) -> (9,10) -> (8,10)`. A batalha ainda
  não foi encontrada nessa janela; o 5F é o próximo ponto para validar as
  mensagens de batalha.
- **Script principal iniciado**: `translations/script_en.json` tem 90
  entradas (cena inicial, restaurante, baú, batalha, eventos do 7F e a
  narração de Pazuzu em `$10:$9C82-$A209`), `make script-en` gera um BPS
  separado de 2718 bytes. A narração inicial em tela preta
  (`古き言い伝えに曰く…`) é um tilemap pré-renderizado (BG1 em VRAM
  `0x7000`, tiles `0x147F+`), não texto codificado; fica para uma passada
  gráfica.
- **História de abertura no banco $05**: o bloco `$05:D917-$DCE5` tem a
  introdução de Nakajima, Lucifer e Izanami. O extrator acha 28 runs, mas
  alguns começam no meio de palavras porque há controles que inserem
  kanji inline (ex.: `0x89 94 FC` insere 美 antes de `しい天使`). Traduzir
  esse bloco exige interpretar esses controles; ainda não foi feito.
- **Mensagens de batalha validadas ao vivo**: no 7F, os encontros
  mostraram `O GREENSLM came` e `B BASMU came` — prefixo de raça + nome
  T1/T2 em inglês + ` came` —, o prompt `What?`, `Is this okay?`,
  `Foe atk`, `dodged!`, `No damage!`, `ナカジマ's atk` e
  `ナカジマ takes 3 dmg`. A primeira versão do dano
  (`takes 1 damage`) foi cortada na janela de 16 colunas; a tradução foi
  encurtada para `takes N dmg`.
- **Nomes T1/T2 traduzidos**: `translations/names_en.json` tem 396
  entradas (253 T1 + 143 T2), em romaji, conferidas contra a fan
  translation EN. `make names-en` gera um BPS de 4242 bytes que repacka
  as tabelas em `$2E` e redireciona o copy de nome; `make names-inplace`
  gera um BPS de 2769 bytes que reescreve as strings originais (fallback
  para o recomp, mas com 335 nomes truncados pelo slot).
- **Caminho do nome de batalha identificado e corrigido**: o write em
  `$0022` vem de `bank_02_C87B` (`$02:C8D9`, parent `bank_02_BAD4`) —
  código AOT nativo, não das instruções 65816 que o BPS redireciona para
  `$2E`. O `tools/patch-name-tables.py`, chamado pelo `tools/regen.sh`,
  redireciona o C gerado de `$11:CDFD/$11:D5A8/$11:0000` para
  `$2E:B820/$2E:BA1A/$2E:0000`. Depois de regerar/rebuilde, a batalha no
  recomp gravou `ZOMBIE` em `$0022` — nomes completos em inglês.
- **Tabela de batalha mapeada e repackada**: `$11:$A5A4` tem 144
  ponteiros para `$A6C6-$B13D`. `tools/patch_battle.py` separa os runs de
  texto dos controles, substitui só os runs, deduplica blobs e atualiza a
  tabela. O pool original tem 2679 bytes e ficou cheio; a tabela e as
  mensagens foram realocadas para `$29:B820` (tabela) e para os buracos
  livres `$29:B940-$BFFF` e `$29:F820-$FFFF` (3744 bytes). Dois leitores
  de tabela em `$01` são redirecionados (`$01:A9B0/$01:A9C0` e
  `$01:A9E5/$01:A9F3`), o segundo através de um wrapper em `$2E:C000` que
  define `$44 = $29`, preserva o índice em A e volta para `$01:A9EC`.
  `translations/battle_en.json`
  cobre 129 entradas (3675 bytes), incluindo ataque/dano/defesa/crítica,
  comandos, ações dos demônios, status e aflições. As 15 entradas restantes
  são vazias ou só têm controles, então não há mais texto japonês no pool.
  `make battle-en` gera um BPS contra a ROM japonesa.
- **Codificação de 1 byte para batalha (validada no recomp)**: o modo
  `patch_battle.py --encoding byte` grava 1 byte ASCII por caractere. O
  codec em `$11:A6C6` converte ASCII para o código da fonte 8x8
  (`ASCII - $1F`) e chama `$01E311`, o mesmo desenhista usado por raça/nome;
  o caminho de 2 bytes (COMP/história) continua usando `$01DFAD` 16x16. O
  escritor 16x16 corrompe a linha a partir do 8º caractere, por isso a
  batalha usa o 8x8; a linha 8x8 cabe cerca de 16-17 caracteres. Espaços
  avançam `$024E` diretamente, porque `$01E311` ignora o código em branco.
  O interpretador é desviado em `$02:B027` com um `JML` sem frame: o
  dispatcher avança o ponteiro no caminho de 2 bytes e não avança no de
  1 byte, porque `$02:B01B` já consumiu o byte. O pool cai de 3675 para 2087
  bytes no EN e o `battle_pt.json` (129 entradas, PT-BR sem acentos por
  enquanto) usa 1896/3744 bytes. Maiúsculas/minúsculas são dobradas para
  maiúsculas até a página 8x8 com minúsculas ser instalada. Como há patch
  de código, o AOT precisa ser regerado a partir do ROM de 1 byte. O codec
  fica no antigo pool `$11:A6C6-$B13D`, fora da fonte de diálogo; os tails
  `$29`/`$2F` ficam zerados. O dispatcher em `$11:A6E6` olha o ponteiro
  corrente (`$42/$43`) e o banco (`$44`): só ponteiros nos buracos
  repackados `$29:B940-$BFFF` e `$29:F820-$FFFF` usam o codec; COMP,
  história e menus seguem o caminho original de 2 bytes. Não há flag global
  nem wrapper de leitor. O `full-pt` aplica a batalha de 1 byte **depois**
  de `full names`.
- **Continuação do interpretador corrigida (validada)**: o desvio em
  `$02:B027` agora é um `JML` para o dispatcher, sem frame de retorno. O
  caminho de 2 bytes lê o segundo byte, chama `$01:DFAD`, incrementa o
  ponteiro e salta para `$02:B037`; o caminho de 1 byte chama `$01E311` e
  salta direto para `$02:B037`, porque `$02:B01B` já consumiu o byte. O
  COMP/história voltou a renderizar (texto japonês do banco `$05` e
  mensagens de sistema) e a batalha PT mostra as palavras em ASCII. A
  pontuação e os espaços da batalha saem corretos com o desenhista 8x8; as
  entradas PT foram encurtadas para caber no limite de ~16-17 caracteres
  (pool em 1896/3744 bytes), faltando validar os templates com nome/dano.
- **Nomes completos na mesma linha**: o alvo `make full-names` instala
  tabelas completas de raça/nome em `$2E`/`$2F` e rotinas 65816 em
  `$2E:BE90`/`$2E:BF00`. A introdução de batalha passa a mostrar, por
  exemplo, `FOUL GREEN SLIME` — raça completa e nome completo na mesma
  linha, ambos em 8x8 maiúsculo, com um intervalo de uma célula (8 px)
  adicionado pela rotina do nome. É o mesmo tamanho da fan translation; a fan translation tem minúsculas porque
  substitui a página de fonte 8x8, e essa instalação em runtime ainda
  trava no snes9x. A janela de batalha tem uma linha só; duas linhas
  exigiriam redesenhar a janela e ficam para depois. Como as rotinas são
  código, o recomp precisa ser regerado de `full_names.sfc` com
  `tools/regen.sh --rom ... --no-verify`. O alvo `script-en` agora parte de
  `menu_en.sfc`, então o `full_names` inclui UI/menu + script + batalha. O
  BPS `full_names.bps` contra a ROM japonesa tem 17.912 bytes com o pool
  de batalha realocado.
- **Prefixos de raça traduzidos**: o controle `01 0C` chama `$02:BCFA`,
  que lê dois caracteres full-width de `$02:BC8E` (26 entradas de 4
  bytes). Como o slot é fixo em 2 caracteres, `translations/races_en.json`
  usa uma letra + espaço (`T `, `D `, ...), com legenda no README de
  traduções. `tools/patch_races.py` grava a tabela; é data-only e vale
  para o recomp. Validado ao vivo: `O GREENSLM came` e `B BASMU came`.

- **UI/menu em PT-BR**: `translations/menu_pt.json` cobre as 93 entradas
  de `menu_en.json` (lojas, arquivos, magia, item, COMP) dentro dos slots
  fixos; `make menu-pt` gera `menu_pt.sfc`/`menu_pt.bps` (2171 bytes).
- **Script PT-BR**: `translations/script_pt.json` cobre as 90 entradas de
  `script_en.json` (abertura, restaurante, baú, batalha e a narração de
  Pazuzu) em PT-BR sem acentos, dentro do slot fullwidth; os offsets e
  controles são os mesmos do script EN. O alvo `script-pt` gera um BPS
  standalone e o `full-pt` usa esse script no lugar do EN. A validação
  cena a cena no recomp ainda está pendente; a renderização fullwidth é a
  mesma já validada no EN.
- **Raças em PT-BR**: `translations/races_pt.json` mantém as letras de
  prefixo e traduz os nomes completos (TIRANO, FERA, IMUNDO, ...). O
  `full-pt` usa esse arquivo em `patch_races` e `patch_full_names`; os
  nomes próprios dos demônios continuam em `names_en.json`.
- **Texto de inicialização em PT-BR**: `translations/startup_pt.json`
  cobre os 9 prompts de nome dos dois protagonistas (banco `$05`) e as
  duas cópias da instrução de distribuir atributos (banco `$03`) na tela
  de criação de personagem. Os rótulos dos atributos (`ちりょく`,
  `ちから`, ...) ainda estão no japonês.
- O alvo `full-pt` parte de `menu_pt.sfc`, aplica o startup PT, o script
  PT, a batalha PT de 1 byte, os nomes EN e as raças PT, gerando
  `full_pt.sfc`/`full_pt.bps` (16557 bytes). O menu/script usam o motor de
  2 bytes estável; a batalha PT usa o codec 8x8 descrito acima.
- O fallback `names-inplace` não é necessário para o recomp agora.
- **Página 8x8 não é ASCII puro na pontuação**: `0x1B` (seria `:`) renderiza
  um glifo parecido com "10"; o label de equipamento usa `EQ` + espaços.
  Letras e dígitos seguem `ASCII - 0x1F`.
- Ferramentas: `tools/vram_tiles.py`, `tools/window_dump.py`,
  `tools/replace_text.py` (ASCII/SJIS/font/fullwidth/raw + BPS),
  `tools/fullwidth.py`, `tools/extract_messages.py`,
  `tools/dump_names.py`.

## Próximos passos

1. Encurtar as entradas PT de batalha que passam de ~16 caracteres e
   validar os templates com nome/dano. Depois, instalar a página 8x8 com
   minúsculas e acentos para o codec não precisar dobrar caixa; o pool de
   2 bytes/char do EN continua em 3675/3744.
2. Continuar o script principal: cena inicial, restaurante e eventos do
   8F; validar cada novo texto em jogo.
3. Interpretar os controles do banco `$05` (`0x89` + kanji inline) e
   traduzir a história de abertura; o extrator atual fragmenta as linhas.
4. Traduzir a narração inicial em tela preta (`古き言い伝えに曰く…`).
   Ela é um tilemap pré-renderizado (BG1 em VRAM `0x7000`), então exige
   edição gráfica, não o pipeline de texto.
5. Interpretar o bytecode do script (comandos `04`-`08`) para agrupar
   mensagens e evitar operandos no dump.
6. Extrair o script completo e montar o glossário EN.
7. Decidir se o patch traduz os nomes padrão dos personagens
   (`ナカジマ`/`ユミコ`); hoje eles vêm do save.
8. PT-BR direto do japonês, com o inglês como referência.

## Regras

- Texto extraído do jogo **não** é commitado; fica em `decomp/build/text/`.
- A tradução EN da cena é referência de termos, não texto a copiar.
- Nomes próprios seguem o estilo da fan translation.
- Nenhuma ROM traduzida é distribuída; só o patch BPS.
- Mensagens do script: caracteres full-width (2 bytes), padding `U+3000`;
  nunca ASCII puro no meio de uma mensagem.
- Nomes/menus 8x8: `font_code = ASCII - 0x1F`, padding `0x01`, maiúsculas.
