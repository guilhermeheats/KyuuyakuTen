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

- ROM `82f0003ea0a2e6653b93c44dccd7cde3e3e75b032fb36305e910be0ab251bbce`
- BPS `ef6af569507a5a1b56146a9054bc7814aa4c3d314782ad6cb0ca2fb39e6a34e7`
  (25.179 bytes)
- `menu_pt.bps` 2.517 bytes

Hashes do build EN atual:

- ROM `dc3b9bd4941b6e7560cdba787b9fea672a28f1f42f46315cb734ca976ee442f9`
- BPS `02b8b5221ba9e348d0a2a4c8e3955a2e081ccd9bce18eb34683601f6f4f27449`
  (25.149 bytes)

O build PT usa:
- UI/menu PT-BR (`menu_pt.json`, 146 entradas);
- script PT-BR (`script_pt.json`, 90 entradas);
- criação de personagem e abertura do banco `$05`
  (`startup_pt.json`, 42 entradas + `startup_raw.json`);
- rótulos de atributos da criação em 8x8 (`stat_labels_pt.json`,
  5 patches de tilemap);
- nomes de itens/equipamentos T3 (`items_pt.json`, 298 entradas;
  repack completo do pool `$06:$ED54+` e da tabela de 299 ponteiros);
- descrições de itens (`descriptions_pt.json`, 175 segmentos do pool
  `$11:B4DC`; 199 segmentos no total, os restantes são vazios/`?????`);
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
- Itens T3: os 298 nomes não vazios estão em PT-BR; ponteiros e pool
  relidos do ROM final e conferidos. A entrada 0 é o placeholder vazio.
- Loja JUNKS: a lista de compra mostrou `POISON / PARALYZE / PETRIFY /
  MUSCLE / ESSENCIA` em PT-BR; a compra de POISON descontou 400 MAG
  (1259 -> 859) e o fluxo YES/NO funcionou.
- Descrições de itens: as linhas visíveis da loja estão em PT-BR:
  POISON `CURA V`, PARALYZE `CURA PAR`, PETRIFY `CURA ST`,
  MUSCLE `HP TEMP +`, ESSENCIA `MP TEMP +`.
- O pool `$11:B4DC` tem 199 segmentos; 175 foram traduzidos,
  incluindo as linhas de ataque/defesa das armas e armaduras.
  Os 24 restantes são vazios ou placeholders `?????`.
- O prompt japonês da segunda loja (save 8) é **cache do save state**:
  o ROM PT já tem `QUE?` em `$1F739` e o `DEPOIS` em PT aparece ao sair
  da loja. Ao reentrar, a tabela corrigida é relida.
- Abertura do banco `$05`: linhas em PT-BR validadas no filme.
- Batalha: `COMANDO?`, `FAZ O QUE?`, `TUDO BEM?`, `SOFRE N DANO`,
  `PERDE N`, `SEM DANO!`, `ESQUIVOU!`.
- COMP/história: texto de 2 bytes renderizando normalmente após a
  correção da continuação em `$02:B037`.
- BPS aplicado contra a ROM japonesa e comparado byte a byte.

## Ainda pendente

1. Nomes próprios dos demônios: mantidos em EN/romaji.
2. Página 8x8 com minúsculas/acentos para PT-BR completo.
3. Tela de status (botão `X`): o painel fica em BG2 `$6C00` e a fonte
   8x8 em `$6000`; os rótulos (`たいりょく`, `ちりょく`, `つよさ`,
   `はやさ`, `うん`) não são lidos da tabela do banco `$06` em `$B22B`
   (um patch nessa tabela não alterou a tela). O painel parece
   pré-renderizado/cacheado; traduzir exige editar o tilemap/tiles do
   painel, não uma string.
4. Lenda inicial em tela preta (`古き言い伝えに曰く…`): o texto fica
   em BG2 `$7A00`, linhas 6-14, com a página de fonte `$B000`
   (16x16). O BG1 `$7200` é a moldura. Os buffers vivos são:
   tilemap `$7E:3588` e página de fonte `$7F:50A0`, alimentada a partir
   de `$7E:F0A0` por `$01D581`/`$01D5B3`; o tilemap é atualizado por
   `$018E92`. O trace de `$01D5B3` mostra a origem em `$37:8060+`
   (banco `$37`, stream comprimido), com destinos em `$7F:0093+`.
   Não há string Shift-JIS simples: é um asset gráfico comprimido.
   Falta decodificar/recomprimir o stream ou usar o pipeline de
   tilemap/fonte.
5. Validação cena a cena do script/raças PT no recomp.
6. MT2 ainda não iniciado.

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
