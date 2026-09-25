import os
import sys
from google import genai
from google.genai import types

def generate_project_report():
    client = genai.Client(
        vertexai=True,
        project=os.environ.get("GOOGLE_CLOUD_PROJECT"),
        location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    )
    
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    tree_output = []
    file_contents = {}
    target_files = ['Cargo.toml', 'orchestrator/agent_loop.py', 'servers/workspace_server.py', 'orchestrator/main.py']
    
    # 1. Map the directory structure and read target files
    for root, dirs, files in os.walk(workspace_dir):
        if '.git' in root or '__pycache__' in root:
            continue
        level = root.replace(workspace_dir, '').count(os.sep)
        indent = ' ' * 4 * level
        tree_output.append(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        
        for f in files:
            tree_output.append(f"{subindent}{f}")
            rel_path = os.path.relpath(os.path.join(root, f), workspace_dir)
            if rel_path in target_files:
                try:
                    with open(os.path.join(root, f), 'r') as file:
                        file_contents[rel_path] = file.read()
                except Exception:
                    pass
    
    tree_str = "\n".join(tree_output)
    
    # 2. Build the context payload
    prompt = f"Analyze the current state of the Project Winter Laminar Beth MCP workspace.\n\n"
    prompt += f"DIRECTORY STRUCTURE:\n{tree_str}\n\nKEY FILE CONTENTS:\n"
    
    for path, content in file_contents.items():
        prompt += f"\n--- {path} ---\n```python\n{content}\n```\n"
        
    prompt += (
        "\nGenerate a highly structured 'State of the Workspace' report. Include:\n"
        "1. **Architecture Overview:** Components built and their interactions.\n"
        "2. **Current Capabilities:** What the MCP servers and autonomous agents can currently execute.\n"
        "3. **Identified Blockers:** Current operational friction (e.g., Solana dependency mapping).\n"
        "4. **Next Logical Steps:** Prioritized technical actions to advance the system.\n\n"
        "Format using clean Markdown. Keep the tone technical, objective, and analytical."
    )
    
    print("Mapping workspace and generating architectural report via Gemini...")
    
    # 3. Generate the report
    response = client.models.generate_content(
        model='gemini-2.5-pro',
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.1)
    )
    
    report_text = response.text.strip()
    print("\n" + "="*60)
    print(report_text)
    print("="*60 + "\n")
    
    # Save the report locally
    report_path = os.path.join(workspace_dir, "PROJECT_REPORT.md")
    with open(report_path, "w") as f:
        f.write(report_text)
    print(f"Report saved locally to {report_path}")

if __name__ == "__main__":
    generate_project_report()
