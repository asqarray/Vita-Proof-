import os
import sys
import json
import re
from datetime import datetime
from google import genai
from google.genai import types

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../servers')))
from workspace_server import read_manifest, write_manifest, read_source_file, write_source_file, run_cargo_build_sbf

SON_STATE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../son_network_state.json'))

def initialize_son_network():
    state = {
        "network_id": "beth-son-alpha-1",
        "status": "SELF_CONFIGURING",
        "nodes": {
            "discovery_agent": {"role": "Eyes", "status": "active"},
            "destruction_agent": {"role": "Hands", "status": "active"},
            "mcp_build_plane": {"role": "Execution Sandbox", "status": "active"}
        },
        "telemetry": [],
        "optimization_history": []
    }
    with open(SON_STATE_PATH, 'w') as f:
        json.dump(state, f, indent=2)
    return state

def update_son_state(update_data):
    if os.path.exists(SON_STATE_PATH):
        with open(SON_STATE_PATH, 'r') as f:
            state = json.load(f)
    else:
        state = initialize_son_network()
        
    state["telemetry"].append(update_data)
    with open(SON_STATE_PATH, 'w') as f:
        json.dump(state, f, indent=2)

def son_self_healing_loop(max_retries=5):
    client = genai.Client(
        vertexai=True,
        project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
        location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    )
    
    state = initialize_son_network()
    state["status"] = "SELF_OPTIMIZING"
    
    print("==================================================")
    print("Project Winter Laminar Beth - Self-Organizing Network")
    print("==================================================")
    
    for attempt in range(1, max_retries + 1):
        print(f"\n[SON CONTROL PLANE] Loop Cycle {attempt}/{max_retries}")
        
        build_output_json = run_cargo_build_sbf()
        result = json.loads(build_output_json)
        exit_code = result.get('exit_code', -1)
        stderr = result.get('stderr', '')
        stdout = result.get('stdout', '')
        
        if exit_code == 0:
            print("[SON] Fault cleared. Network achieved convergence (Target SBF compiled).")
            update_son_state({"attempt": attempt, "event": "CONVERGENCE_SUCCESS", "exit_code": 0})
            return True
            
        print("[SON] Fault detected. Deploying Discovery Agent (Eyes)...")
        error_lines = [line for line in stderr.splitlines() if "error" in line.lower() or "caused by" in line.lower()]
        fault_signature = error_lines[:5] if error_lines else ["Unknown compilation error"]
        
        current_manifest = read_manifest("Cargo.toml")
        
        print("[SON] Deploying Destruction Agent (Hands) for topology mutation...")
        system_instruction = (
            "You are the Destruction Agent within a Self-Organizing Network (SON). "
            "Your objective is self-healing: resolve compilation errors by mutating Cargo.toml or src/lib.rs. "
            "Review previous network telemetry to avoid repeating failed states."
        )
        
        prompt = (
            f"NETWORK TELEMETRY HISTORY:\n{json.dumps(state['telemetry'], indent=2)}\n\n"
            f"CURRENT FAULT SIGNATURE (Attempt {attempt}):\n{fault_signature}\n\n"
            f"STDERR TAIL:\n{stderr[-1500:]}\n\n"
            f"CURRENT MANIFEST:\n```toml\n{current_manifest}\n```\n\n"
            "Provide the complete, corrected Cargo.toml (inside ```toml ... ```) and/or src/lib.rs "
            "that optimizes the node configuration to bypass this specific fault."
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0
            )
        )
        
        response_text = response.text.strip()
        cargo_match = re.search(r'```toml\n(.*?)\n```', response_text, re.DOTALL | re.IGNORECASE)
        rust_match = re.search(r'```rust\n(.*?)\n```', response_text, re.DOTALL | re.IGNORECASE)
        
        mutated = False
        if cargo_match:
            write_manifest("Cargo.toml", cargo_match.group(1).strip())
            mutated = True
            print("[SON] Cargo.toml topology mutated.")
            
        if rust_match:
            write_source_file("src/lib.rs", rust_match.group(1).strip())
            mutated = True
            print("[SON] src/lib.rs topology mutated.")
            
        update_son_state({
            "attempt": attempt,
            "fault_signature": fault_signature,
            "manifest_snapshot": current_manifest,
            "mutation_applied": mutated
        })
        
    print("\n[SON] Max retries reached. Network failed to converge autonomously.")
    state["status"] = "CONVERGENCE_FAILURE"
    return False

if __name__ == "__main__":
    son_self_healing_loop()
