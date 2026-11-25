# Kyuuyaku Megami Tensei — decomp workspace

Este diretório é o início do **decomp source-level** de Kyuuyaku Megami Tensei
(MT1 primeiro, MT2 depois). Ele convive com o recomp em `../`:

- o recomp continua sendo o build nativo jogável e o **oráculo de
  comportamento**;
- o decomp é a fonte de verdade para tradução, mods e full-ROM matching;
- nenhuma ROM, asset original, C gerado ou save é commitado aqui.

## Decisões do projeto

- **Assembly estruturado matching primeiro**; C fiel/byte-matching depois da
  maturidade do projeto.
- Baseline full-ROM **byte-a-byte**: 65816 + SPC700 + dados/gráficos/áudio.
- **EN primeiro, PT-BR depois**; PT-BR direto do japonês, inglês como
  referência.
- Fan translation EN é referência de termos/encoding, não texto a copiar.
- **BPS patch primeiro**; integração com o recomp depois.
- Licença **BSD-3-Clause** para código/ferramentas/patch; o jogo/ROM/assets
  não são relicenciados.
- Créditos da fan translation no README do patch; tela de créditos depois,
  se viável.

## Toolchain

- **WLA-DX 10.9a**, commit `86fe2067d6f99cf7b4a765fb8a07d37180ecac92`.
- `wla-65816` para o CPU principal e `wla-spc700` para o áudio.
- O toolchain não é commitado. Use `tools/bootstrap_toolchain.sh` ou aponte
  `WLA_BIN` para uma instalação existente.

```bash
./tools/bootstrap_toolchain.sh
export WLA_BIN="$PWD/.toolchain/wla-dx/build/binaries"
make toolchain-test
```

## Comandos

```bash
make baseline       # verifica a ROM japonesa contra rom_identity.txt
make symbols        # exporta símbolos do recomp para build/symbols/
make text           # dump inicial das tabelas de nomes (build/text/)
make text-extract   # dump inicial do script Shift-JIS (build/text/)
make names          # decodifica nomes de demônios/itens para kana + CSV
make replace-test   # self-test da substituição de texto
make font-test      # self-test do mapa ASCII -> código de fonte
make fullwidth-test # self-test do codec full-width do diálogo
make bps-test       # self-test do BPS
make toolchain-test # monta 65816 + SPC700 de teste
make all
```

Saídas geradas ficam em `decomp/build/` e são ignoradas pelo git.

## Layout

```text
decomp/
  Makefile
  README.md
  docs/           # auditoria do mod loader, plano de texto, notas
  src/            # código decompilado (começa no M1)
  symbols/        # documentação do mapa de símbolos (saída gerada em build/)
  tests/          # testes de toolchain e de formatos
  tools/          # verificação de ROM, símbolos, BPS, texto
  toolchain.lock  # pin do WLA-DX
```

## Status

M0 em andamento:

- [x] toolchain 65816 + SPC700 escolhido e compilado;
- [x] workspace e regras source-only;
- [x] verificador de ROM/full-ROM matching;
- [x] exportador de símbolos do recomp;
- [x] ferramenta BPS com self-test;
- [x] dump inicial de tabelas de nomes e do script Shift-JIS;
- [x] extrator/substituidor de texto com BPS;
- [x] base VRAM da fonte da janela (`$6000` palavras) e ferramenta de
  inspeção de tiles;
- [x] ASCII de menu verificado (`font_code = ASCII - 0x1F`);
- [x] janela de diálogo 16x16 localizada e primeira fala decodificada;
- [x] renderizador de janela a partir de dump (`window_dump.py`);
- [x] auditoria do mod loader;
- [ ] confirmação de ASCII no renderizador do script (M1);
- [ ] agrupamento de mensagens pelo bytecode do script (M1);
- [ ] primeiro build mínimo do decomp (M1);
- [ ] matching 65816/SPC700 (M3).

## Regras

1. Não commitar ROM (`*.sfc`, `*.smc`), assets originais, C gerado,
   `decomp/build/`, saves ou screenshots.
2. O baseline de decomp deve ser construído a partir da ROM do usuário.
3. Toda ferramenta deve ser reproduzível e documentada.
4. O recomp é o oráculo: mudanças de comportamento devem ser comparadas com
   ele e com `snesref`/Mesen quando possível.
