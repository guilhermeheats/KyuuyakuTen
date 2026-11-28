PYTHON ?= python3
ROOT := $(abspath ..)
BUILD ?= build
ROM ?= $(shell cat "$(ROOT)/rom.cfg" 2>/dev/null)
BASE_ROM_ARG := $(if $(ROM),--base-rom "$(ROM)")
WLA_BIN ?= $(CURDIR)/.toolchain/wla-dx/build/binaries
export WLA_BIN

.PHONY: all baseline symbols text text-extract messages names names-en names-inplace replace-test font-test fullwidth-test bps-test toolchain-test menu-en menu-pt startup-pt bank0f-pt script-en script-pt battle-en battle-pt full-pt races-en full-en full-names clean

all: baseline symbols text text-extract messages names replace-test font-test fullwidth-test bps-test toolchain-test

baseline:
	$(PYTHON) tools/verify_rom.py --identity "$(ROOT)/rom_identity.txt"

symbols:
	$(PYTHON) tools/export_symbols.py --root "$(ROOT)" --out "$(BUILD)/symbols"

text:
	$(PYTHON) tools/scan_text.py --out "$(BUILD)/text/item_ptrs.json"

text-extract:
	$(PYTHON) tools/extract_text.py --out "$(BUILD)/text/script_jp.json" --jsonl

messages:
	$(PYTHON) tools/extract_messages.py --out "$(BUILD)/text/messages.json"

names:
	$(PYTHON) tools/dump_names.py --root "$(ROOT)" --out "$(BUILD)/text/names.json"

replace-test:
	$(PYTHON) tools/replace_text.py --selftest

font-test:
	$(PYTHON) tools/font_codec.py selftest

fullwidth-test:
	$(PYTHON) tools/fullwidth.py selftest

bps-test:
	$(PYTHON) tools/bps.py selftest

toolchain-test:
	$(MAKE) -C tests/toolchain WLA_BIN="$(WLA_BIN)" BUILD="$(abspath $(BUILD))/toolchain"

menu-en:
	$(PYTHON) tools/replace_text.py --translations translations/menu_en.json \
		--raw-patches translations/raw_en.json \
		--patch-name "Kyuuyaku Megami Tensei English UI" \
		--out "$(BUILD)/rom/menu_en.sfc" \
		--patch "$(BUILD)/rom/menu_en.bps" \
		--report "$(BUILD)/rom/menu_en_report.json"

menu-pt:
	$(PYTHON) tools/replace_text.py --translations translations/menu_pt.json \
		--raw-patches translations/raw_en.json \
		--patch-name "Kyuuyaku Megami Tensei Portuguese UI" \
		--out "$(BUILD)/rom/menu_pt.sfc" \
		--patch "$(BUILD)/rom/menu_pt.bps" \
		--report "$(BUILD)/rom/menu_pt_report.json"

startup-pt: menu-pt
	$(PYTHON) tools/replace_text.py --rom "$(BUILD)/rom/menu_pt.sfc" \
		--translations translations/startup_pt.json \
		--raw-patches translations/startup_raw.json \
		--out "$(BUILD)/rom/startup_pt.sfc" \
		--report "$(BUILD)/rom/startup_pt_report.json"

bank0f-pt: startup-pt
	$(PYTHON) tools/replace_text.py --rom "$(BUILD)/rom/startup_pt.sfc" \
		--translations translations/bank0f_pt.json \
		--out "$(BUILD)/rom/bank0f_pt.sfc" \
		--report "$(BUILD)/rom/bank0f_pt_report.json"

script-en: menu-en
	$(PYTHON) tools/replace_text.py --rom "$(BUILD)/rom/menu_en.sfc" \
		--translations translations/script_en.json \
		--patch-name "Kyuuyaku Megami Tensei English script" \
		--out "$(BUILD)/rom/script_en.sfc" \
		--patch "$(BUILD)/rom/script_en.bps" \
		--report "$(BUILD)/rom/script_en_report.json"

script-pt: menu-pt
	$(PYTHON) tools/replace_text.py --rom "$(BUILD)/rom/menu_pt.sfc" \
		--translations translations/script_pt.json \
		--patch-name "Kyuuyaku Megami Tensei Portuguese script" \
		--out "$(BUILD)/rom/script_pt.sfc" \
		--patch "$(BUILD)/rom/script_pt.bps" \
		--report "$(BUILD)/rom/script_pt_report.json"

names-en:
	$(PYTHON) tools/patch_names.py --translations translations/names_en.json \
		--patch-name "Kyuuyaku Megami Tensei English names" \
		--out "$(BUILD)/rom/names_en.sfc" \
		--patch "$(BUILD)/rom/names_en.bps" \
		--report "$(BUILD)/rom/names_en_report.json"

