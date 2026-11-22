# Crash intermitente: retorno de `ApuCommand` ($01:EBA5)

## Sintoma

Duas sessões longas terminaram em `SIGSEGV` no
`debug_server_record_frame` (`build-debug/crash_report_20261121_231216.json`
e `crash_report_20261122_002533.json`), com a CPU convidada em
`PC=$0000`, `PB=0`, `DB=0` e `S` por volta de `$1FD8`/`$1FDB`. O
`px_tripwire` apontava `Coverage_3F_C5B8` (APUUpdate), mas o ponto de
perda do controle era o retorno de `JSL $01:EBA5` (`ApuCommand`).

## Evidência no `trace_recent`

```text
JSL $01:EBA5            (ApuCommand)
FUNC_ENTRY $01:EBA5
? PC=$0000              (retorno perdido)
FUNC_ENTRY $00:ACDF     (destino errado; o chamador era $00:C646)
JSL $00:9397            (FrameWait)
FUNC_ENTRY $00:9397
? PC=$0000
```

O frame de retorno de 3 bytes do `JSL` foi consumido/deslocado; a CPU
caiu em `$00:ACDF`, executou `JSL $9397` e terminou em `PC=$0000`. O
`stack_balance` e o `S` dos dois relatórios confirmam o desalinhamento
de pilha. O `Coverage_3F_C5B8` é só o chamador do caminho APU.

## Causa

A variante AOT `Coverage_01_EBA5_V10_M1X1` não preserva o retorno do
`JSL` quando chamada com M=1/X=1. O dispatch de `$3F:C5B8` já manda
M1X0/M1X1 para a LLE autoritativa, mas o dispatch de `$01:EBA5` ainda
usava a variante AOT.

O próprio manifesto de análise já marcava os dois call sites como não
provados:

```text
truncated_call_at_018EAF_to_01EBA5
unproven_call_at_018EAF_to_01EBA5_m1x1
truncated_call_at_02EE38_to_01EBA5
unproven_call_at_02EE38_to_01EBA5_m1x0
```

Ou seja: a promoção AOT dessas variantes não deveria ter sido feita.

## Correção interina (substituída em 2026-11-22)

> Esta foi a primeira correção, mantida aqui como histórico. O
> all-AOT estrito foi restaurado depois pela correção definitiva do
> bounce do interpretador (seção mais abaixo).

- `recomp/symbols.toml`: `ApuCommand` com `emit = false`.
- `recomp/bank01.cfg`: removida a raiz
  `func Coverage_01_EBA5_V10 eba5 entry_mx:1,0`; o sync gera
  `force_lle 01eba5`.
- `tools/regen.sh`: 83 roots, **153 variantes AOT + 2 LLE-only**;
  `src/gen` sem `Coverage_01_EBA5`.
- Binário: `build-debug/KyuuyakuTen` SHA-256
  `7745ba22a5ddb2bbb1d4a3c72d05a6323238b11c1403c3902daf3a6d6c870f79`.

Uma única função fica na LLE (não é HLE); as outras 153 variantes
continuam AOT. A LLE preserva a pilha convidada exatamente e mantém o
áudio/APU funcionando.

## Tentativa all-AOT estrito (2026-11-22)

Tentei manter o `ApuCommand` AOT fixando o corpo canônico M1X0 nos
quatro call sites com `force_variant_at` (`00c646`, `009143`,
`018eaf`, `02ee38`). O `program_emit` descartava esses pins
(`set_force_variant_at({})`); liguei os pins dos cfgs ao emissor e
regenerei **1460 variantes AOT, 0 LLE-only** (binário `d2c3584d…`).

O `savequick` do all-AOT original carregou; após ~183.600 frames veio
o mesmo `signal 11` (`addr=0x1000a44b4`, `PC=0`). O `trace_recent`
agora termina em `FUNC_ENTRY $00:9397` (**FrameWait**) com `P=0x16`
(M0X1) e `S=8165`, seguido de `PC=0`. O defeito de frame de retorno
também existe na variante **M0X1 do FrameWait**, que é um root AOT
chamado pelo driver de frame.

Conclusão: o all-AOT estrito exige corrigir o host-return das
variantes M/X do caminho `FrameWait`/`ApuCommand` (ou forçar LLE nos
call sites não provados desse caminho), não só do `ApuCommand`. O
fallback LLE foi restaurado; o rebuild é byte-idêntico ao binário
validado `7745ba22…`.

## Correção definitiva (2026-11-22)

