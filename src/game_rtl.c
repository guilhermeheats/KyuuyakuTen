#include "game_rtl.h"

#include <string.h>

#include "beam_frame_driver.h"

void GameRunOneFrame(void)
{
    snes_beam_frame_driver_run_frame();
}

void GameDrawPpuFrame(void)
{
    snes_beam_frame_driver_draw_ppu_frame();
}

void GameSessionReset(void)
{
    /* Rematch / soft-return: clear anything that must not survive a new
     * session. recomp-ai-rules/NETPLAY.md §3 — sticky state that "has always
     * been fine" is the usual desync culprit, because single-player never
     * re-enters the boot path twice in one process. */
    snes_beam_frame_driver_reset();
}

const RtlGameInfo kGameInfo = {
    .title = "kyuuyakuten",
    .initialize = NULL,
    .run_frame = &GameRunOneFrame,
    .draw_ppu_frame = &GameDrawPpuFrame,
    .save_name_prefix = "save",
    .session_reset = &GameSessionReset,
    .hardware_reset = &GameSessionReset,
    .state_save_extra = &snes_beam_frame_driver_state_save,
    .state_load_extra = &snes_beam_frame_driver_state_load,
    .on_state_loaded = &snes_beam_frame_driver_state_loaded,
    .snapshot_guard_identity = &snes_beam_frame_driver_state_identity,
    .snapshot_preflight = &snes_beam_frame_driver_state_preflight,
};
