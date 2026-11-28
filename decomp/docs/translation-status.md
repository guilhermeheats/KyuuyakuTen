# Translation status — MT1

Estado dos patches de tradução e do build jogável. Este documento é um
resumo de revisão; os detalhes de implementação ficam em
[`text-plan.md`](text-plan.md) e [`translations/README.md`](../translations/README.md).

## Builds

| Alvo | ROM | BPS |
|---|---|---|
| EN | `build-debug/full_names.sfc` | `full_names.bps` |
| PT-BR | `build-debug/pt_full.sfc` | `build-debug/pt_full.bps` |

Hashes do build PT atual:

- ROM `4941873185f574c9485e186d650f501b2c349009d8db342ba3a2cfe3b2e6a4c1`
- BPS `8e27de39192d02dbe9a2c600e14ce2ad8adbc9d20549910e2d6b7dadbca6b14d`
  (17.948 bytes)
- `menu_pt.bps` 2.517 bytes

Hashes do build EN atual:

- ROM `a18fd1c0ea0fa1e732dd56ba94d7fed9f324b5e29797b81e3cee54fd0874112b`
- BPS `d5b7d46446da06f8cd95b8e45557631ab1650f676a06cd1a665df50f826f4eac`
  (17.951 bytes)

O build PT usa:
- UI/menu PT-BR (`menu_pt.json`, 146 entradas);
- script PT-BR (`script_pt.json`, 90 entradas);
- criação de personagem e abertura do banco `$05`
  (`startup_pt.json`, 42 entradas + `startup_raw.json`);
- rótulos de atributos da criação em 8x8 (`stat_labels_pt.json`,
  5 patches de tilemap);
- batalha PT-BR de 1 byte com codec 8x8 (`battle_pt.json`, 129 entradas);
- raças PT-BR (`races_pt.json`, 24 descritores);
- nomes próprios dos demônios em EN (`names_en.json`).

## Validação no recomp

- Menu principal: `COMP / MAGIA / ITEM / ESTADO`.
- Submenu COMP: `CHAMAR / VOLTAR / LIBERAR / TROCAR / MAPA AUTO /
  CONFIG / ANALISAR`.
- Configuração: `BATALHA / MAGIAS / MAPA AUTO / SOM` e valores
  `RAP / LEN / NOR / OFF / ON / AUT / FIX / STER`.
- Criação de personagem: prompts de nome, `Distribua` e rótulos
  `VIT / INT / FOR / AGI / SOR`.
- Abertura do banco `$05`: linhas em PT-BR validadas no filme.
- Batalha: `COMANDO?`, `FAZ O QUE?`, `TUDO BEM?`, `SOFRE N DANO`,
  `PERDE N`, `SEM DANO!`, `ESQUIVOU!`.
- COMP/história: texto de 2 bytes renderizando normalmente após a
  correção da continuação em `$02:B037`.
- BPS aplicado contra a ROM japonesa e comparado byte a byte.

## Ainda pendente

1. Nomes de itens/equipamentos da tabela T3 do banco `$06` (299 entradas):
   a maioria continua em japonês; só os itens de menu mais visíveis foram
   traduzidos. As nove strings de efeito estatístico do banco `$0F`
   (`MUSCLE`, `MANA`, `SOM`, `VIT`, `INT`, `FOR`, `AGI`, `SOR`, `AMET`)
   já estão em PT-BR.
2. Nomes próprios dos demônios: mantidos em EN/romaji.
3. Página 8x8 com minúsculas/acentos para PT-BR completo.
4. Tela de status (botão `X`): o painel fica em BG2 `$6C00` e a fonte
   8x8 em `$6000`; os rótulos (`たいりょく`, `ちりょく`, `つよさ`,
   `はやさ`, `うん`) não são lidos da tabela do banco `$06` em `$B22B`
   (um patch nessa tabela não alterou a tela). O painel parece
   pré-renderizado/cacheado; traduzir exige editar o tilemap/tiles do
   painel, não uma string.
5. Lenda inicial em tela preta (`古き言い伝えに曰く…`): capturada por
   volta do frame 900; fica no tilemap BG1 `$7200`, linhas 4-15, com
   glifos 16x16 pré-renderizados. Também exige edição gráfica.
6. Validação cena a cena do script/raças PT no recomp.
7. MT2 ainda não iniciado.

## Reprodução

```bash
cd decomp
make full-pt
```

Saídas em `decomp/build/rom/` (ignoradas pelo git). O `src/gen` do recomp
deve ser regerado a partir de `full_pt.sfc` quando o codec de batalha ou
outra rotina 65816 mudar:

```bash
cd ..
tools/regen.sh --rom decomp/build/rom/full_pt.sfc --no-verify
cmake --build build-debug -j"$(nproc)"
```

O binário `build-debug/KyuuyakuTen-translated` carrega o gate SHA da ROM
PT final; `build-debug/KyuuyakuTen` é a referência original.
