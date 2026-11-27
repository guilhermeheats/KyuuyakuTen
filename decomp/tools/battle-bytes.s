; 1-byte battle text codec: expand an ASCII code to a full-width Shift-JIS
; pair and reuse the stock glyph writer. Assembled at $29:FF20; called from
; the battle text interpreter at $02:B027.
.MEMORYMAP
  DEFAULTSLOT 0
  SLOTSIZE $8000
  SLOT 0 $8000
.ENDME

.ROMBANKSIZE $8000
.ROMBANKS 1

.BANK 0 SLOT 0
.ORG $7F20
.SECTION "BattleByteCodec" FORCE
BattleByteCodec:
  sec
  sbc #$20
  asl a
  tax
  lda.l $29FF40,x
  sta $01
  lda.l $29FF41,x
  sta $00
  jsl $01DFAD
  rtl
.ENDS
