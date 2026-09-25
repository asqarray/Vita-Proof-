import time
import json
import hmac
import hashlib
import os
import requests

GATEWAY_URL = "https://vitaproof-gateway-869469225283.us-central1.run.app/ingest"
API_KEY = os.environ.get("API_KEY", "vp_secure_dev_key_2026")
HMAC_SECRET = os.environ.get("HMAC_SECRET", "vp_hmac_secret_2026").encode("utf-8")

def run_daemon():
    print("====================================================")
    print("   VITAPROOF CLIENT TELEMETRY DAEMON (HMAC-AUTH)   ")
    print(f"   Target Gateway: {GATEWAY_URL}")
    print("====================================================")
    
    counter = 1
    while True:
        payload = {
            "cert_id": f"CLIENT-DAEMON-NODE-{counter:04d}",
            "state_hash": hashlib.sha256(f"state_{time.time()}_{counter}".encode("utf-8")).hexdigest(),
            "cpu_cycles": 850000 + (counter * 10)
        }
        
        body_bytes = json.dumps(payload).encode("utf-8")
        timestamp = str(time.time())
        message = f"{timestamp}:".encode("utf-8") + body_bytes
        signature = hmac.new(HMAC_SECRET, message, hashlib.sha256).hexdigest()
        
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY,
            "X-Timestamp": timestamp,
            "X-Signature": signature
        }
        
        try:
            res = requests.post(GATEWAY_URL, data=body_bytes, headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                print(f"[{time.strftime("%H:%M:%S")}] TELEMETRY ANCHORED | Cert: {payload["cert_id"]} | ID: {data.get("record_id")} | KMS Sig: {data.get("tx_signature")[:16]}...")
            else:
                print(f"[{time.strftime("%H:%M:%S")}] REJECTED ({res.status_code}): {res.text}")
        except Exception as e:
            print(f"[{time.strftime("%H:%M:%S")}] ERROR: {str(e)}")
            
        counter += 1
        time.sleep(10)

if __name__ == "__main__":
    run_daemon()
