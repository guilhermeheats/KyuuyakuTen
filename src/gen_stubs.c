/* Hand-written bodies for code the recompiler could not translate.
 *
 * All gameplay code is AOT now, including the window-text chain, the
 * item-name builder, and the ITEM/STATUS page entry and list renderer.
 * This translation unit stays in the build's source list so regeneration
 * does not need to special-case its absence.
 */
#include "cpu_state.h"
