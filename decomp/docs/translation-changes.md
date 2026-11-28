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
| `translations/items_en.json` | EN | 146 | font 8x8 | T3 itens/equipamentos |
| `translations/items_pt.json` | PT-BR | 146 | font 8x8 | T3 itens/equipamentos |

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
- 146 entradas foram traduzidas nesta primeira passada: armas,
  armaduras, capacetes, luvas e botas com katakana decodificado.
- EN e PT-BR usam códigos de fonte 8x8 (`ASCII - $1F`); nomes longos
  foram abreviados para caber no menu. Exemplos:
  `WALTHER`, `ESCOPETA`, `CANIVETE`, `CIMITARRA`, `NUNCHAKU`,
  `MUSCLE`, `SOMA`, `AMETHYST`, `MACCA`.
- As 153 entradas restantes são itens especiais com kanji ainda não
  mapeado; permanecem em japonês.
- Validação: pool e ponteiros relidos do ROM final; os nomes PT foram
  renderizados com os tiles reais da fonte `$0F:AF6B`; BPS aplicado
  contra a ROM japonesa e comparado byte a byte.

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
  um patch dessa tabela não alterou a tela. O painel parece
  pré-renderizado/cacheado e exige edição do tilemap/tiles.
- A lenda inicial aparece por volta do frame 900, no tilemap BG1
  `$7200` (linhas 4-15), com glifos 16x16 pré-renderizados; também exige
  edição gráfica.
- Nenhum patch cego foi aplicado nessas duas telas.

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

## Hashes de referência

- EN `full_names.sfc`:
  - `e4eb56ac691fe3e0d86ffef4019fe0c1370f96687c2123204876f5a0adc9f0e8`
- EN `full_names.bps`:
  - 20.914 bytes
  - `11c2a8e0486870d953d1187d8edc4f8db23dc2dfc7b9f3775cef72fd9c457c1d`
- PT `pt_full.sfc`:
  - `3cc30f7274e2c8fdf9b25d94d9b657a409a7a9522975dd069a4251e55b92a588`
- PT `pt_full.bps`:
  - 21.028 bytes
  - `3b9f820bb8ae26ce1cbe922ea409bd547856a3264468e7a33784a0afa7ab517c`
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

- Tela de status e lenda inicial: painéis pré-renderizados, exigem
  pipeline de edição gráfica.
- Nomes de itens/equipamentos T3: 146/299 traduzidos; restam 153 itens
  especiais com kanji não mapeado.
- Nomes próprios dos demônios em EN/romaji.
- Página 8x8 com minúsculas/acentos.
- Validação cena a cena do script/raças.
- MT2.
