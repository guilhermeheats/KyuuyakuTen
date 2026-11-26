# Traduções (source-only)

Este diretório guarda **apenas dados de tradução originais**: offsets,
tamanhos de slot, texto em inglês/PT-BR e a codificação usada. Nenhuma ROM,
texto japonês extraído ou asset do jogo é commitado aqui.

## Formato

`menu_en.json` é uma lista de entradas:

```json
{
  "offset": "08A187",
  "length": 26,
  "text": "Which item?",
  "encoding": "fullwidth"
}
```

| Campo | Uso |
|---|---|
| `offset` | offset do arquivo na ROM japonesa, em hex |
| `length` | tamanho do slot em bytes (o texto é preenchido até esse tamanho) |
| `text` | tradução original |
| `encoding` | `fullwidth` para diálogo/script; `font` para nomes/menus 8x8 |

### `fullwidth`

O renderizador do script lê 2 bytes por caractere (Shift-JIS). ASCII puro
vira kanji; por isso o texto EN é convertido para o bloco Latin
full-width (`Ａ`-`Ｚ`, `ａ`-`ｚ`, dígitos, pontuação) e preenchido com
`U+3000`. O orçamento é `length / 2` caracteres.

### `font`

Nomes de itens/demônios e labels do submenu COMP usam códigos de fonte de
1 byte (`font_code = ASCII - 0x1F`, maiúsculas), preenchidos com `0x01`.
O orçamento é `length` caracteres.

A página 8x8 em VRAM `0x6000` tem glifos próprios: letras e dígitos seguem
`ASCII - 0x1F`, mas a pontuação não é toda igual ao ASCII. O código `0x1B`
(que seria `:`) renderiza um glifo parecido com "10"; por isso o label de
equipamento usa `EQ` + espaços em vez de `EQ:`. Valide qualquer pontuação
nova ao vivo antes de commitar.

### Patches crus (`raw_en.json`)

Algumas traduções precisam mexer em ponteiros ou terminadores NUL, não só
em texto. `raw_en.json` é uma lista separada:

```json
[
  {
    "offset": "088ECF",
    "bytes": "FB8F",
    "note": "shop menu option 2: $8FF9 -> $8FFB"
  }
]
```

`bytes` é hexadecimal e pode ter espaços. O `replace_text.py` aplica os
patches crus depois do texto, valida limites e recusa sobreposição com as
entradas de texto. Use só quando o layout do texto exigir: por exemplo, ao
remanejar strings NUL-terminated da loja e atualizar a tabela de ponteiros
em `$11:8ECB`.

## Build

Com a ROM japonesa configurada (`rom.cfg` ou `SNESRECOMP_ROM`):

```bash
make menu-en    # UI, menus e lojas
make script-en  # script principal (banco $10)
```

Saídas em `decomp/build/rom/` (ignoradas pelo git):

- `menu_en.sfc` / `menu_en.bps` / `menu_en_report.json`;
- `script_en.sfc` / `script_en.bps` / `script_en_report.json`.

## Escopo atual

`menu_en.json` tem 93 entradas (82 fullwidth + 11 font) e cobre o pool de
mensagens de sistema `$11` (63 ponteiros, 55 mensagens limpas), o submenu
COMP, as lojas JUNKS e ARMORS e os prompts de escada:

- prompts de save/load, arquivo, confirmação e cancelamento;
- prompts de magia, item, alvo, retorno/chamada/remoção de demônio;
- mensagens de erro e de estado (MP, Macca, COMP, itens, programas);
- opções do submenu COMP (`USE ITEM`, `STORE`, `DROP`, `EQ`);
- nomes de cinco itens visíveis (`JEWEL`, `PARA`, `PETRA`, `MUSCLE`,
  `MANA`);
- saudação, pergunta e opções da loja (`Welcome`, `WHAT`, `BUY`, `SELL`,
  `STATUS`, `EXIT`) e a despedida (`Later`);
- lista de compra (`CURE`, `PARA`, `PETRA`, `MUSCLE`) com descrições
  (`Cure`, `Cure par`, `Cure`, `Temp HP up`);
- confirmação compartilhada (`Okay`), rótulo de venda (`Sell`) e erros
  (`No cash`, `No items`);
- prompts de escada (`Upstairs?`, `Go down?`);
- saudação e prompts da loja ARMORS (`Armor, gear`, `Fair armor shop`,
  `Need help`, `May I?`);
- nomes de armadura do banco `$0F` (`CHAIN`, `BREAST`, `IRON`,
  `HELMET`); no save 11 a lista ainda mostra o japonês porque os nomes
  estão em cache na WRAM, não por falha do patch;
- três falas de história do resgate da fada (`Thank you!`, `Take this`,
  `Take Tower Key`), ainda sem validação ao vivo.

As mensagens com nomes dinâmicos preservam os controles `01 04` (demônio),
`01 05` (item), `01 0D` (magia) e `0F` (quebra de linha); só o segmento de
texto é substituído. Mensagens de batalha que concatenam nome + verbo
(`$A433`, `$A4E3`, `$A558`) são tratadas pela passada de batalha
(`battle_en.json`), que repacka o pool e preserva os controles.

