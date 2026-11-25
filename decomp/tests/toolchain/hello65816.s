; Minimal WLA-DX 65816 smoke test for the decomp toolchain.
.MEMORYMAP
  DEFAULTSLOT 0
  SLOTSIZE $8000
  SLOT 0 $8000
.ENDME

.ROMBANKSIZE $8000
.ROMBANKS 1

.BANK 0 SLOT 0
.ORG $0000

.SECTION "ResetSmoke" FORCE
Reset:
  sei
  clc
  xce
  lda #$01
  sta $7E0000
  jml Reset
.ENDS
