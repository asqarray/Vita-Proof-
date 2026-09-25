import os
import sys
import json
import re
from google import genai
from google.genai import types

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../servers')))
from workspace_server import read_manifest, write_manifest, read_source_file, write_source_file, run_cargo_build_sbf

def run_autonomous_repair_loop():
    client = genai.Client(
        vertexai=True,
        project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
        location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    )
    
    system_instruction = (
        "You are the Master Supervisor Agent for the Project Winter Laminar Beth autonomous software system. "
        "Your objective is to fix Solana compilation failures. You can modify both Cargo.toml and src/lib.rs. "
        "Enforce a strict maximum of 5 retry loops."
    )

    project_context = """
    DESIRED OUTCOME:
    Successfully compile a Solana smart contract to an SBF (.so) binary using `cargo build-sbf`.
    
    ENVIRONMENT CONTEXT:
    - Build Container: `backpackapp/build:v0.30.1`
    - Target Architecture: Solana BPF/SBF
    
    REPAIR CAPABILITIES:
    - You can fix dependency/edition conflicts in Cargo.toml.
    - You can fix syntax, macro, or logic errors in src/lib.rs.
    
    OUTPUT FORMAT:
    If modifying Cargo.toml, output the full new content inside a ```toml code block.
    If modifying src/lib.rs, output the full new content inside a ```rust code block.
    You may output one or both depending on what needs fixing. Do not include extraneous text.
    """

    print("Initiating autonomous agentic compilation and repair loop (Code + Manifest)...")
    
    for attempt in range(1, 6):
        print(f"\n--- Retry Attempt {attempt} of 5 ---")
        
        build_output_json = run_cargo_build_sbf()
        result = json.loads(build_output_json)
        exit_code = result.get('exit_code', -1)
        stderr_tail = result.get('stderr', '')[-2500:]
        stdout_tail = result.get('stdout', '')[-1000:]
        
        if exit_code == 0:
            print("Build succeeded successfully! Valid Solana SBF binary generated.")
            return True
            
        print(f"Build failed (Exit {exit_code}). Gathering workspace context...")
        current_manifest = read_manifest("Cargo.toml")
        current_source = read_source_file("src/lib.rs")
        
        prompt = (
            f"{project_context}\n\n"
            f"CURRENT MANIFEST (Cargo.toml):\n```toml\n{current_manifest}\n```\n\n"
            f"CURRENT SOURCE (src/lib.rs):\n```rust\n{current_source}\n```\n\n"
            f"STDERR LOGS:\n{stderr_tail}\n\n"
            "Analyze the failure. Provide the complete, corrected code blocks for Cargo.toml and/or src/lib.rs as needed to fix the build."
        )
        
        print("Consulting Gemini 2.5 Pro for architectural and code repairs...")
        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0
            )
        )
        
        response_text = response.text.strip()
        
        # Parse output for targeted file updates
        cargo_match = re.search(r'```toml\n(.*?)\n```', response_text, re.DOTALL | re.IGNORECASE)
        rust_match = re.search(r'```rust\n(.*?)\n```', response_text, re.DOTALL | re.IGNORECASE)
        
        if not cargo_match and not rust_match:
            print("Agent failed to return valid code blocks. Trying again...")
            continue
            
        if cargo_match:
            print("Applying patched Cargo.toml...")
            write_manifest("Cargo.toml", cargo_match.group(1).strip())
            
        if rust_match:
            print("Applying patched src/lib.rs...")
            write_source_file("src/lib.rs", rust_match.group(1).strip())
        
    print("\nReached maximum retry limit (5). Manual intervention required.")
    return False

if __name__ == "__main__":
    run_autonomous_repair_loop()
