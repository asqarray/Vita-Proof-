#!/usr/bin/env bash
set -e

echo "=== Initializing Clean Build Environment ==="

# 1. Remap build homes to /tmp
export RUSTUP_HOME=/tmp/rustup
export CARGO_HOME=/tmp/cargo
export RUSTUP_OFFLINE=1

# 2. STRIP RUSTUP FROM PATH: Force cargo/rustc to look at raw system paths or direct binaries, 
# bypassing ~/.cargo/bin and rustup shims entirely.
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# 3. Ensure temporary directories exist
mkdir -p "$RUSTUP_HOME" "$CARGO_HOME"

echo "Current directory: $(pwd)"
echo "Active cargo path: $(which cargo || echo 'None in stripped path')"
echo "=== Environment Ready ==="
