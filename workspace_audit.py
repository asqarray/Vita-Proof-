import os
from pathlib import Path

home = Path.home()
ignore_dirs = {".cache", ".local", ".cargo", ".rustup", ".config", ".docker", ".avm", ".codeoss", ".gemini", ".vscode"}

print(f"{'DIRECTORY / FILE':<40} {'SIZE (MB)':<10}")
print("=" * 52)

for item in sorted(home.iterdir()):
    if item.name in ignore_dirs:
        continue
    if item.is_dir():
        try:
            total_bytes = sum(f.stat().st_size for f in item.rglob('*') if f.is_file() and not any(part in ignore_dirs for part in f.parts))
            size_mb = total_bytes / (1024 * 1024)
            print(f"📁 {item.name:<38} {size_mb:>8.2f} MB")
            
            # Print immediate sub-files for context
            for sub in sorted(item.iterdir()):
                if sub.is_file():
                    sub_size = sub.stat().st_size / 1024
                    print(f"   ├── 📄 {sub.name:<32} {sub_size:>6.1f} KB")
        except PermissionError:
            continue
    elif item.is_file():
        size_kb = item.stat().st_size / 1024
        print(f"📄 {item.name:<38} {size_kb:>8.1f} KB")

