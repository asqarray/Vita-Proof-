import os
import ctypes
import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vitaproof-gateway")

app = FastAPI(title="VITAPROOF Gateway")

# 1. Load the native C library compiled by Docker
try:
    core_lib = ctypes.CDLL("./vitaproof_core.so")
    # Define the C function signature: double compute_collapse(double*, int, double)
    core_lib.compute_collapse.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_double]
    core_lib.compute_collapse.restype = ctypes.c_double
    core_loaded = True
    logger.info("Successfully loaded vitaproof_core.so AVX2 engine")
except Exception as e:
    logger.error(f"Failed to load native engine: {e}")
    core_loaded = False

class StateCollapseRequest(BaseModel):
    manifold_id: str
    phase_vector: List[float]
    entropy_threshold: float

@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "engine_loaded": core_loaded}

@app.post("/opf/state-collapse")
def state_collapse(payload: StateCollapseRequest):
    if not core_loaded:
        raise HTTPException(status_code=500, detail="Native AVX2 engine unavailable")

    # 2. Convert Python list to C-compatible double array
    length = len(payload.phase_vector)
    CArrayType = ctypes.c_double * length
    c_phase_vector = CArrayType(*payload.phase_vector)

    # 3. Call the native C function
    collapsed_value = core_lib.compute_collapse(
        c_phase_vector, 
        length, 
        payload.entropy_threshold
    )

    return {
        "status": "COLLAPSED_VIA_SIMD",
        "manifold_id": payload.manifold_id,
        "final_entropy": collapsed_value
    }

port = int(os.environ.get("PORT", 8080))

if __name__ == "__main__":
    uvicorn.run("attest_daemon:app", host="0.0.0.0", port=port, log_level="info")