O bounce interpretador → AOT (`cpu_dispatch_pc_paired`) empilha o
frame clássico (PCL em `_entry_s`), mas o prólogo AOT amostrava o
retorno em `_entry_s+1/+2/+3` (layout do tailcall). O
`_host_return_pc24` não casava com o PC popped; o RTL despachava no
meio do bloco e o miss terminava em `PC=0`.

- Globais `g_aot_host_return_override`/`_valid` (fora do `CpuState`,
  sem impacto no savestate).
- `cpu_dispatch_pc_paired(..., return_pc24)`: o bridge passa a
  continuação exata e prime o override antes de chamar o corpo AOT.
- O prólogo AOT consome o override; os chamadores AOT (override
  clear) mantêm o dispatch normal — a lógica de batalha não muda.
- `interp_bridge.c` calcula `pc_before + 4` (JSL) / `+3` (JSR).
- `bank30.cfg`: os seis `hle_dispatch ... __runtime_indirect__`
  passam a usar `__balanced_interp__` (LLE balanceada do emissor);
  o link error do helper HLE antigo desaparece e o texto/menus roda
  o ROM real.
- `emit_function.py`: restaurados `terminal_jsl_sites`/
  `noreturn_jsl_sites` (WIP que o `git checkout` apagou) e o consumo
  do override.

Regen: **1460 variantes AOT, 0 LLE-only** (all-AOT estrito). Binário
`aeed2baaff547b6ded17e800a7bd1ef8ca20d2cd859effd3ba520fbe0d43cec6`.
`save8` carrega, campo 60,6 FPS, menu COMP e batalha OK; stress de
72.000 frames em andamento.

## Follow-up

- Repetir o stress longo e monitorar `crash_report_*` (o crash era
  intermitente; o último relatório é o do experimento AOT-pin).
- O caminho `FrameWait`/`ApuCommand` continua coberto pelo override
  do bridge; se um novo relatório aparecer, conferir o
  `g_aot_host_return_override`/o frame do bridge.
- Rota 2F/1F segue bloqueada (ver `route-3f-junks.md`).

## Validação

- `loadstate 8` (JUNKS), caminhada, batalha, savestate, screenshot e
  áudio OK com o binário novo (HP 999/999 preservado).
- Stress de **36.000 frames** (60 × `step 600`, ~10,6 min) sem crash e
  sem `crash_report_*` novo. O `step` deixa o jogo pausado; `continue`
  retomou.
- FPS em campo: **58,96** (8 s). Em batalha aguardando input: ~47,5
  (custo do caminho LLE + batalha; follow-up de performance).
- `src/gen/dispatch_v2.c`: `{ 0x018EABu, { NULL, NULL, NULL, NULL }, 0 }`
  (`FrameWaitWrapper` LLE) e chamadas
  `interp_tier_run_call_frame(cpu, 0x018eabu, 0x0093b4u, 3, NULL)`.
  Não existe `Coverage_01_EBA5` no `src/gen`; o cfg tem
  `force_lle 01eba5`.
- O `dispatch_log_get` registra o chamador (`interp@$0093C2`), não o
  alvo LLE interno; a ausência de `01EBA5` no log é esperada.

## Stress final do all-AOT `04f3a5e1` (2026-11-22)

Binário `build-debug/KyuuyakuTen` SHA-256
`04f3a5e1a2ff6770199203d30a8b2fd6d10ce52ee513010d012ab0ebbe592add`,
1460 variantes AOT / 0 LLE-only.

- **72.000 frames de campo** (120 × `step 600`) a partir do `save10`
  (4F `(19,5)`, área `01`): frame `648.295 → 720.295`, posição e área
  estáveis, nenhum `crash_report_*` novo.
- **28.800 frames no padrão do crash antigo** (200 ciclos de
  `right → step 4 → clear_controller → step 140`): nenhum crash; a
  posição permaneceu `(19,5)` e o `facing` completou as voltas.
- **Batalha aleatória** (Dryad no 4F): menu de batalha, 100 ciclos do
  mesmo padrão (14.400 frames) e ataques até encerrar; nenhum crash.
- `save_state`/`load_state` L3 restaurou `(19,5)`; os slots 0–11 do
  debug server não foram tocados (`save12` não é gravável: o servidor
  aceita apenas 0–11).
- FPS em campo: **60,19** (8 s); durante o spin de batalha: ~56,1.
- RSS: **636 MB** no início, **676 MB** após os 72k, **678 MB** após o
  turn stress, sem crescimento depois do bloco 30.
- Screenshot 256×224 de campo e de batalha limpos; HP 999/999
  preservado. Último `crash_report` continua sendo o anterior ao fix
  (`20261122_043727`).
