import os
import sys
import logging
import uvicorn
from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vitaproof-gateway")

app = FastAPI(title="VITAPROOF Gateway")

@app.get("/health")
def health_check():
    return {"status": "HEALTHY"}

@app.get("/")
def root():
    return {"service": "vitaproof-gateway", "status": "online"}

# Bind to PORT provided by Cloud Run, defaulting to 8080
port = int(os.environ.get("PORT", 8080))
logger.info(f"Starting uvicorn server on 0.0.0.0:{port}")

if __name__ == "__main__":
    uvicorn.run("attest_daemon:app", host="0.0.0.0", port=port, log_level="info")