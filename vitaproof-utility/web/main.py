import os
import time
import hmac
import hashlib
import sqlite3
from typing import Optional
from fastapi import FastAPI, Request, Header, HTTPException
from pydantic import BaseModel
from kms_signer import sign_state_hash

app = FastAPI(title="VITAPROOF Gateway")

HMAC_SECRET = os.environ.get("HMAC_SECRET", "vp_hmac_secret_2026").encode("utf-8")
API_KEY = os.environ.get("API_KEY", "vp_secure_dev_key_2026")
DB_PATH = "telemetry.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cert_id TEXT NOT NULL,
            state_hash TEXT NOT NULL,
            tx_signature TEXT,
            engine TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

class TelemetryPayload(BaseModel):
    cert_id: str
    state_hash: str
    cpu_cycles: Optional[int] = 0

async def verify_hmac_request(
    request: Request,
    x_api_key: Optional[str],
    x_timestamp: Optional[str],
    x_signature: Optional[str]
):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if not x_timestamp or not x_signature:
        raise HTTPException(status_code=401, detail="Missing HMAC authentication headers")

    try:
        ts = float(x_timestamp)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid X-Timestamp header format")

    if abs(time.time() - ts) > 300:
        raise HTTPException(status_code=401, detail="Request timestamp expired")

    body_bytes = await request.body()
    message = f"{x_timestamp}:".encode("utf-8") + body_bytes
    expected_sig = hmac.new(HMAC_SECRET, message, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_sig, x_signature):
        raise HTTPException(status_code=401, detail="Invalid HMAC payload signature")

@app.get("/")
def read_root():
    return {"status": "online", "service": "VITAPROOF Gateway"}

@app.post("/ingest")
async def ingest_telemetry(
    payload: TelemetryPayload,
    request: Request,
    x_api_key: Optional[str] = Header(None),
    x_timestamp: Optional[str] = Header(None),
    x_signature: Optional[str] = Header(None)
):
    await verify_hmac_request(request, x_api_key, x_timestamp, x_signature)

    try:
        raw_sig = sign_state_hash(payload.state_hash)
        kms_sig = raw_sig.hex() if isinstance(raw_sig, bytes) else str(raw_sig)
    except Exception as e:
        kms_sig = f"kms_error_{str(e)}"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO records (cert_id, state_hash, tx_signature, engine) VALUES (?, ?, ?, ?)",
        (payload.cert_id, payload.state_hash, kms_sig, "Python Fallback")
    )
    rec_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "status": "success",
        "engine": "Python Fallback",
        "record_id": rec_id,
        "cert_id": payload.cert_id,
        "state_hash": payload.state_hash,
        "tx_signature": kms_sig,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

@app.get("/records")
def get_records(x_api_key: Optional[str] = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, cert_id, state_hash, created_at FROM records ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()

    return [
        {"id": row[0], "cert_id": row[1], "state_hash": row[2], "created_at": row[3]}
        for row in rows
    ]

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
