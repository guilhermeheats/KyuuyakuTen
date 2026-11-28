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

- ROM `8a80f89f305173543e3ebafbcfddf5e4c1ac8644fd720dbb5bf8f8eaf10fb394`
- BPS `374641706c40a97e8d8e8fe90fa8f43f80380df52759b3d35f1efc34bb8ee727`
  (21.104 bytes)
- `menu_pt.bps` 2.517 bytes

Hashes do build EN atual:

- ROM `4c7bb4d17c5ea07a2b19a1ee28a55b5060f60139196546d0a09e4390d1b4252a`
- BPS `d1e77aa599e24208f232958b3b576f28b3b2746556ad50aba0b4d6f03293b274`
  (21.070 bytes)

O build PT usa:
- UI/menu PT-BR (`menu_pt.json`, 146 entradas);
- script PT-BR (`script_pt.json`, 90 entradas);
- criação de personagem e abertura do banco `$05`
  (`startup_pt.json`, 42 entradas + `startup_raw.json`);
- rótulos de atributos da criação em 8x8 (`stat_labels_pt.json`,
  5 patches de tilemap);
- nomes de itens/equipamentos T3 (`items_pt.json`, 298 entradas;
  repack completo do pool `$06:$ED54+` e da tabela de 299 ponteiros);
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
- Descrições de itens: a linha inferior da loja continua em japonês
  (`一時的にＭＰを増幅させる`). A tabela é separada do T3: 299
  ponteiros **big-endian** em `$11:B4DC`, strings Shift-JIS com
  separador `01 01`. A ordem não é necessariamente 1:1 com o T3;
  a descrição do MUSCLE fica em `$11:C3DD` e a de HP em `$11:C3F7`.
- Uma segunda loja (save 8) ainda mostrou o prompt em japonês
  (`何の用? / 買う / 売る / ステイタスを見る / 外に出る`); verificar se é
  outra cópia/tabela ou cache.
- Abertura do banco `$05`: linhas em PT-BR validadas no filme.
- Batalha: `COMANDO?`, `FAZ O QUE?`, `TUDO BEM?`, `SOFRE N DANO`,
  `PERDE N`, `SEM DANO!`, `ESQUIVOU!`.
- COMP/história: texto de 2 bytes renderizando normalmente após a
  correção da continuação em `$02:B037`.
- BPS aplicado contra a ROM japonesa e comparado byte a byte.

## Ainda pendente

1. Descrições de itens/equipamentos: tabela `$11:B4DC` (299
   ponteiros) ainda em japonês; traduzir e validar na loja.
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
