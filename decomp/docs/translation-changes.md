# Translation change log — EN/PT-BR

Registro das mudanças de tradução para revisão posterior. Não contém a ROM
nem textos longos do jogo; apenas arquivos, contagens, trechos curtos e
resultados de validação. O estado consolidado fica em
[`translation-status.md`](translation-status.md).

## Arquivos de tradução

| Arquivo | Idioma | Entradas | Codificação | Uso |
|---|---|---:|---|---|
| `translations/menu_en.json` | EN | 93 | fullwidth/font | UI, lojas, COMP |
| `translations/script_en.json` | EN | 90 | fullwidth | script `$10` |
| `translations/battle_en.json` | EN | 129 | fullwidth | batalha de 2 bytes |
| `translations/names_en.json` | EN | 396 | font | T1/T2 |
| `translations/races_en.json` | EN | 24 | font | raças |
| `translations/menu_pt.json` | PT-BR | 146 | fullwidth/font/ascii | UI, lojas, COMP, config |
| `translations/script_pt.json` | PT-BR | 90 | fullwidth | script `$10` |
| `translations/battle_pt.json` | PT-BR | 129 | ASCII 1 byte | batalha 8x8 |
| `translations/races_pt.json` | PT-BR | 24 | font | raças |
| `translations/startup_pt.json` | PT-BR | 42 | fullwidth | nomes/atributos + abertura `$05` |
| `translations/startup_raw.json` | PT-BR | 5 | raw | payloads `0x89` inline |
| `translations/stat_labels_en.json` | EN | 5 | raw | rótulos da criação (tilemap) |
| `translations/stat_labels_pt.json` | PT-BR | 5 | raw | rótulos da criação (tilemap) |
| `translations/items_en.json` | EN | 298 | font 8x8 | T3 itens/equipamentos |
| `translations/items_pt.json` | PT-BR | 298 | font 8x8 | T3 itens/equipamentos |
| `translations/descriptions_en.json` | EN | 175 | fullwidth | pool `$11:B4DC` |
| `translations/descriptions_pt.json` | PT-BR | 175 | fullwidth | pool `$11:B4DC` |

## Mudanças recentes (MT1)

### Menu e UI

- Menu principal: `COMP / MAGIA / ITEM / ESTADO`.
- Submenu COMP: `CHAMAR / VOLTAR / LIBERAR / TROCAR / MAPA AUTO / CONFIG /
  ANALISAR`.
- Configuração: `BATALHA / MAGIAS / MAPA AUTO / SOM`; valores
  `RAP/LEN/NOR`, `OFF/ON`, `AUT/FIX`, `STER`.
- Criação de personagem: prompts de nome em PT-BR e `Distribua` na tela
  de atributos.
- Validação: screenshots do recomp nativo; menus e config abrem e
  renderizam sem blocos.

### Abertura do banco `$05`

- 29 runs de Nakajima/Lucifer/Izanami traduzidos em `startup_pt.json`.
- `startup_raw.json` troca os payloads de kanji inline (`0x89 ...`) por
  espaços fullwidth.
- Linhas limitadas a 13 caracteres para caber na janela do filme.
- Trechos validados: `Nakajima`, `criou o prog`, `tomou forma`,
  `Yumiko e ele`, `quase vencer`, `podem voltar?`.

### Script `$10`

- 90 entradas em PT-BR, derivadas do japonês com o script EN como
  referência de termos.
- Texto sem acentos, dentro dos slots fullwidth.
- Inclui abertura/abrigo, Bistro Angry, baús, prompts de batalha e a
  narração de Pazuzu.
- A renderização fullwidth é a mesma já validada no EN; a validação cena
  a cena ainda está pendente.

### Batalha

- Codec de 1 byte/char no antigo pool `$11:A6C6-$B13D`.
- O caminho de 2 bytes usa `$02:B037` e o de 1 byte usa o desenhista 8x8
  `$01E311`; espaços avançam `$024E`.
- Linha 8x8 com ~16-17 caracteres; as entradas PT foram encurtadas para
  caber.
- Validação: `COMANDO?`, `FAZ O QUE?`, `TUDO BEM?`, `SOFRE N DANO`,
  `PERDE N`, `SEM DANO!`, `ESQUIVOU!`.

### Raças

- 24 descritores em PT-BR (`TIRANO`, `FERA`, `IMUNDO`, `SELVAGEM`, ...),
  mantendo as letras de prefixo.

### Itens/equipamentos T3 (banco `$06`)

