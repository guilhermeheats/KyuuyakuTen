; Minimal WLA-DX SPC700 smoke test for the decomp toolchain.
.MEMORYMAP
  SLOTSIZE $8000
  DEFAULTSLOT 0
  SLOT 0 START $0000
.ENDME

.ROMBANKSIZE $8000
.ROMBANKS 1

.BANK 0 SLOT 0
.ORG 0

.SECTION "ResetSmoke" FORCE
Reset:
  nop
  bra Reset
.ENDS
