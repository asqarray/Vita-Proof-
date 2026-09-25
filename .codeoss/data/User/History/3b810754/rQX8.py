import os
import ctypes
import logging
import uvicorn
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vitaproof-gateway")

app = FastAPI(title="VITAPROOF Gateway")

# 1. Define the Security Header
api_key_header = APIKeyHeader(name="X-License-Key", auto_error=True)

def verify_enterprise_license(api_key: str = Security(api_key_header)):
    # Hardcoded for beta - later this queries your DB or Solana voucher PDA
    valid_licenses = {"ENT-VITAPROOF-2026-ALPHA", "DEMO-LICENSE-001"}
    if api_key not in valid_licenses:
        logger.warning(f"Rejected unauthorized license attempt: {api_key}")
        raise HTTPException(status_code=403, detail="Invalid or Exhausted Enterprise License")
    return api_key

# (Keep your existing C-library loading logic here...)
try:
    core_lib = ctypes.CDLL("./vitaproof_core.so")
    core_lib.compute_collapse.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_double]
    core_lib.compute_collapse.restype = ctypes.c_double
    core_loaded = True
except Exception as e:
    core_loaded = False

class StateCollapseRequest(BaseModel):
    manifold_id: str
    phase_vector: List[float]
    entropy_threshold: float

@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "engine_loaded": core_loaded}

# 2. Inject the dependency into the route
@app.post("/opf/state-collapse")
def state_collapse(payload: StateCollapseRequest, license_key: str = Depends(verify_enterprise_license)):
    if not core_loaded:
        raise HTTPException(status_code=500, detail="Native AVX2 engine unavailable")

    length = len(payload.phase_vector)
    CArrayType = ctypes.c_double * length
    c_phase_vector = CArrayType(*payload.phase_vector)

    collapsed_value = core_lib.compute_collapse(c_phase_vector, length, payload.entropy_threshold)

    return {
        "status": "COLLAPSED_VIA_SIMD",
        "license_used": license_key,
        "manifold_id": payload.manifold_id,
        "final_entropy": collapsed_value
    }

port = int(os.environ.get("PORT", 8080))
if __name__ == "__main__":
    uvicorn.run("attest_daemon:app", host="0.0.0.0", port=port, log_level="info")