- A tabela T3 tem 299 ponteiros de 16 bits em `$06:EAFE` e strings
  nulas-terminadas em `$06:ED54+`.
- O novo `tools/patch_items.py` relê os ponteiros/strings do ROM de
  entrada, reempacota o pool a partir de `$06:ED54` (com espaço livre
  até `$06:FFFF`) e atualiza os 299 ponteiros.
- A página de hiragana/dakuten `$3F-$8B` da fonte `$0F:AF6B` foi
  mapeada (incluindo の, つ, る, ぎ, け, ん); `dump_names.py` agora
  decodifica T3 por completo.
- As 298 entradas não vazias foram traduzidas. A entrada 0 é um
  placeholder vazio.
- EN e PT-BR usam códigos de fonte 8x8 (`ASCII - $1F`); nomes longos
  foram abreviados para caber no menu. Exemplos:
  `WALTHER`, `ESCOPETA`, `CANIVETE`, `CIMITARRA`, `NUNCHAKU`,
  `MUSCLE`, `SOMA`, `AMETHYST`, `MACCA`, `KUSANAGI`, `MURAMASA`,
  `SOLOMON`, `HINOKAGU`.
- Validação: pool e ponteiros relidos do ROM final; os nomes PT foram
  renderizados com os tiles reais da fonte `$0F:AF6B`; BPS aplicado
  contra a ROM japonesa e comparado byte a byte.

### Validação da loja e descrições de itens

- Loja JUNKS validada no recomp: a lista de compra mostrou
  `POISON / PARALYZE / PETRIFY / MUSCLE / ESSENCIA` em PT-BR.
- Compra de POISON: 400 MAG descontados (1259 -> 859), confirmação
  `YES/NO` e retorno à lista funcionando.
- A linha de descrição da loja foi validada para os itens visíveis:
  `CURA`, `CURA PAR`, `CURA`, `HP TEMP +` e `MP TEMP +`.
  A descrição MP foi adicionada em `$11:C3F7`.
- O pool longo de descrições é separado do T3:
  - 299 ponteiros **big-endian** de 16 bits em `$11:B4DC`;
  - strings Shift-JIS separadas por `01 01`, por volta de
    `$11:B733-$11:C5xx`;
  - a descrição do MUSCLE fica em `$11:C3DD` e a de HP em `$11:C3F7`;
  - a ordem da tabela de descrições não é necessariamente 1:1 com o T3.
- O prompt japonês da segunda loja (save 8) é cache do save state:
  o ROM PT contém `QUE?` em `$1F739` e o `DEPOIS` em PT aparece ao
  sair. A tabela está aplicada; reentrar na loja redesenha o prompt.

### Pool de descrições de itens (`$11:B4DC`)

- O pool tem **199 segmentos** Shift-JIS separados por `01 01`; os
  299 ponteiros big-endian apontam para eles, com descrições
  compartilhadas entre itens.
- 175 segmentos foram traduzidos:
  - linhas de ataque/defesa compactas (`A2 H1 MF`, `DEF3 F`);
  - efeitos visíveis da loja (`CURA V`, `CURA PAR`, `CURA ST`,
    `HP TEMP +`, `MP TEMP +`);
  - efeitos especiais (`SEM DEM. FRACOS`, `P. ZAN`, `CURA TOTAL`,
    `WARP ENTRADA`, ...).
- Os 24 segmentos restantes são vazios ou placeholders `?????`.
- Novo alvo `descriptions-pt`/`descriptions-en` no Makefile, aplicado
  antes de `startup-pt`/`items-en`.
- Validação na loja JUNKS: as cinco descrições visíveis apareceram em
  PT-BR.

### Itens de efeito estatístico (banco `$0F`)

- `MUSCLE` (マッスルドリンコ), `MANA` (魔力の素), `SOM` (ソーマ),
  `VIT` (体力の香), `INT` (知力の香), `FOR` (強さの香),
  `AGI` (速さの香), `SOR` (運の香), `AMET` (アメジスト).
- Aplicado pelo novo alvo `bank0f-pt`, antes do script no `full-pt`.

### Rótulos de atributos da criação (BG3)

- A tela de criação desenha o painel em BG3 (`$7C00`) com a fonte 8x8
  em `$C000` e scroll vertical 48.
- Os cinco rótulos não são um tilemap estático: a rotina em `$01:B3C6`
  lê um display-list em `$01:B383` e copia blocos de 5 bytes para
  `$7E3800+offset`.
- Cada bloco é `[offset word][5 glyph codes]`; os offsets
  `0508/0548/0588/05C8/0608` correspondem às cinco linhas do painel.
