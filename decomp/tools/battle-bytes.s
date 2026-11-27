; 1-byte battle text codec and dispatcher.
;
; All new code/data lives in the old bank-$11 battle message pool
; ($11:A6C6-$B13D), which was message data, not dialogue-font source. The
; battle table/messages have moved to bank $29 and the old pool is unused.
;
; The dispatcher checks the current message pointer ($42/$43) and bank ($44).
; Only pointers inside the two repacked battle holes in bank $29
; ($B940-$BFFF and $F820-$FFFF) use the 1-byte codec; every other message
; (COMP, story, menus) takes the stock two-byte path.
;
; The battle path uses the stock 8x8 glyph drawer at $01E311 (the same
; routine used by race/name text) instead of the 16x16 dialogue writer at
; $01DFAD. This keeps the battle line small and allows more characters per
; row. The codec converts ASCII to the 8x8 font code (ASCII - $1F), draws
; one glyph, and resumes the stock continuation at $02:B037. The 1-byte path
; skips the second-byte pointer advance because $02:B01B already consumed
; its byte. Codec at $11:A6C6; dispatcher at $11:A6E6.
.MEMORYMAP
  DEFAULTSLOT 0
  SLOTSIZE $8000
  SLOT 0 $8000
.ENDME

.ROMBANKSIZE $8000
.ROMBANKS 1

.BANK 0 SLOT 0
.ORG $26C6
.SECTION "BattleByteCodec" FORCE
.ACCU 8
.INDEX 8
BattleByteCodec:
  phx
  cmp #$20
  beq Space
  sec
  sbc #$1F
  jsl $01E311
  plx
  jml $02B037
Space:
  php
  rep #$20
  inc $024E
  plp
  plx
  jml $02B037
.ENDS

.BANK 0 SLOT 0
.ORG $26E6
.SECTION "BattleByteDispatch" FORCE
.ACCU 8
.INDEX 8
BattleByteDispatch:
  pha
  lda $44
  cmp #$29
  bne OriginalPath
  lda $43
  cmp #$B9
  bcc CheckF8
  cmp #$C0
  bcc CodecPath
CheckF8:
  cmp #$F8
  bcs CodecPath
OriginalPath:
  pla
  sta $01
  lda [$42]
  sta $00
  jsl $01DFAD
  inc $42
  bne AfterInc
  inc $43
AfterInc:
  jml $02B037
CodecPath:
  pla
  jml $11A6C6
.ENDS
