; Full demon-name copy for the battle intro.
; Assembled at $2E:BF40; replaces the JSL $02C87B inside $02:BAD4.
; Writes to the direct-page scratch buffer at $57 and lets the patched
; display loop render it. The race routine sets $7E:1FF0, so only the
; race+name intro uses the full table; other <04> messages keep the
; eight-character T1/T2 names.
.MEMORYMAP
  DEFAULTSLOT 0
  SLOTSIZE $8000
  SLOT 0 $8000
.ENDME

.ROMBANKSIZE $8000
.ROMBANKS 1

.BANK 0 SLOT 0
.ORG $3F40
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
  ldy #$0000
CopyLoop:
  lda.l $2F0000,x
  beq CopyDone
  sta $0057,y
  inx
  iny
  cpy #$0010
  bne CopyLoop
CopyDone:
  lda #$00
  sta $0057,y
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
