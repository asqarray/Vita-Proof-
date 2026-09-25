import sys
import os

# Ensure the script can import the agent loop
sys.path.append(os.path.dirname(__file__))
from agent_loop import run_autonomous_repair_loop

def main():
    print("==================================================")
    print("Project Winter Laminar Beth - Supervisor Node")
    print("==================================================")
    print("Delegating task to Autonomous Repair Agent...")
    
    success = run_autonomous_repair_loop()
    
    if success:
        print("\n[SUPERVISOR] Workflow completed successfully. SBF contract is ready.")
    else:
        print("\n[SUPERVISOR] Workflow failed after max retries. System halting.")

if __name__ == "__main__":
    main()
