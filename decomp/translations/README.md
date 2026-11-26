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
make menu-en
```

Saídas em `decomp/build/rom/` (ignoradas pelo git):

- `menu_en.sfc` — ROM traduzida para teste local;
- `menu_en.bps` — patch contra a ROM japonesa;
- `menu_en_report.json` — offsets, bytes antigos/novos e encoding.

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

## Créditos e licença

- O texto em inglês é original deste projeto.
- Termos e nomes seguem o estilo da fan translation EN existente, usada
  apenas como referência local. Os autores da fan translation devem ser
  creditados no README do patch antes de qualquer release público.
- Código, ferramentas e patch: BSD-3-Clause (ver `LICENSE` na raiz).
- Nenhuma ROM traduzida é distribuída; só o BPS.
