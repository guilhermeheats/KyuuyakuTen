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

- ROM `5192df2ce287e4c3b7ddb506be830f4ff2f68188676fbae95e3269ecc4e869c3`
- BPS `f6981d60991ab7a25a27d4260cf3ce32f76bd38970939047570a2d0a94beba99`
- `menu_pt.bps` 2.488 bytes

O build PT usa:
- UI/menu PT-BR (`menu_pt.json`, 146 entradas);
- script PT-BR (`script_pt.json`, 90 entradas);
- criação de personagem e abertura do banco `$05`
  (`startup_pt.json`, 42 entradas + `startup_raw.json`);
- batalha PT-BR de 1 byte com codec 8x8 (`battle_pt.json`, 129 entradas);
- raças PT-BR (`races_pt.json`, 24 descritores);
- nomes próprios dos demônios em EN (`names_en.json`).

## Validação no recomp

- Menu principal: `COMP / MAGIA / ITEM / ESTADO`.
- Submenu COMP: `CHAMAR / VOLTAR / LIBERAR / TROCAR / MAPA AUTO /
  CONFIG / ANALISAR`.
- Configuração: `BATALHA / MAGIAS / MAPA AUTO / SOM` e valores
  `RAP / LEN / NOR / OFF / ON / AUT / FIX / STER`.
- Criação de personagem: prompts de nome e `Distribua`.
- Abertura do banco `$05`: linhas em PT-BR validadas no filme.
- Batalha: `COMANDO?`, `FAZ O QUE?`, `TUDO BEM?`, `SOFRE N DANO`,
  `PERDE N`, `SEM DANO!`, `ESQUIVOU!`.
- COMP/história: texto de 2 bytes renderizando normalmente após a
  correção da continuação em `$02:B037`.
- BPS aplicado contra a ROM japonesa e comparado byte a byte.

## Ainda pendente

1. Rótulos dos atributos na criação de personagem (`ちりょく`, `うん`,
   `たいりょく`, `ちから`, `はやさ`): usam um tilemap/fonte separado.
2. Lenda inicial em tela preta (`古き言い伝えに曰く…`): tilemap BG1
   pré-renderizado, exige edição gráfica.
3. Nomes de itens/equipamentos da tabela T3 do banco `$06` (299 entradas):
   a maioria continua em japonês; só os itens de menu mais visíveis foram
   traduzidos.
4. Nomes próprios dos demônios: mantidos em EN/romaji.
5. Página 8x8 com minúsculas/acentos para PT-BR completo.
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
