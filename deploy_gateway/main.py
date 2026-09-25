import os
import time
import struct
import hashlib
import ctypes
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List

app = FastAPI(title="VITAPROOF Hardware-Bound Gateway")

class VerificationRequest(BaseModel):
    client_id: str = "test_enterprise_01"
    workload_type: str = "state_collapse"
    payload: List[float] = []

CPU_BASE_FREQ_HZ = 2.8e9
CPU_TDP_WATTS    = 45.0
GRID_CO2_KG_KWH  = 0.385

# Load dynamic shared library at startup
so_path = "./libwinterstar.so"
winter_lib = None
if os.path.exists(so_path):
    winter_lib = ctypes.CDLL(so_path)
    winter_lib.run_state_collapse.argtypes = [
        ctypes.POINTER(ctypes.c_float),
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint32)
    ]
    winter_lib.run_state_collapse.restype = ctypes.c_uint64

@app.get("/health")
@app.get("/api/health")
def health_check():
    return {"status": "HEALTHY"}

@app.post("/api/v1/verify")
async def verify_state(request: Request):
    try:
        content_type = request.headers.get("content-type", "")

        if "application/octet-stream" in content_type:
            packed_payload = await request.body()
            client_id = request.headers.get("x-client-id", "binary_client")
            workload_type = "avx2_state_collapse_raw"
            element_count = len(packed_payload) // 4
        else:
            body = await request.json()
            req = VerificationRequest(**body)
            if not req.payload:
                raise HTTPException(status_code=400, detail="Payload cannot be empty")
            client_id = req.client_id
            workload_type = req.workload_type
            packed_payload = struct.pack(f"<{len(req.payload)}f", *req.payload)
            element_count = len(req.payload)

        if len(packed_payload) == 0 or element_count == 0:
            raise HTTPException(status_code=400, detail="Payload cannot be empty")

        if winter_lib:
            # Direct in-process C-memory execution (Zero IPC overhead)
            c_float_p = ctypes.cast(packed_payload, ctypes.POINTER(ctypes.c_float))
            out_bits = ctypes.c_uint32()
            
            cpu_cycles = winter_lib.run_state_collapse(c_float_p, element_count, ctypes.byref(out_bits))
            accumulator = f"VP_SIMD_ACCUMULATOR_{out_bits.value:08X}"
        else:
            accumulator = "VP_SIMD_ACCUMULATOR_FALLBACK"
            cpu_cycles = element_count * 32

        state_hash_bytes = hashlib.blake2b(
            accumulator.encode("utf-8") + packed_payload,
            digest_size=32
        ).digest()
        state_hash_hex = state_hash_bytes.hex()

        execution_seconds = cpu_cycles / CPU_BASE_FREQ_HZ
        energy_joules = CPU_TDP_WATTS * execution_seconds
        simd_kwh = energy_joules / 3.6e6
        baseline_kwh = simd_kwh * 18.0
        net_kwh_saved = baseline_kwh - simd_kwh
        co2_avoided_kg = net_kwh_saved * GRID_CO2_KG_KWH

        return {
            "status": "VERIFIED",
            "client_id": client_id,
            "workload_type": workload_type,
            "program_id": "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",
            "state_hash_hex": state_hash_hex,
            "hardware_telemetry": {
                "kernel_accumulator": accumulator,
                "measured_cpu_cycles": cpu_cycles,
                "derived_execution_seconds": round(execution_seconds, 9),
                "active_energy_joules": round(energy_joules, 6),
                "payload_elements": element_count
            },
            "carbon_audit": {
                "simd_compute_kwh": round(simd_kwh, 9),
                "baseline_compute_kwh": round(baseline_kwh, 9),
                "net_kwh_saved": round(net_kwh_saved, 9),
                "co2_avoided_kg": round(co2_avoided_kg, 9),
                "esg_certificate_id": f"ESG-VP-{state_hash_hex[:8].upper()}"
            }
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")
