# Dados extraídos — Torre de Daedalus

Esta pasta contém **dados factuais** (coordenadas, tipos de evento, tabelas de
encontros e preços) extraídos de fontes públicas e da tabela derivada do ROM.
Não há imagens de mapas, ROM, assets, saves ou screenshots versionados aqui.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `daedalus-8f.json` | Eventos do 8F (Mikon City), coordenadas Atlas, conexão da escada |
| `daedalus-7f.json` | Eventos do 7F, componentes desconectados, escadas, batalhas fixas |
| `daedalus-encounters.json` | Tabelas de encontros 8F–5F e 4F–1F |
| `daedalus-shop.json` | Estoque e preços da loja do 8F |
| `daedalus-junks.json` | JUNKS da 3F 2ª seção: rota, menu e estoque validados no all-AOT |

## Fontes

- Tabela de eventos, encontros e loja derivada do ROM:
  <https://pareido.jp/cyber-newtown/megaten-daedalus/nam-mt-dg-0/>
- Rota e mapas de speedrun (SNES):
  <https://sioneus.me/notes/kmt1>
- Detonado/tradução (SNES), incluindo o Gate Keeper e as batalhas fixas do 7F:
  <https://gamefaqs.gamespot.com/snes/581301-kyuuyaku-megami-tensei/faqs/54063?print=1>
- Mapas da comunidade (FC/NES, usados só para topologia):
  <https://aruto.info/dds/dds1/map1.html> e
  <https://grappli.net/strategy/megamitensei1/story-daidaros-kouryaku/>
- Auto-map SNES (8F/7F) do opatil:
  <https://dds.opatil.com/kmt1/story/c01.html>
- Sistema SNES e Gate Keeper azul (Cielgrand):
  <https://cielgrand.web.fc2.com/retrogame/ddsmegaten1.html>

## Ressalvas

- As coordenadas são **Atlas/ROM**, não necessariamente a célula local do
  jogador. Objetos como o baú podem ser abertos a partir de uma célula
  adjacente.
- Os mapas do aruto/grappli são da versão FC; a versão SNES tem uma loja única
  em vez de lojas separadas de arma/armadura. Use-os para topologia, não para
  coordenadas exatas.
- O JUNKS é uma instalação da 3F 2ª seção. As coordenadas em
  `daedalus-junks.json` são **WRAM** `(112,19)`, com entrada a partir de
  `(113,19)` virado para oeste; não são coordenadas Atlas.
- O 7F tem duas partes desconectadas. A escada do 8F cai na componente #1;
  a componente #2 só é alcançada pelo 6F em `(15,3)`.
- A tabela derivada do ROM não lista batalhas fixas no 7F, mas o detonado e o
  mapa da Sion listam Basim e Gnome como encontros não aleatórios. Os tiles
  exatos ainda não foram confirmados no jogo.
