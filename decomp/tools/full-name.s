; Full demon name for the battle intro: 16x16 dialogue font, mixed case.
; Assembled at $2E:BF00; replaces the JSL $02C87B inside $02:BAD4.
; The 8x8 name codes are mapped through a 256-entry Shift-JIS table at
; $2E:DD08 and drawn with $01DFAD, so the dialogue font's lowercase Latin
; block is used. The race prefix was already drawn in 8x8.
.MEMORYMAP
  DEFAULTSLOT 0
  SLOTSIZE $8000
  SLOT 0 $8000
.ENDME

.ROMBANKSIZE $8000
.ROMBANKS 1

.BANK 0 SLOT 0
.ORG $3F00
.SECTION "FullName" FORCE
FullName:
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
  beq NotFull
  lda #$00
  sta.l $7E1FF0
  lda $00
  cmp #$FD
  bcs NotFull
  lda $0CE8
  bne T2
  rep #$20
  lda $00
  asl a
  tax
  lda.l $2EBB38,x
  rep #$10
  tax
  bra CopyFull
T2:
  rep #$20
  lda $00
  asl a
  tax
  cpx #$011C
  bcc T2ok
  ldx #$011C
T2ok:
  lda.l $2EBD32,x
  rep #$10
  tax
CopyFull:
  sep #$20
NameLoop:
  lda.l $2F0000,x
  beq NameDone
  rep #$20
  and #$00FF
  asl a
  tay
  lda $DD08,y
  beq NameSkip
  xba
  sta $00
  phx
  jsl $01DFAD
  plx
  sep #$20
  lda $0289
  beq NameNoWait
  and #$7F
  pha
NameWait:
  lda $022F
  ora #$10
  sta $022F
  jsl $009397
  pla
  dec a
  bne NameWait
NameNoWait:
NameSkip:
  inx
  bra NameLoop
NameDone:
  lda #$00
  sta $0057
  bra Epilogue
NotFull:
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
Epilogue:
  rep #$10
  ply
  plx
  plb
  plp
  rtl
.ENDS
