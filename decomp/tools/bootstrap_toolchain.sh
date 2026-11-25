#!/usr/bin/env bash
# Build the pinned WLA-DX toolchain inside decomp/.toolchain (ignored by git).
# Requires git, cmake, make and a C compiler. No system install is performed.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${DEST:-$HERE/../.toolchain}"
LOCK="$HERE/../toolchain.lock"
URL="$(sed -n 's/^url = //p' "$LOCK")"
COMMIT="$(sed -n 's/^commit = //p' "$LOCK")"

mkdir -p "$DEST"
if [ ! -d "$DEST/wla-dx/.git" ]; then
  git clone --filter=blob:none "$URL" "$DEST/wla-dx"
fi
git -C "$DEST/wla-dx" fetch --depth 1 origin "$COMMIT"
git -C "$DEST/wla-dx" checkout --detach "$COMMIT"
cmake -S "$DEST/wla-dx" -B "$DEST/wla-dx/build" -DCMAKE_BUILD_TYPE=Release
cmake --build "$DEST/wla-dx/build" -j"$(nproc)"

echo
echo "WLA_BIN=$DEST/wla-dx/build/binaries"
echo "export WLA_BIN=\"$DEST/wla-dx/build/binaries\""
