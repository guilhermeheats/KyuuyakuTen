; Full race name for the battle intro: 8x8 font, uppercase.
; Assembled at $2E:BE90; called from the text renderer's 01 0C handler.
.MEMORYMAP
  DEFAULTSLOT 0
  SLOTSIZE $8000
  SLOT 0 $8000
.ENDME

.ROMBANKSIZE $8000
.ROMBANKS 1

.BANK 0 SLOT 0
.ORG $3E90
.SECTION "FullRace" FORCE
FullRace:
  php
  phb
  phk
  plb
  sep #$30
  lda $048C
  jsl $02BF75
  pha
  lda #$01
  sta.l $7E1FF0
  pla
  asl a
  tax
  rep #$20
  lda.l $2EBE50,x
  rep #$10
  tax
RaceLoop:
  sep #$20
  lda.l $2E0000,x
  beq RaceDone
  phx
  jsl $01E311
  plx
  sep #$20
  lda $0289
  beq RaceNoWait
  and #$7F
  pha
RaceWait:
  lda $022F
  ora #$10
  sta $022F
  jsl $009397
  pla
  dec a
  bne RaceWait
RaceNoWait:
  inx
  bra RaceLoop
RaceDone:
  plb
  plp
  rtl
.ENDS