- Os bytes originais eram `5A 3F 85 82 4A` (たいりょく),
  `5C 85 82 4A` (ちりょく), `5F 83 50` (ちから),
  `6A 7F 50` (はやさ) e `41 8B` (うん), com `$01` de padding.
- Foram trocados por códigos ASCII da fonte 8x8 (`ASCII - $1F`), com
  `$01` como espaço: EN `VIT / INT / STR / AGI / LUK`; PT-BR
  `VIT / INT / FOR / AGI / SOR`.
- Validação: screenshot do recomp nativo com a ROM PT final; as cinco
  linhas renderizam alinhadas antes das barras.

### Tela de status e lenda inicial (investigação)

- O botão `X` abre a tela de status; o painel inferior fica em BG2
  `$6C00` e a fonte 8x8 em `$6000`.
- Os rótulos do painel (`たいりょく`, `ちりょく`, `つよさ`, `はやさ`,
  `うん`) não vêm da tabela de strings do banco `$06` em `$B22B`:
  um patch dessa tabela não alterou a tela. O trace mostra que as
  últimas escritas na área dos labels em `$6C00` são `0x00` de
  `bank_05_817A_M1X0`; eles não estão no tilemap BG2 vivo. O painel
  parece pré-renderizado/cacheado e exige edição do tilemap/tiles.
- A lenda inicial é um texto completo de 7 linhas. A camada é **BG3**;
  o tilemap fica em `$6800` (buffer `$7F:0010`, 2 KB, upload por DMA no
  frame 724) e a fonte 16x16 em `$5000` (buffer `$7F:4000`, 4 KB, parte
  do bloco de 24 KB `$7F:0000-$5FFF` copiado para a VRAM `$3000` no
  frame 701).
- O bloco de 24 KB vem de assets comprimidos do banco `$37` (tabela em
  `$37:8000`, blocos em `$37:8012`, `$BD3A`, `$E896`, `$F48D`, ...).
  A decodificação é fatiada em vários frames (630-730) e o destino
  avança de `$7F:0000` até `$7F:5B74`.
- Texto original confirmado por render direto do tilemap/fonte:

  ```
  古き言い伝えに曰く
  かつて
  翼持つ者どもの反乱あり
  けれど彼ら敗れたり
  彼ら栄光を失い
  白き翼もがかれ
  暗き地の底へと堕されたり
  ```

- EN: *An ancient legend tells / of a time when / the winged ones
  rebelled / but they were defeated / they lost their glory / their
  white wings were torn / and they fell into darkness.*
- PT-BR: *Uma antiga lenda conta / de um tempo em que / os alados se
  rebelaram / mas foram derrotados / perderam sua glória / suas asas
  brancas foram / arrancadas na escuridão.*
- Não há string Shift-JIS simples; é um asset gráfico comprimido.
- Implementado: `tools/patch_legend.py` grava um tilemap 8x8 e 32 tiles
  latinos no espaço livre do banco `$2A` (`0x153820`/`0x157820`) e
  instala dois hooks de DMA:
  - `0x17665` → `$2A:BB C0` (copia a fonte antes do bloco de 24 KB);
  - `0x177C9` → `$2A:BC 00` (copia o tilemap antes do upload de `$6800`).
- A cópia do tilemap cobre as linhas 7-20 (0x380 bytes) para apagar
  também o rodapé japonês original.
- Validado no recomp nativo: PT-BR e EN exibem as 7 linhas traduzidas
  no frame 1750; o BPS continua aplicando contra a ROM japonesa.
- A fonte tem 32 tiles ASCII maiúsculos; acentos PT-BR ficam para a
  página 8x8 acentuada (`GLORIA`/`ESCURIDAO` por enquanto).
- A tela de status continua pendente (painel pré-renderizado).

## Investigação dos rótulos de atributos

- Resolvido: os rótulos da criação vêm do display-list em `$01:B383`,
  não dos pools de texto `$06/$10/$11`.
- O bloco 5x5 em BG4 `$7C00` que havíamos associado aos labels é o
  menu/valores da direita: em `$FAB0` o trace mostra os códigos ASCII de
  `ESTADO`. O BG2 é o teclado de nomes.
- O banco `$0F` em `$8AE7+` contém nomes de itens (`体力の香`,
  `知力の香`, ...), não os labels da tela.
- A tabela de strings do banco `$06` em `$B22B+` contém os mesmos
  rótulos com sufixo `69 4E 41`; ainda não foi traduzida e falta
  confirmar se é usada pela tela de status.

## Tela de status

