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
; Both paths finish the stock continuation at $02:B037: the original path
; consumes the second byte, the 1-byte path only consumes the byte already
; read at $02:B01B. Codec at $11:A6C6; dispatcher at $11:A6E6; full-width
; table at $11:A740.
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
BattleByteCodec:
  phx
  sec
  sbc #$20
  asl a
  tax
  lda.l $11A740,x
  sta $01
  lda.l $11A741,x
  sta $00
  plx
  jsl $01DFAD
  jml $02B037
.ENDS

.BANK 0 SLOT 0
.ORG $26E6
.SECTION "BattleByteDispatch" FORCE
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
