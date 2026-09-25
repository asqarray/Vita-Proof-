import os
import subprocess
import json
from fastmcp import FastMCP

mcp = FastMCP("workspace_server")

# Anchor paths to the true project root (one level above 'servers/')
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

@mcp.tool()
def read_manifest(file_path: str = "Cargo.toml") -> str:
    """Reads the Cargo.toml manifest file."""
    full_path = os.path.join(PROJECT_ROOT, file_path)
    try:
        with open(full_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading manifest: {str(e)}"

@mcp.tool()
def write_manifest(file_path: str, content: str) -> str:
    """Writes updated content to Cargo.toml."""
    full_path = os.path.join(PROJECT_ROOT, file_path)
    try:
        with open(full_path, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing manifest: {str(e)}"

@mcp.tool()
def read_source_file(file_path: str) -> str:
    """Reads a Rust source file (e.g., src/lib.rs) from the workspace."""
    full_path = os.path.join(PROJECT_ROOT, file_path)
    try:
        with open(full_path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
def write_source_file(file_path: str, content: str) -> str:
    """Writes updated Rust source code back to the file system."""
    full_path = os.path.join(PROJECT_ROOT, file_path)
    try:
        with open(full_path, 'w') as f:
            f.write(content)
        return f"Successfully updated {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@mcp.tool()
def run_cargo_build_sbf() -> str:
    """Executes cargo build-sbf inside the backpackapp/build:v0.30.1 Docker container."""
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{PROJECT_ROOT}:/workdir",
        "-w", "/workdir",
        "backpackapp/build:v0.30.1",
        "cargo", "build-sbf"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        output = {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        return json.dumps(output)
    except subprocess.TimeoutExpired:
        return json.dumps({"exit_code": -1, "stdout": "", "stderr": "Build timed out after 120 seconds."})
    except Exception as e:
        return json.dumps({"exit_code": -1, "stdout": "", "stderr": str(e)})

if __name__ == "__main__":
    mcp.run()