names-inplace:
	$(PYTHON) tools/patch_names.py --in-place --translations translations/names_en.json \
		--patch-name "Kyuuyaku Megami Tensei English names (in-place)" \
		--out "$(BUILD)/rom/names_inplace.sfc" \
		--patch "$(BUILD)/rom/names_inplace.bps" \
		--report "$(BUILD)/rom/names_inplace_report.json"

battle-en: script-en
	$(PYTHON) tools/patch_battle.py --rom "$(BUILD)/rom/script_en.sfc" \
		--translations translations/battle_en.json \
		--patch-name "Kyuuyaku Megami Tensei English battle text" \
		--out "$(BUILD)/rom/script_battle_en.sfc" \
		--patch "$(BUILD)/rom/script_battle_en.bps" \
		--report "$(BUILD)/rom/script_battle_en_report.json"

battle-pt: script-en
	$(PYTHON) tools/patch_battle.py --rom "$(BUILD)/rom/script_en.sfc" \
		--translations translations/battle_pt.json --encoding byte \
		--patch-name "Kyuuyaku Megami Tensei Portuguese battle text" \
		--out "$(BUILD)/rom/script_battle_pt.sfc" \
		--patch "$(BUILD)/rom/script_battle_pt.bps" \
		--report "$(BUILD)/rom/script_battle_pt_report.json"

full-pt: bank0f-pt
	$(PYTHON) tools/replace_text.py --rom "$(BUILD)/rom/bank0f_pt.sfc" \
		--translations translations/script_pt.json \
		--out "$(BUILD)/rom/script_pt_ui.sfc" \
		--report "$(BUILD)/rom/script_pt_ui_report.json"
	$(PYTHON) tools/patch_races.py --rom "$(BUILD)/rom/script_pt_ui.sfc" \
		--translations translations/races_pt.json \
		--out "$(BUILD)/rom/script_pt_races.sfc" \
		--report "$(BUILD)/rom/pt_races_report.json"
	$(PYTHON) tools/patch_names.py --rom "$(BUILD)/rom/script_pt_races.sfc" \
		$(BASE_ROM_ARG) --translations translations/names_en.json \
		--out "$(BUILD)/rom/script_pt_names.sfc" \
		--report "$(BUILD)/rom/pt_names_report.json"
	$(PYTHON) tools/patch_full_names.py --rom "$(BUILD)/rom/script_pt_names.sfc" \
		$(BASE_ROM_ARG) --names translations/names_en.json --races translations/races_pt.json \
		--out "$(BUILD)/rom/pt_full_names.sfc" \
		--report "$(BUILD)/rom/pt_full_names_report.json"
	$(PYTHON) tools/patch_battle.py --rom "$(BUILD)/rom/pt_full_names.sfc" \
		$(BASE_ROM_ARG) --translations translations/battle_pt.json --encoding byte \
		--patch-name "Kyuuyaku Megami Tensei Portuguese translation" \
		--out "$(BUILD)/rom/full_pt.sfc" \
		--patch "$(BUILD)/rom/full_pt.bps" \
		--report "$(BUILD)/rom/full_pt_report.json"

races-en: battle-en
	$(PYTHON) tools/patch_races.py --rom "$(BUILD)/rom/script_battle_en.sfc" \
		--translations translations/races_en.json \
		--patch-name "Kyuuyaku Megami Tensei English battle races" \
		--out "$(BUILD)/rom/script_battle_races.sfc" \
		--patch "$(BUILD)/rom/races_en.bps" \
		--report "$(BUILD)/rom/races_en_report.json"

full-en: races-en
	$(PYTHON) tools/patch_names.py --rom "$(BUILD)/rom/script_battle_races.sfc" \
		$(BASE_ROM_ARG) --translations translations/names_en.json \
		--patch-name "Kyuuyaku Megami Tensei English full text" \
		--out "$(BUILD)/rom/full_en.sfc" \
		--patch "$(BUILD)/rom/full_en.bps" \
		--report "$(BUILD)/rom/full_en_names_report.json"

full-names: full-en
	$(PYTHON) tools/patch_full_names.py --rom "$(BUILD)/rom/full_en.sfc" \
		$(BASE_ROM_ARG) --names translations/names_en.json --races translations/races_pt.json \
		--patch-name "Kyuuyaku Megami Tensei English full battle names" \
		--out "$(BUILD)/rom/full_names.sfc" \
		--patch "$(BUILD)/rom/full_names.bps" \
		--report "$(BUILD)/rom/full_names_report.json"

clean:
	rm -rf "$(BUILD)"
