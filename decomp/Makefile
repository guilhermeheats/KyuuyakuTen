PYTHON ?= python3
ROOT := $(abspath ..)
BUILD ?= build
WLA_BIN ?= $(CURDIR)/.toolchain/wla-dx/build/binaries
export WLA_BIN

.PHONY: all baseline symbols text text-extract names replace-test font-test bps-test toolchain-test clean

all: baseline symbols text text-extract names replace-test font-test bps-test toolchain-test

baseline:
	$(PYTHON) tools/verify_rom.py --identity "$(ROOT)/rom_identity.txt"

symbols:
	$(PYTHON) tools/export_symbols.py --root "$(ROOT)" --out "$(BUILD)/symbols"

text:
	$(PYTHON) tools/scan_text.py --out "$(BUILD)/text/item_ptrs.json"

text-extract:
	$(PYTHON) tools/extract_text.py --out "$(BUILD)/text/script_jp.json" --jsonl

names:
	$(PYTHON) tools/dump_names.py --root "$(ROOT)" --out "$(BUILD)/text/names.json"

replace-test:
	$(PYTHON) tools/replace_text.py --selftest

font-test:
	$(PYTHON) tools/font_codec.py selftest

bps-test:
	$(PYTHON) tools/bps.py selftest

toolchain-test:
	$(MAKE) -C tests/toolchain WLA_BIN="$(WLA_BIN)" BUILD="$(abspath $(BUILD))/toolchain"

clean:
	rm -rf "$(BUILD)"