O diálogo de história continua bloqueado no save 8: o texto está em cache
na WRAM e o flag do evento não foi encontrado.

## Script principal (`script_en.json`)

`script_en.json` tem 90 entradas e usa o mesmo formato, mas endereça o
script do banco `$10`, cópias no banco `$11` e mensagens de batalha/evento
no banco `$13`. Ele cobre a cena inicial (entrada no abrigo, sonho,
sequência da Astaroth), o restaurante, a narração de Pazuzu
(`$10:$9C82-$A209`), o prompt de baú e as primeiras mensagens de batalha:

- `Box!` / `Open?` — validado ao vivo em um jogo novo, no baú do 8F.
- ` came` — validado ao vivo em um encontro aleatório no 7F
  (`外道ピンクルーパー  came`).
- `What?` — prompt de batalha validado ao vivo.
- ` acts?` — validado ao vivo com o nome dinâmico
  (`ナカジマ  acts?`, `ユミコ  acts?`).
- `Ambush!`, `Looked around`, `Nothing` — eventos de encontro fixo do 7F
  (traduzidos; validação ao vivo pendente).

Os nomes de demônios agora vêm das tabelas T1/T2 em inglês (patch de
nomes); os nomes dos personagens (`ナカジマ`/`ユミコ`) ainda vêm do save.
As linhas de ataque/dano são tratadas pelo passe de batalha
(`battle_en.json`), não por este arquivo.

A narração inicial em tela preta (`古き言い伝えに曰く…`) não está em
Shift-JIS: é um tilemap pré-renderizado (BG1 em VRAM `0x7000`, tiles
`0x147F+`), que exigirá edição gráfica em vez deste pipeline de texto.

A história de abertura de Nakajima/Lucifer/Izanami está no banco `$05`
(`$D917-$DCE5`), não no `$10`. O extrator acha 28 runs, mas alguns começam
no meio de palavras porque há controles que inserem kanji inline (ex.:
`0x89 94 FC` insere 美 antes de `しい天使`). Esse bloco ainda não foi
traduzido; primeiro é preciso interpretar os controles.

O alvo `make script-en` gera `script_en.sfc` e `script_en.bps` separados do
patch de UI. `make battle-en` aplica o passe de batalha em cima; `make
races-en` adiciona os prefixos de raça; `make full-en` combina script,
batalha, raças e nomes e gera `full_en.bps` contra a ROM japonesa. As
validações usaram um save state criado **depois** do patch, com o jogo
começado do zero, para evitar o cache de texto da WRAM.

## Nomes T1/T2 (`names_en.json`)

`names_en.json` cobre as **396** entradas das tabelas T1 (253 demônios) e
T2 (143 demônios). Os nomes em romaji foram conferidos contra a fan
translation EN local, que é referência de grafia, não texto a copiar. Como
o copy de nome do jogo copia no máximo 8 caracteres, nomes longos usam
abreviações (`BEELZEBU`, `MEGAPLAN`, `9TAILFOX` etc.).

`make names-en` gera `names_en.sfc`, `names_en.bps` (4242 bytes) e
`names_en_report.json`. O patch:

- grava as tabelas de ponteiros T1/T2 em `$2E:B820`/`$2E:BA1A`;
- empacota os nomes NUL-terminated em `$2E:D1A0`;
- redireciona as três leituras longas do copy de nome de `$11` para `$2E`.

O espaço usado era zero no ROM original e foi verificado pelo tool. O BPS
faz round-trip contra a ROM japonesa.

`make names-inplace` gera uma variante que reescreve as strings originais
em `$11` (BPS de 2769 bytes), compatível com o recomp sem patch de código,
mas **335 dos 396 nomes ficam truncados** pelo tamanho do slot original.

**Caminho de batalha:** o write em `$0022` vem de `bank_02_C87B`
(`$02:C8D9`) — código AOT nativo. O patch 65816 do BPS funciona em
emulador, mas o recomp não executa essas instruções; ele lê a tabela
original em `$11`. Para o recomp, `tools/regen.sh` chama
`tools/patch-name-tables.py`, que redireciona o C gerado de
`$11:CDFD/$11:D5A8/$11:0000` para `$2E:B820/$2E:BA1A/$2E:0000`.
Depois de regerar e rebuildar, o teste no 7F gravou `ZOMBIE` em `$0022`
— o nome completo em inglês. O prefixo de raça é tratado pelo passe
`races_en.json`.

## Batalha (`battle_en.json`)

A tabela de mensagens de batalha fica em `$11:$A5A4` (144 ponteiros) e o
pool em `$11:$A6C6-$B13D`. Cada mensagem mistura Shift-JIS com controles
`01 xx` e bytes de 1 byte. O `battle_en.json` usa:

```json
{"index": 11, "runs": ["'s attack"], "jp": "の攻撃", "en": "'s attack"}
```

