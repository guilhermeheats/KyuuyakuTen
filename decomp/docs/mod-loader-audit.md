# Mod loader — o que ele faz hoje

Auditoria do mod loader do recomp para decidir como a tradução e os mods
comunitários entram no projeto.

## O que existe

O framework tem pacotes `.snesmod`:

- ZIP com `manifest.toml` na raiz;
- metadados de pacote, features, opções e plugins confiáveis;
- validação de CRC, caminho, versão, tamanho e identidade da ROM;
- instalação atômica em `<exe-dir>/mods/preloaded/packages/`;
- features com opções boolean/choice/integer;
- plugins de ativação **confiáveis, já linkados no executável**.

Referências: `snesrecomp/docs/MOD_PACKAGES.md`,
`snesrecomp/docs/MOD_AUTHORING.md`,
`snesrecomp/docs/MOD_SHARED_RESOURCES.md`.

## Limitações atuais

- O pacote é **data-only**: não carrega código nativo, DLL, símbolo ou
  biblioteca.
- O vocabulário inicial é de **plugins de ativação confiáveis**.
- “Guarded ROM writes, asset overlays ou interpreter hooks” são trabalho
  futuro, segundo o próprio documento do framework.
- Não há, hoje, um overlay geral de texto/fonte/assets que permita publicar
  uma tradução completa como `.snesmod` sem suporte adicional.

## Implicações para este projeto

1. **Tradução inicial**: BPS patch sobre a ROM japonesa. É o caminho direto
   para EN/PT-BR e não depende do mod loader.
2. **Integração com o recomp**: depois, podemos ensinar o recomp a aceitar
   uma ROM traduzida/patch ou implementar overlay de texto/assets.
3. **Mods de dados**: pacotes `.snesmod` podem distribuir metadados,
   features e plugins confiáveis; overlay de assets precisa ser implementado
   e validado.
4. **Mods de código**: dependem de hooks/plugins confiáveis ou do decomp;
   não são o foco do M0/M1.

## Decisão de curto prazo

Não bloquear a tradução no mod loader. Primeiro:

- extrair/inserir texto e fonte;
- gerar BPS patch;
- validar em emulador/hardware/recomp.

Depois, avaliar um **overlay de texto/assets** no recomp para distribuir a
tradução como pacote e habilitar mods de dados comunitários.
