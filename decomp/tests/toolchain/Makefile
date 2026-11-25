WLA_BIN ?= ../../.toolchain/wla-dx/build/binaries
BUILD ?= ../../build/toolchain
WLA_65816 := $(WLA_BIN)/wla-65816
WLA_SPC700 := $(WLA_BIN)/wla-spc700
WLALINK := $(WLA_BIN)/wlalink

.PHONY: all clean
all: $(BUILD)/hello65816.sfc $(BUILD)/hello_spc700.bin

$(BUILD):
	mkdir -p "$@"

$(BUILD)/hello65816.o: hello65816.s | $(BUILD)
	$(WLA_65816) -o "$@" "$<"

$(BUILD)/hello65816.sfc: $(BUILD)/hello65816.o
	printf '[objects]\n%s\n' "$(abspath $<)" > "$(BUILD)/linkfile65816"
	$(WLALINK) -i -v -s "$(BUILD)/linkfile65816" "$@"

$(BUILD)/hello_spc700.o: hello_spc700.s | $(BUILD)
	$(WLA_SPC700) -o "$@" "$<"

$(BUILD)/hello_spc700.bin: $(BUILD)/hello_spc700.o
	printf '[objects]\n%s\n' "$(abspath $<)" > "$(BUILD)/linkfile_spc700"
	$(WLALINK) -i -S "$(BUILD)/linkfile_spc700" "$@"

clean:
	rm -rf "$(BUILD)"
