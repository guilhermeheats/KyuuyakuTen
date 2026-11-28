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

### Itens de efeito estatístico (banco `$0F`)

- `MUSCLE` (マッスルドリンコ), `MANA` (魔力の素), `SOM` (ソーマ),
  `VIT` (体力の香), `INT` (知力の香), `FOR` (強さの香),
  `AGI` (速さの香), `SOR` (運の香), `AMET` (アメジスト).
- Aplicado pelo novo alvo `bank0f-pt`, antes do script no `full-pt`.

## Investigação dos rótulos de atributos

- Os labels da criação (`ちりょく`, `うん`, `たいりょく`, `ちから`,
  `はやさ`) não estão nos pools de texto `$06`, `$10` ou `$11`.
- O banco `$0F` em `$8AE7+` contém nomes de itens (`体力の香`,
  `知力の香`, `強さの香`, `速さの香`, `運の香`), que são itens, não os
  labels da tela.
- O traço de VRAM do momento da criação mostrou o painel/valores sendo
  escritos por `Coverage_00_84E8` em BG4 (`$F8B4-$FFFF`); os labels
  parecem vir de um tilemap BG2 que não foi capturado como escrita de
  CPU, provavelmente por DMA. `get_dma_state` no estado da criação mostra
  os canais 5/7 com fontes `$00:D8E1`/`$00:0A20` e transfers de ~64 KB
  (prováveis cópias em bloco/de boot). O próximo passo é rastrear a
  origem exata do tilemap ou a rotina do renderizador da criação.

## Hashes de referência

- EN `full_names.sfc`:
  - `749e2384ef44fb3eaa247a45b9505ac4e100d4aef0113096cb837a68a40736ea`
- PT `pt_full.sfc`:
  - `2366b42ec705fd8ffac5538b831a03373c13a0110ea58205abba268e5c3deba9`
- PT `pt_full.bps`:
  - 17.919 bytes
  - `c4708a51fbd8cfe37a1e91d59964400bbc0a62fee6550aa31df0a6ef750d7cfe`
- `menu_pt.bps`:
  - 2.488 bytes

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

- Rótulos de atributos na criação de personagem.
- Lenda inicial em BG1 pré-renderizado.
- Nomes de itens/equipamentos T3 (299 entradas).
- Nomes próprios dos demônios em EN/romaji.
- Página 8x8 com minúsculas/acentos.
- Validação cena a cena do script/raças.
- MT2.
