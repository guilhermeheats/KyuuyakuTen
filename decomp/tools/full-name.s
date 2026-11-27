; Full demon name for the battle intro: 8x8 font, uppercase.
; Assembled at $2E:BF00; replaces the JSL $02C87B inside $02:BAD4.
.MEMORYMAP
  DEFAULTSLOT 0
  SLOTSIZE $8000
  SLOT 0 $8000
.ENDME

.ROMBANKSIZE $8000
.ROMBANKS 1

.BANK 0 SLOT 0
.ORG $3F00
.SECTION "FullName8c" FORCE
FullName8:
  php
  phb
  phk
  plb
  rep #$30
  phx
  phy
  and #$00FF
  sta $00
  sep #$20
  lda.l $7E1FF0
  beq NotFull8
  lda #$00
  sta.l $7E1FF0
  lda $00
  cmp #$FD
  bcs NotFull8
  lda $0CE8
  bne T2_8
  rep #$20
  lda $00
  asl a
  tax
  lda.l $2EBB38,x
  rep #$10
  tax
  bra Loop8
T2_8:
  rep #$20
  lda $00
  asl a
  tax
  cpx #$011C
  bcc T2ok8
  ldx #$011C
T2ok8:
  lda.l $2EBD32,x
  rep #$10
  tax
Loop8:
  sep #$20
  lda.l $2F0000,x
  beq Done8
  phx
  jsl $01E311
  plx
  sep #$20
  lda $0289
  beq NoWait8
  and #$7F
  pha
Wait8:
  lda $022F
  ora #$10
  sta $022F
  jsl $009397
  pla
  dec a
  bne Wait8
NoWait8:
  inx
  bra Loop8
Done8:
  lda #$00
  sta $0057
  bra Epilogue8
NotFull8:
  rep #$30
  lda $00
  jsl $02C87B
  sep #$20
  ldx #$0000
Copy8:
  lda $0022,x
  sta $0057,x
  inx
  cpx #$0009
  bne Copy8
Epilogue8:
  rep #$10
  ply
  plx
  plb
  plp
  rtl
.ENDS
