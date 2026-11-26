PYTHON ?= python3
ROOT := $(abspath ..)
BUILD ?= build
WLA_BIN ?= $(CURDIR)/.toolchain/wla-dx/build/binaries
export WLA_BIN

.PHONY: all baseline symbols text text-extract messages names replace-test font-test fullwidth-test bps-test toolchain-test menu-en script-en clean

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

script-en:
	$(PYTHON) tools/replace_text.py --translations translations/script_en.json \
		--patch-name "Kyuuyaku Megami Tensei English script" \
		--out "$(BUILD)/rom/script_en.sfc" \
		--patch "$(BUILD)/rom/script_en.bps" \
		--report "$(BUILD)/rom/script_en_report.json"

clean:
	rm -rf "$(BUILD)"
