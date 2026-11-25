# Toolchain smoke test

Assembles a minimal 65816 image and a minimal SPC700 image with the pinned
WLA-DX. It proves both assemblers and the linker are usable before the decomp
source is populated.

Run from `decomp/`:

```bash
export WLA_BIN=/path/to/wla-dx/build/binaries
make toolchain-test
```

No game code or ROM data is included; this is only a build-system test.
