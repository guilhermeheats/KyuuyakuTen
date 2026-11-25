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

`menu_en.json` cobre o fluxo de item do save 11:

- prompts de usar/descartar item, falta de MP, alvo, etc.;
- opções do submenu COMP (`USE ITEM`, `STORE`, `DROP`, `EQ:`);
- nomes de cinco itens visíveis (`JEWEL`, `PARA`, `PETRA`, `MUSCLE`,
  `MANA`).

Ainda não há diálogo de história traduzido; o save 8 tem o texto em cache
na WRAM e o evento precisa ser reaberto.

## Créditos e licença

- O texto em inglês é original deste projeto.
- Termos e nomes seguem o estilo da fan translation EN existente, usada
  apenas como referência local. Os autores da fan translation devem ser
  creditados no README do patch antes de qualquer release público.
- Código, ferramentas e patch: BSD-3-Clause (ver `LICENSE` na raiz).
- Nenhuma ROM traduzida é distribuída; só o BPS.
