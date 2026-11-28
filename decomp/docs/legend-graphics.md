# Lenda inicial — mapa gráfico e plano de patch

Documento de revisão para a tela da lenda (texto branco em fundo preto,
exibido no início do MT1). O texto é pré-renderizado: não existe uma
string Shift-JIS simples. Este documento registra os endereços vivos, o
pipeline de upload e o caminho de patch escolhido.

## Texto

Original (7 linhas):

```
古き言い伝えに曰く
かつて
翼持つ者どもの反乱あり
けれど彼ら敗れたり
彼ら栄光を失い
白き翼もがかれ
暗き地の底へと堕されたり
```

EN:

```
An ancient legend tells
of a time when
the winged ones rebelled
but they were defeated
they lost their glory
their white wings were torn
and they fell into darkness
```

PT-BR:

```
Uma antiga lenda conta
de um tempo em que
os alados se rebelaram
mas foram derrotados
perderam sua glória
suas asas brancas foram
arrancadas na escuridão
```

## Camada e buffers

| Item | Endereço | Tamanho | Observação |
|---|---|---|---|
| Tilemap BG3 | VRAM `$6800` | 2 KB | linhas 0-15, 32 colunas |
| Buffer do tilemap | `$7F:0010` | 2 KB | DMA no frame 724 |
| Fonte 16x16 (BG3) | VRAM `$5000` | 4 KB | 256 tiles 8x8, 2bpp |
| Buffer da fonte | `$7F:4000` | 4 KB | parte do bloco de 24 KB |
| Bloco de 24 KB | `$7F:0000-$5FFF` | 24 KB | DMA no frame 701 para VRAM `$3000` |
| Moldura BG1 | VRAM `$7200` | — | fora do escopo da lenda |

A camada foi confirmada com `SNESRECOMP_LAYER_MASK=4` (BG3). O render
direto de VRAM `$6800` + `$5000` (2bpp) reproduz o texto completo.

## Pipeline de assets

O bloco de 24 KB é decodificado de assets comprimidos do banco `$37`.
A tabela de ponteiros fica em `$37:8000`:

```
$37:8000: 0E 80 36 BD 92 E8 89 F4 56 FA D5 FC B9 FE ...
```

Blocos iniciais: `$37:8012`, `$37:BD3A`, `$37:E896`, `$37:F48D`,
`$37:FA5A`, `$37:FCD9`, `$37:FEBD`.

O decodificador fica em `$01:D5B3`/`$01:D581`/`$01:D419` e usa um
window de 2 KB em `$7E:F000`. O stream é fatiado em vários frames
(aproximadamente 630-730) e o destino avança de `$7F:0000` até
`$7F:5B74`. O upload para a VRAM acontece depois:

- frame 701: `$7F:0000` → VRAM `$3000`, 0x6000 bytes (inclui a fonte
  em `$7F:4000` → VRAM `$5000`);
- frame 724: `$7F:0010` → VRAM `$6800`, 0x800 bytes (tilemap);
- frame 729/730: `$7E:3000`/`$7E:3800` → VRAM `$7800`/`$7C00`
  (tilemap auxiliar da moldura).

## Patch implementado

`tools/patch_legend.py` substitui o asset comprimido por dados próprios,
sem depender do decoder:

- Tilemap 32x32 em 8x8, linhas 7-20 (`0x380` bytes), em `$2A:B820`
  (file `0x153820`).
- 32 tiles latinos 2bpp (A-Z, espaço e pontuação), em `$2A:F820`
  (file `0x157820`).
- Hook da fonte em `$2A:BBC0`: copia os 32 tiles para `$7F:5E00`
  (tiles `0x1E0-0x1FF`) e dispara o DMA de `0x6000` bytes.
- Hook do tilemap em `$2A:BC00`: copia as 14 linhas para `$7F:01D0` e
  dispara o DMA de `0x800` bytes.

Sites patcheados:

| File offset | Original | Novo |
|---|---|---|
| `0x17665` | `A9 08 8D 0B 42` | `22 C0 BB 2A EA` |
| `0x177C9` | `A9 08 8D 0B 42` | `22 00 BC 2A EA` |

A cópia do tilemap cobre também a linha 20 para apagar o rodapé japonês
que sobrava com 13 linhas. Validado no recomp nativo em PT-BR e EN no
frame 1750.

A fonte de 32 tiles usa apenas ASCII maiúsculo. Acentos PT-BR (GLÓRIA,
ESCURIDÃO) ficam para a página 8x8 acentuada, que é uma pendência
separada; por enquanto o texto usa `GLORIA`/`ESCURIDAO`.

## Espaço livre

| File offset | Banco:endereço | Uso |
|---|---|---|
| `0x153820` | `$2A:B820` | tilemap (0x380) |
| `0x153BC0` | `$2A:BBC0` | hook da fonte |
| `0x153C00` | `$2A:BC00` | hook do tilemap |
| `0x157820` | `$2A:F820` | tiles latinos (0x200) |

Os trechos estão zerados nos ROMs finais PT e EN; o banco `$2A` não é
usado pelos patches de texto existentes.
