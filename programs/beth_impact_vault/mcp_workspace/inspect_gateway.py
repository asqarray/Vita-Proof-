import os

root_dir = os.path.expanduser("~/vitaproof-gateway")
print(f"=== INSPECTING VITAPROOF GATEWAY AT: {root_dir} ===")

for sub in ["services", "infrastructure", "core"]:
    path = os.path.join(root_dir, sub)
    if os.path.exists(path):
        print(f"\n[{sub.upper()}] contents:")
        for item in os.listdir(path):
            print(f"  - {item}")

print("\n=== CORE C EXTENSION & BUILD STATE ===")
so_path = os.path.join(root_dir, "vitaproof_core.so")
if os.path.exists(so_path):
    print(f"vitaproof_core.so size: {os.path.getsize(so_path)} bytes")

print("\n=== KEY ROOT PYTHON SCRIPTS ===")
for f in ["attest_daemon.py", "payment_manager.py", "solana_provider.py"]:
    f_path = os.path.join(root_dir, f)
    if os.path.exists(f_path):
        print(f"  - {f} (present)")
