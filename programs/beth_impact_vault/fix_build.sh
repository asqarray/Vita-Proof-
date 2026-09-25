#!/bin/bash
set -e

echo "Cleaning workspace..."
sudo rm -f Cargo.lock Cargo.toml

echo "Writing updated Cargo.toml..."
cat << 'TOML' > Cargo.toml
[package]
name = "beth_impact_vault"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib", "lib"]

[dependencies]
solana-program = "=1.18.17"
spl-token = { version = "=4.0.0", features = ["no-entrypoint"] }
TOML

echo "Generating strictly pinned Cargo.lock with serde 1.0.204..."
python3 -c '
pkgs = {
    "ahash": "0.8.11", "arrayref": "0.3.7", "base64": "0.21.7",
    "bincode": "1.3.3", "bitflags": "2.6.0", "blake3": "1.5.0",
    "block-buffer": "0.10.4", "borsh": "0.10.3", "borsh-derive": "0.10.3",
    "bs58": "0.4.0", "bv": "0.11.1", "bytemuck": "1.16.1",
    "bytemuck_derive": "1.7.0", "byteorder": "1.5.0", "cfg-if": "1.0.0",
    "console_error_panic_hook": "0.1.7", "constant_time_eq": "0.3.0",
    "cpufeatures": "0.2.12", "crypto-common": "0.1.6", "curve25519-dalek": "3.2.1",
    "digest": "0.10.7", "ed25519": "1.5.3", "either": "1.13.0",
    "generic-array": "0.14.7", "getrandom": "0.2.15",
    "hashbrown": "0.14.5", "hmac": "0.12.1", "indexmap": "2.2.6",
    "itertools": "0.10.5", "itoa": "1.0.11", "lazy_static": "1.4.0",
    "libc": "0.2.155", "lock_api": "0.4.12", "log": "0.4.21",
    "memchr": "2.7.4", "memoffset": "0.9.1", "num-derive": "0.3.3",
    "num-integer": "0.1.46", "num-traits": "0.2.19", "num_enum": "0.7.3",
    "num_enum_derive": "0.7.3", "once_cell": "1.19.0", "parking_lot": "0.12.3",
    "parking_lot_core": "0.9.10", "pbkdf2": "0.12.2", "percent-encoding": "2.3.1",
    "proc-macro-crate": "1.3.1", "proc-macro2": "1.0.86", "quote": "1.0.35",
    "rand": "0.8.5", "rand_chacha": "0.3.1", "rand_core": "0.6.4",
    "rustc_version": "0.4.0", "ryu": "1.0.18", "scopeguard": "1.2.0",
    "semver": "1.0.23", "serde": "1.0.204", "serde_bytes": "0.11.15",
    "serde_derive": "1.0.204", "serde_json": "1.0.120", "serde_with": "3.9.0",
    "sha2": "0.10.8", "sha3": "0.10.8", "signature": "1.6.4",
    "smallvec": "1.13.2", "solana-frozen-abi": "1.18.17",
    "solana-frozen-abi-macro": "1.18.17", "solana-program": "1.18.17",
    "solana-sdk-macro": "1.18.17", "solana-security-txt": "1.1.1",
    "spl-memo": "4.0.0", "spl-program-error": "0.4.0", "spl-token": "4.0.0",
    "spl-type-length-value": "0.4.0", "subtle": "2.5.0", "syn": "2.0.68",
    "thiserror": "1.0.61", "thiserror-impl": "1.0.61", "tiny-bip39": "1.0.0",
    "toml": "0.8.19", "toml_datetime": "0.6.8", "toml_edit": "0.22.20",
    "typenum": "1.17.0", "unicode-ident": "1.0.12", "wasm-bindgen": "0.2.92",
    "winnow": "0.5.40", "zeroize": "1.3.0", "zeroize_derive": "1.3.3"
}

deps = {
    "spl-token": ["arrayref", "bytemuck", "num-derive", "num-traits", "num_enum", "solana-program", "spl-memo", "spl-program-error", "spl-type-length-value", "thiserror"],
    "solana-program": ["bincode", "bs58", "bv", "bytemuck", "borsh", "lazy_static", "log", "num-derive", "num-traits", "rustc_version", "serde", "serde_derive", "serde_bytes", "solana-frozen-abi", "solana-frozen-abi-macro", "solana-sdk-macro", "thiserror"],
    "serde": ["serde_derive"]
}

lines = ["# Auto-generated lockfile for Rust 2021 SBF compatibility", "version = 3", ""]
lines.extend(["[[package]]", "name = \"beth_impact_vault\"", "version = \"0.1.0\"", "dependencies = [", " \"solana-program\",", " \"spl-token\",", "]", ""])

for name, ver in pkgs.items():
    lines.extend(["[[package]]", f"name = \"{name}\"", f"version = \"{ver}\"", "source = \"registry+https://github.com/rust-lang/crates.io-index\""])
    if name in deps:
        lines.append("dependencies = [")
        for d in deps[name]:
            lines.append(f" \"{d}\",")
        lines.append("]")
    lines.append("")

open("Cargo.lock", "w").write("\n".join(lines))
'

echo "Compiling SBF target in Docker..."
docker run --rm -v "$(pwd)":/workdir -w /workdir backpackapp/build:v0.30.1 bash -c "cargo build-sbf --offline"
