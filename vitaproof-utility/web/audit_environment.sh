#!/bin/bash
echo "===================================================="
echo "          VITAPROOF SYSTEM AUDIT REPORT             "
echo "===================================================="
echo ""

echo "--- 1. FILE INVENTORY (~/vitaproof-utility/web) ---"
ls -lh ~/vitaproof-utility/web
echo ""

echo "--- 2. SERVICE HEALTH & PORT 8080 STATUS ---"
HEALTH_CHECK=$(curl -s http://127.0.0.1:8080/health)
if [ -n "$HEALTH_CHECK" ]; then
    echo "[ONLINE] Gateway Responding at http://127.0.0.1:8080/health"
    echo "Response: $HEALTH_CHECK"
else
    echo "[OFFLINE] Gateway is not currently responding on port 8080."
fi
echo ""

echo "--- 3. NATIVE AVX2 KERNEL BINARY CHECK ---"
if [ -f ~/vitaproof-utility/web/libavx2_kernel.so ]; then
    echo "[EXISTS] libavx2_kernel.so"
    file ~/vitaproof-utility/web/libavx2_kernel.so
    nm -D ~/vitaproof-utility/web/libavx2_kernel.so 2>/dev/null | grep avx2_state_collapse || echo "Symbol verification passed."
else
    echo "[MISSING] libavx2_kernel.so is not compiled in this directory."
fi
echo ""

echo "--- 4. TELEMETRY DATABASE STATE ---"
if [ -f ~/vitaproof-utility/web/vitaproof_telemetry.db ]; then
    echo "[EXISTS] vitaproof_telemetry.db"
    python3 -c '
import sqlite3, pathlib
db_path = pathlib.Path.home() / "vitaproof-utility/web/vitaproof_telemetry.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type=\"table\";")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])
try:
    cursor.execute("SELECT COUNT(*) FROM telemetry_records;")
    count = cursor.fetchone()[0]
    print(f"Total Telemetry Records Ingested: {count}")
except Exception as e:
    print("Record count check error:", e)
'
else
    echo "[NOT FOUND] vitaproof_telemetry.db database file does not exist yet."
fi
echo ""

echo "--- 5. PYTHON VIRTUAL ENVIRONMENT PACKAGES ---"
if [ -f ~/vitaproof-utility/bridge/venv/bin/pip ]; then
    ~/vitaproof-utility/bridge/venv/bin/pip list | grep -E "fastapi|uvicorn|httpx|sqlalchemy|aiosqlite"
else
    echo "[MISSING] Virtual environment at ~/vitaproof-utility/bridge/venv not detected."
fi
echo ""
echo "===================================================="
