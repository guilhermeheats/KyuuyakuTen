PYTHON ?= python3
ROOT := $(abspath ..)
BUILD ?= build
WLA_BIN ?= $(CURDIR)/.toolchain/wla-dx/build/binaries
export WLA_BIN

.PHONY: all baseline symbols text bps-test toolchain-test clean

all: baseline symbols text bps-test toolchain-test

baseline:
	$(PYTHON) tools/verify_rom.py --identity "$(ROOT)/rom_identity.txt"

symbols:
	$(PYTHON) tools/export_symbols.py --root "$(ROOT)" --out "$(BUILD)/symbols"

text:
	$(PYTHON) tools/scan_text.py --out "$(BUILD)/text/item_ptrs.json"

bps-test:
	$(PYTHON) tools/bps.py selftest

toolchain-test:
	$(MAKE) -C tests/toolchain WLA_BIN="$(WLA_BIN)" BUILD="$(abspath $(BUILD))/toolchain"

clean:
	rm -rf "$(BUILD)"
