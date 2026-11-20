/* Hand-written bodies for code the recompiler could not translate.
 *
 * The window/text chain below runs the original ROM bytes in the byte
 * interpreter. The AOT bodies of these routines fragment the window text
 * (16-pixel kanji); the interpreter reproduces the original output.
 * Each helper owns the replaced routine's frame: the interpreter charges the
 * original cycles and pops exactly what the original RTS/RTL pops.
 */

#include "cpu_state.h"

/* $01:D61B — builds the window map/records. Called with JSL, returns RTL. */
RecompReturn HleTextWindowMapBuild(CpuState *cpu) {
    return interp_tier_run_call_frame(
        cpu, 0x01D61Bu, 0x01D61Bu, 3 /* JSL/RTL frame */, NULL);
}

/* $01:D419 — draws one glyph page entry. Called with JSR, returns RTS. */
RecompReturn HleTextGlyphD419(CpuState *cpu) {
    return interp_tier_run_call_frame(
        cpu, 0x01D419u, 0x01D419u, 2 /* JSR/RTS frame */, NULL);
}

/* $01:D581 — draws one glyph page entry. JSR/RTS. */
RecompReturn HleTextGlyphD581(CpuState *cpu) {
    return interp_tier_run_call_frame(
        cpu, 0x01D581u, 0x01D581u, 2 /* JSR/RTS frame */, NULL);
}

/* $01:D5B3 — draws one glyph page entry. JSR/RTS. */
RecompReturn HleTextGlyphD5B3(CpuState *cpu) {
    return interp_tier_run_call_frame(
        cpu, 0x01D5B3u, 0x01D5B3u, 2 /* JSR/RTS frame */, NULL);
}

/* $01:E311 — character-code -> font-page dispatch. JSL/RTL. */
RecompReturn HleTextCharDispatch(CpuState *cpu) {
    return interp_tier_run_call_frame(
        cpu, 0x01E311u, 0x01E311u, 3 /* JSL/RTL frame */, NULL);
}

/* $01:DFBF — glyph wrapper (E2BD + DFCE). JSL/RTL. */
RecompReturn HleTextGlyphWrapper(CpuState *cpu) {
    return interp_tier_run_call_frame(
        cpu, 0x01DFBFu, 0x01DFBFu, 3 /* JSL/RTL frame */, NULL);
}

/* $01:DFAD — dialogue glyph draw wrapper. JSL/RTL.
 * $E22E (code -> font index), $E2BD (font pointer) and $DFCE (blitter) are
 * all executed from the original ROM bytes by the interpreter. */
RecompReturn HleDialogueGlyphDraw(CpuState *cpu) {
    return interp_tier_run_call_frame(
        cpu, 0x01DFADu, 0x01DFADu, 3 /* JSL/RTL frame */, NULL);
}

/* $01:E22E — character code -> 12x12 font index. JSR/RTS.
 * The AOT body mis-computes the index; the interpreter follows the original
 * arithmetic and the $E25B/$E27B tables. */
RecompReturn HleTextFontIndex(CpuState *cpu) {
    return interp_tier_run_call_frame(
        cpu, 0x01E22Eu, 0x01E22Eu, 2 /* JSR/RTS frame */, NULL);
}

/* $01:E2BD — character code -> glyph source pointer. JSR/RTS. */
RecompReturn HleTextGlyphPointer(CpuState *cpu) {
    return interp_tier_run_call_frame(
        cpu, 0x01E2BDu, 0x01E2BDu, 2 /* JSR/RTS frame */, NULL);
}

/* $01:DFCE — window text glyph rasterizer. JSR/RTS. */
RecompReturn HleWindowTextRender(CpuState *cpu) {
    return interp_tier_run_call_frame(
        cpu, 0x01DFCEu, 0x01DFCEu, 2 /* JSR/RTS frame */, NULL);
}

/* $03:8834 — ITEM/STATUS page entry (window state + item slots). JSL/RTL. */
RecompReturn HleItemPageEntry(CpuState *cpu) {
    return interp_tier_run_call_frame(
        cpu, 0x038834u, 0x038834u, 3 /* JSL/RTL frame */, NULL);
}

/* $02:C87B — ITEM name builder. JSL/RTL (frame 3). The AOT body builds the
 * wrong name string for shop/menu item IDs; the interpreter follows the ROM
 * tables at $11:CDFD/$11:D5A8 and $0C40 exactly. */
RecompReturn HleItemNameBuild(CpuState *cpu) {
    return interp_tier_run_call_frame(
        cpu, 0x02C87Bu, 0x02C87Bu, 3 /* JSL/RTL frame */, NULL);
}

/* $03:91F8 — ITEM window list renderer. JSR/RTS (frame 2). */
RecompReturn HleItemListRender(CpuState *cpu) {
    return interp_tier_run_call_frame(
        cpu, 0x0391F8u, 0x0391F8u, 2 /* JSR/RTS frame */, NULL);
}
