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
(`$A433`, `$A4E3`, `$A558`) ficam para a passada de batalha, porque o slot
não comporta o espaço separador.

O diálogo de história continua bloqueado no save 8: o texto está em cache
na WRAM e o flag do evento não foi encontrado.

## Script principal (`script_en.json`)

`script_en.json` tem 41 entradas e usa o mesmo formato, mas endereça o
script do banco `$10`, cópias no banco `$11` e mensagens de batalha/evento
no banco `$13`. Ele cobre a cena inicial (entrada no abrigo, sonho,
sequência da Astaroth), o restaurante, o prompt de baú e as primeiras
mensagens de batalha:

- `Box!` / `Open?` — validado ao vivo em um jogo novo, no baú do 8F.
- ` came` — validado ao vivo em um encontro aleatório no 7F
  (`外道ピンクルーパー  came`).
- `What?` — prompt de batalha validado ao vivo.
- ` acts?` — validado ao vivo com o nome dinâmico
  (`ナカジマ  acts?`, `ユミコ  acts?`).
- `Ambush!`, `Looked around`, `Nothing` — eventos de encontro fixo do 7F
  (traduzidos; validação ao vivo pendente).

Os nomes de demônios e personagens continuam em japonês porque vêm das
tabelas T1/T2, ainda não traduzidas. Linhas de ataque/dano
(`ナカジマの攻撃`, `ナカジマは３ダメージ`) também continuam em japonês.

O alvo `make script-en` gera `script_en.sfc` e `script_en.bps` separados do
patch de UI. As validações usaram um save state criado **depois** do patch,
com o jogo começado do zero, para evitar o cache de texto da WRAM.

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

**Limitação de batalha:** um boot novo ainda mostrou o nome do inimigo em
japonês (`マッドスラッグ`). O caminho que exibe o nome no encontro usa
outra rotina (a região `$014898`/`$0C40`), não o copy T1/T2 que foi
redirecionado para `$2E`. A tabela/patch T1/T2 está correta para os usos
que passam pelo copy; falta mapear/patchear o caminho de batalha.

## Créditos e licença

- O texto em inglês é original deste projeto.
- Termos e nomes seguem o estilo da fan translation EN existente, usada
  apenas como referência local. Os autores da fan translation devem ser
  creditados no README do patch antes de qualquer release público.
- Código, ferramentas e patch: BSD-3-Clause (ver `LICENSE` na raiz).
- Nenhuma ROM traduzida é distribuída; só o BPS.
