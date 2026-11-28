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

- ROM `0ac724dce3d93ee2453f7641c2933814d5fded3d1c7291d15147205521d6bae5`
- BPS `ff27862459405631adba1fd8673aee67ac4ba9874d669127a15cfc4aa5740218`
  (26.760 bytes)
- `menu_pt.bps` 2.517 bytes

Hashes do build EN atual:

- ROM `d74f61278ada237a61fe8b37e7c9d0e450f8873d7a4ca667c515f9785e961894`
- BPS `0dd8c866067f61c0312114b9b2be31752d00f702bdb8b01c82bacadee36aff14`
  (26.752 bytes)

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
- nomes próprios dos demônios em EN (`names_en.json`);
- lenda inicial em 8x8 (`legend_pt.json`/`legend_en.json`, 7 linhas,
  hook de DMA no banco `$2A`).

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
- Lenda inicial: as 7 linhas em PT-BR e EN foram validadas no recomp
  nativo (frame 1750), com fonte 8x8 e tilemap próprios. O rodapé
  japonês residual foi removido ao estender a cópia até a linha 20.
- Tela de status: os cinco rótulos aparecem traduzidos no detalhe do
  personagem (PT `VIT/INT/FOR/AGI/SOR`, EN `VIT/INT/STR/AGI/LUK`),
  validados no recomp nativo.
- Batalha: `COMANDO?`, `FAZ O QUE?`, `TUDO BEM?`, `SOFRE N DANO`,
  `PERDE N`, `SEM DANO!`, `ESQUIVOU!`.
- COMP/história: texto de 2 bytes renderizando normalmente após a
  correção da continuação em `$02:B037`.
- BPS aplicado contra a ROM japonesa e comparado byte a byte.

## Ainda pendente

1. Nomes próprios dos demônios: mantidos em EN/romaji.
2. Página 8x8 com minúsculas/acentos para PT-BR completo.
3. ~~Tela de status~~ (resolvido): painel BG2 `$6C00`, char base
   `$3000` (4bpp), rótulos nas linhas 22-26. O asset do painel é
   `$07:E998`, descomprimido para `$7F:0000`; os rótulos ficam em
   `$7F:2686` e os glifos em `$7F:01A0`. `patch_status.py` substitui
   o `JSL $01D61B` do loader (`0x19720`) por um wrapper que
   descomprime, grava os 13 glifos latinos e as 5 linhas traduzidas.
   EN `VIT/INT/STR/AGI/LUK`; PT `VIT/INT/FOR/AGI/SOR`. Validado no
   recomp nativo. Detalhes em [`status-graphics.md`](status-graphics.md).
4. ~~Lenda inicial~~ (resolvido): texto completo em 7 linhas, renderizado em BG3 com
   tilemap em `$6800` (buffer `$7F:0010`, 2 KB, DMA no frame 724) e
   fonte 16x16 em `$5000` (buffer `$7F:4000`, 4 KB, parte do bloco de
   24 KB `$7F:0000-$5FFF`, DMA no frame 701 para a VRAM `$3000`).
   O bloco vem de assets comprimidos do banco `$37` (tabela em
   `$37:8000`; blocos em `$37:8012`, `$BD3A`, `$E896`, `$F48D`...).
   Texto original:

   ```
   古き言い伝えに曰く
   かつて
   翼持つ者どもの反乱あり
   けれど彼ら敗れたり
   彼ら栄光を失い
   白き翼もがかれ
   暗き地の底へと堕されたり
   ```

   EN: *An ancient legend tells / of a time when / the winged ones
   rebelled / but they were defeated / they lost their glory / their
   white wings were torn / and they fell into darkness.*
   PT-BR: *Uma antiga lenda conta / de um tempo em que / os alados se
   rebelaram / mas foram derrotados / perderam sua glória / suas asas
   brancas foram / arrancadas na escuridão.*

   A tradução usa tiles 8x8 latinos e um tilemap próprio, gravados no
   espaço livre do banco `$2A` (`0x153820`, tilemap; `0x157820`,
   fonte), com hooks de DMA em `0x153BC0`/`0x153C00`. Validado em PT-BR
   e EN no recomp nativo.
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
