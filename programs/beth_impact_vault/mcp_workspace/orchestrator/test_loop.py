import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../servers')))
from workspace_server import read_manifest, run_cargo_build_sbf

def test_mcp_integration():
    print("Testing MCP Filesystem Tool (Reading Cargo.toml)...")
    cargo_path = "Cargo.toml"
    if os.path.exists(cargo_path):
        manifest_data = read_manifest(cargo_path)
        print(f"Manifest Read Success (length: {len(manifest_data)} chars)")
    else:
        print("Cargo.toml not found. Creating mock manifest...")
        with open("Cargo.toml", "w") as f:
            f.write("[package]\nname = \"beth_impact_vault\"\nversion = \"0.1.0\"\n")
        print("Mock Cargo.toml created.")

    print("Testing Docker Build Sandbox Tool (cargo build-sbf)...")
    build_result_json = run_cargo_build_sbf()
    result = json.loads(build_result_json)
    print(f"Build Sandbox Exit Code: {result.get('exit_code', 'unknown')}")
    print(f"Stdout Tail:\n{result.get('stdout', '')[-500:]}")
    print(f"Stderr Tail:\n{result.get('stderr', '')[-500:]}")

if __name__ == "__main__":
    test_mcp_integration()