`runs` substitui, em ordem, só os trechos de texto; os controles são
copiados byte a byte. O `tools/patch_battle.py` repacka o pool, deduplica
blobs idênticos e atualiza a tabela. O BPS é gerado contra a ROM japonesa.

Cobertura atual: 10-22 e 40-50/94-106 (ataque, dano, defesa, crítico e
prompt de confirmação). O pool original tem 2679 bytes e a tradução usa
2674, então novas mensagens precisam de relocação/expansão.

Validação ao vivo no recomp: `Foe atk`, `dodged!`, `No damage!`,
`Is this okay?`, `What?`, `acts?`, `ナカジマ's atk`,
`ナカジマ takes 3 dmg`, `O GREENSLM came` e `B BASMU came`.

## Nomes completos na batalha (`full_names.sfc`)

A linha de batalha original tem dois caracteres de raça e até oito de
nome. O alvo `make full-names` instala um caminho **só para a batalha** que
mostra a raça completa e o nome completo na mesma linha:

```text
Foul Green Slime
```

A raça é um prefixo compacto de **duas letras maiúsculas** em 8x8
(`FO` para Foul, `TY` para Tyrant, ...), e o nome completo em 16x16 usa a
fonte de diálogo, que já tem minúsculas. Uma tabela em `$2E:DD08` converte
os códigos 8x8 do nome para Shift-JIS full-width antes de chamar o
renderizador 16x16. Os menus e o status continuam usando os nomes de oito
caracteres em maiúsculas. Validado ao vivo no recomp: `FO Pink Worm`.

O patch instala:

- tabelas de ponteiros de nome completo em `$2E:BB38` (T1) e `$2E:BD32`
  (T2);
- strings de nome completo nos espaços livres de `$2F`;
- tabela e prefixos de raça (8x8, 2 letras) em `$2E:BE50`/`$2E:DF08`;
- tabela de conversão 8x8 -> Shift-JIS full-width em `$2E:DD08`;
- rotinas 65816 em `$2E:BE90` (raça) e `$2E:BF00` (nome), montadas de
  `tools/full-race.s`/`tools/full-name.s`;
- o buffer direto `$57` e o loop de exibição `$02:BADE` redirecionado;
- a flag `$7E:1FF0`, que faz o copy de nome usar a tabela completa apenas
  depois do controle de raça `01 0C`.

O BPS `full_names.bps` é diffado contra a ROM japonesa e inclui todos os
passes anteriores. Como as rotinas novas são código 65816, o recomp deve
ser gerado a partir de `full_names.sfc`:

```sh
make -C decomp full-names
tools/regen.sh --rom decomp/build/rom/full_names.sfc --no-verify
cmake --build build-debug
```

O `--no-verify` é necessário porque o ROM de entrada já contém o patch de
código; a identidade japonesa continua sendo verificada pelo baseline.

## Raças (`races_en.json`)

O controle `01 0C` chama `$02:BCFA`, que lê dois caracteres full-width da
tabela `$02:BC8E` (26 entradas de 4 bytes). O slot é fixo em dois
caracteres, então a tradução usa **uma letra + espaço**:

| Código | Raça | Código | Raça |
|---|---|---|---|
| `T ` | Tyrant (魔王) | `N ` | Night (夜魔) |
| `D ` | Deity (邪神) | `S ` | Spirit (幽鬼) |
| `B ` | Beast (怪獣) | `W ` | Wilder (妖獣) |
| `F ` | Femme (鬼女) | `J ` | Jaki (邪鬼) |
| `M ` | Machine (機械) | `H ` | Haunt (悪霊) |
| `A ` | Madman (狂人) | `O ` | Foul (外道) |
| `Y ` | Fairy (妖精) | `E ` | Earth (地霊) |
| `Q ` | Yoma (妖鬼) | `V ` | Vile (魔獣) |
| `U ` | Yoma (妖魔) | `L ` | Element (精霊) |
| `C ` | Holy (聖獣) | `P ` | Phantom (幻魔) |
| `I ` | Divine (天使) | `K ` | Kishin (鬼神) |
| `R ` | Avatar (神獣) | `G ` | God (魔神) |

`tools/patch_races.py` grava a tabela. É data-only e o recomp lê a ROM,
então não precisa de patch no C gerado. `make races-en` gera o BPS contra
a ROM japonesa. Validado ao vivo: `O GREENSLM came` (Foul + Green Slime)
e `B BASMU came` (Beast + Basmu).

A limitação de uma letra é consequência do slot de 2 caracteres; se o
prefixo precisar de mais espaço, será necessário patchar `$02:BCFA` para
ler uma tabela maior (e refazer o redirect no AOT).

## Créditos e licença

- O texto em inglês é original deste projeto.
- Termos e nomes seguem o estilo da fan translation EN existente, usada
  apenas como referência local. Os autores da fan translation devem ser
  creditados no README do patch antes de qualquer release público.
- Código, ferramentas e patch: BSD-3-Clause (ver `LICENSE` na raiz).
- Nenhuma ROM traduzida é distribuída; só o BPS.