- O detalhe do personagem (`ESTADO` → `A`) desenha os rótulos a partir
  do asset comprimido `$07:E998`, descomprimido para `$7F:0000`.
- Os rótulos ficam em `$7F:2686` (linhas 22-26, colunas 3-7); a página
  de fonte em `$7F:0100` (tiles `0x05-0x11`).
- `tools/patch_status.py` substitui o `JSL $01D61B` do loader em
  `0x19720` por um wrapper que:
  1. chama o decompressor original;
  2. grava 13 glifos latinos em `$7F:01A0` (4bpp, layout correto);
  3. grava as 5 linhas de rótulos em `$7F:2686`.
- EN: `VIT / INT / STR / AGI / LUK`; PT: `VIT / INT / FOR / AGI / SOR`.
- Validado no recomp nativo para as duas builds.

## Hashes de referência

- EN `full_names.sfc`:
  - `d74f61278ada237a61fe8b37e7c9d0e450f8873d7a4ca667c515f9785e961894`
- EN `full_names.bps`:
  - 26.752 bytes
  - `0dd8c866067f61c0312114b9b2be31752d00f702bdb8b01c82bacadee36aff14`
- PT `pt_full.sfc`:
  - `0ac724dce3d93ee2453f7641c2933814d5fded3d1c7291d15147205521d6bae5`
- PT `pt_full.bps`:
  - 26.760 bytes
  - `ff27862459405631adba1fd8673aee67ac4ba9874d669127a15cfc4aa5740218`
- `menu_pt.bps`:
  - 2.517 bytes
  - `f16258388b94daddb944ce6acdda85c410cde3acfd345d306b290a3eba63714b`

## Commits desta fase

| Commit | Mudança |
|---|---|
| `c38666e` | corrige a continuação do interpretador de texto |
| `23377a0` | codec de batalha no desenhista 8x8 |
| `0616972` | encurta linhas PT de batalha |
| `0de0dc3` | script PT e pipeline `full-pt` |
| `14c1dc9` | raças PT |
| `1ad8863` | prompts de nome/atributos |
| `648595e` | labels do menu principal/batalha |
| `7e69c64` | labels do submenu COMP |
| `9785c8a` | abertura do banco `$05` |
| `439c863` | menu de configuração |
| `a632785` | revisão da abertura |
| `8cce0a9` | documento de status/cobertura |
| `b377b19` | rótulos de atributos da criação (EN/PT) |
| `c818ee4` | repack e tradução parcial dos nomes T3 |
| `e1a6905` | página hiragana e nomes T3 completos |
| `9863ed3` | descrição MP da loja (`MP TEMP +`) |
| `da9fa18` | pool de descrições `$11:B4DC` (175 segmentos) |
| `documento atual` | lenda inicial em 8x8 (PT/EN, hook de DMA) |
| `documento atual` | changelog EN/PT para revisão |

## Como revisar

1. Comparar os JSONs de tradução com os relatórios:
   - `decomp/build/rom/menu_pt_report.json`;
   - `decomp/build/rom/script_pt_ui_report.json`;
   - `decomp/build/rom/startup_pt_report.json`;
   - `decomp/build/rom/full_pt_report.json`.
2. Aplicar o BPS contra a ROM japonesa e comparar com `pt_full.sfc`:
   ```bash
   python3 decomp/tools/bps.py apply /caminho/kyuuyaku.sfc \
     decomp/build/rom/full_pt.bps /tmp/pt_check.sfc
   cmp decomp/build/rom/full_pt.sfc /tmp/pt_check.sfc
   ```
3. Revisar os trechos curtos e terminologia:
   - `MAGIA` (não `MAGIC`), `ESTADO` (não `STATUS`);
   - `DEMO` para demônio em batalha, `NOME` para name;
   - sem acentos por causa da fonte 8x8 atual;
   - comandos de batalha em maiúsculas e curtos.
4. Validar no recomp as telas indicadas em `translation-status.md`.

## Pendências para a próxima revisão

- Tela de status: painel pré-renderizado, exige pipeline de edição
  gráfica. A lenda inicial já foi resolvida.
- Nomes de itens/equipamentos T3: 298/299 traduzidos; resta apenas o
  placeholder vazio (índice 0).
- Pool de descrições: 175/199 segmentos traduzidos; restam apenas
  vazios/placeholders.
- Prompt da segunda loja: cache do save state; sem pendência de
  tradução.
- Nomes próprios dos demônios em EN/romaji.
- Página 8x8 com minúsculas/acentos.
- Validação cena a cena do script/raças.
- MT2.
