# Glossário

O glossário é gerado a partir das tabelas de nomes do banco `$11`:

```bash
make names
```

Saídas (ignoradas pelo git):

- `decomp/build/text/names.json` — tabela completa com códigos, offset e kana;
- `decomp/build/text/names.csv` — template para tradução.

## Formato do CSV

| Coluna | Uso |
|---|---|
| `table` | `t1` = demônios/personagens; `t2` = itens/equipamentos |
| `index` | índice na tabela |
| `file_offset` | offset da string na ROM |
| `jp` | leitura em kana (não é o texto oficial; é a decodificação dos códigos de fonte) |
| `en` | tradução inglesa a preencher |
| `pt_br` | tradução PT-BR a preencher |
| `notes` | observações (termo da fan translation, contexto, etc.) |

## Regras

- O CSV gerado **não** é commitado; só o template vazio ou entradas
  sintéticas de teste podem ir para o repo.
- Nomes próprios seguem o estilo da fan translation EN, mas o texto é
  nosso.
- PT-BR é traduzido do japonês; o inglês é referência.
- Códigos desconhecidos aparecem como `{XX}` e precisam de revisão manual.
  Exemplos atuais: `{69}{46}{4D}` (provável texto ASCII/`iFM`) e
  `{76}{41}{52}`.

## Estado

- T1: 253 entradas (demônios/personagens).
- T2: 143 entradas (itens/equipamentos).
- A página de katakana `0x8C-0xDF`, `0x0E` (ー) e `0x0F` (゛) está
  mapeada; a página ASCII baixa (`0x01` espaço, `0x11-0x1A` dígitos,
  `0x22-0x3B` A-Z) também.
- Falta mapear a página ASCII/kanji usada por alguns nomes (`0x41-0x7F`).
