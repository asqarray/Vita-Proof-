import os
import sys
import logging
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vitaproof-gateway")

app = FastAPI(title="VITAPROOF Gateway")

class StateCollapseRequest(BaseModel):
    manifold_id: str
    phase_vector: List[float]
    entropy_threshold: float

@app.get("/health")
def health_check():
    return {"status": "HEALTHY"}

@app.get("/")
def root():
    return {"service": "vitaproof-gateway", "status": "online"}

@app.post("/opf/state-collapse")
def state_collapse(payload: StateCollapseRequest):
    logger.info(f"Processing state collapse for manifold: {payload.manifold_id}")
    return {
        "status": "COLLAPSED",
        "manifold_id": payload.manifold_id,
        "phase_vector": payload.phase_vector,
        "entropy_threshold": payload.entropy_threshold
    }

port = int(os.environ.get("PORT", 8080))

if __name__ == "__main__":
    uvicorn.run("attest_daemon:app", host="0.0.0.0", port=port, log_level="info")