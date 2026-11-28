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

## Plano de patch

Como o asset é comprimido e o decoder ainda não foi reproduzido com
segurança byte a byte, o caminho escolhido é substituir os **buffers
finais** por dados traduzidos e reenviá-los por DMA, sem depender do
stream original.

1. Extrair o bloco final de `$7F:0000-$5FFF` (fontes e gráficos) do
   estado vivo no frame 900, usando a VRAM `$3000` para a primeira
   página.
2. Construir uma fonte 8x8 latina na página `$5000` (tiles 2bpp) e um
   tilemap novo em `$6800` com as linhas EN/PT.
3. Gravar tilemap (0x800 bytes) e tiles (0xD00 bytes) em espaço livre
   do banco `$2E`:
   - `0x173820` (2 KB, livre);
   - `0x1751A0` (0xE60 bytes, livre).
4. Hook 65816 no loader da lenda:
   - dividir o DMA de 0x6000 bytes do frame 701 em três partes:
     `$7F:0000` (0x4000), fonte nova (0xD00), `$7F:5000` (0x1000);
   - trocar a origem do DMA do tilemap para o buffer novo;
   - validar no recomp nativo antes de gerar o BPS.
5. Atualizar hashes, gates SHA e este documento.

## Espaço livre

| File offset | Banco:endereço | Tamanho |
|---|---|---|
| `0x173820` | `$2E:B820` | 0x800 |
| `0x1751A0` | `$2E:D1A0` | 0xE60 |

O banco `$2E` é mapeado em LoROM como `$2E:8000-$FFFF`; os dois trechos
são preenchidos com `0x00` e não aparecem em nenhuma tabela de assets
conhecida.
