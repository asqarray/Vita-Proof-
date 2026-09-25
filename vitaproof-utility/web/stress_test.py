import asyncio
import time
import math
import random
import uuid
import httpx
import hashlib

GATEWAY_URL = "http://127.0.0.1:8080/ingest"
API_KEY = "vp_secure_dev_key_2026"
TOTAL_REQUESTS = 50
CONCURRENCY = 5

async def perform_heavy_enterprise_work(client: httpx.AsyncClient, semaphore: asyncio.Semaphore):
    async with semaphore:
        start_time = time.perf_counter()
        
        # --- HEAVY ENTERPRISE WORKLOAD ---
        # Simulating Observer Potential Framework hyperbolic tiling state collapse 
        # and high-dimensional vector grid projections over model parameters {54, 55}
        
        grid_dim = 64
        matrix_a = [[random.uniform(-1.0, 1.0) for _ in range(grid_dim)] for _ in range(grid_dim)]
        matrix_b = [[random.uniform(-1.0, 1.0) for _ in range(grid_dim)] for _ in range(grid_dim)]
        result_matrix = [[0.0 for _ in range(grid_dim)] for _ in range(grid_dim)]
        
        cpu_cycles_sim = 0
        accumulator = 0.0
        
        # Heavy matrix multiplication & hyperbolic transformation passes
        for iteration in range(15): # Multi-pass high-intensity compute
            for i in range(grid_dim):
                for j in range(grid_dim):
                    val = 0.0
                    for k in range(grid_dim):
                        val += matrix_a[i][k] * matrix_b[k][j]
                    
                    # Apply non-linear hyperbolic mapping ({54,55} space simulation)
                    hyp_val = math.sinh(val * 0.01) * math.cosh(val * 0.01)
                    result_matrix[i][j] = hyp_val
                    accumulator += hyp_val
                    cpu_cycles_sim += 128
            
            # Rotate state matrices for next pass
            matrix_a, matrix_b = matrix_b, result_matrix

        # Final cryptographic state collapse hash of the resulting matrix telemetry
        hasher = hashlib.sha256()
        for row in result_matrix:
            row_bytes = "".join(f"{val:.6f}" for val in row).encode("utf-8")
            hasher.update(row_bytes)
            
        state_hash_hex = hasher.hexdigest()
        cert_id = f"ESG-VP-ENT-{uuid.uuid4().hex[:8].upper()}"
        
        payload = {
            "cert_id": cert_id,
            "state_hash": state_hash_hex,
            "cpu_cycles": cpu_cycles_sim
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        }
        
        try:
            response = await client.post(GATEWAY_URL, json=payload, headers=headers, timeout=15.0)
            elapsed = time.perf_counter() - start_time
            return response.status_code, elapsed
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            return 0, elapsed

async def main():
    print(f"====================================================")
    print(f"Starting Enterprise Heavy-Duty Stress Test")
    print(f"Workload: Hyperbolic Tiling State-Collapse Matrix Passes")
    print(f"Requests: {TOTAL_REQUESTS} | Concurrency: {CONCURRENCY}")
    print(f"====================================================")
    
    semaphore = asyncio.Semaphore(CONCURRENCY)
    limits = httpx.Limits(max_keepalive_connections=CONCURRENCY, max_connections=CONCURRENCY)
    
    async with httpx.AsyncClient(limits=limits) as client:
        start_global = time.perf_counter()
        tasks = [perform_heavy_enterprise_work(client, semaphore) for _ in range(TOTAL_REQUESTS)]
        results = await asyncio.gather(*tasks)
        total_duration = time.perf_counter() - start_global

    status_codes = [r[0] for r in results]
    latencies = [r[1] for r in results]
    
    success_count = status_codes.count(200)
    failed_count = TOTAL_REQUESTS - success_count
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    max_latency = max(latencies) if latencies else 0
    min_latency = min(latencies) if latencies else 0
    rps = TOTAL_REQUESTS / total_duration if total_duration > 0 else 0

    print(f"\n--- ENTERPRISE STRESS TEST RESULTS ---")
    print(f"Total Duration      : {total_duration:.4f} seconds")
    print(f"Throughput          : {rps:.2f} requests/sec")
    print(f"Successful (200 OK) : {success_count}")
    print(f"Failed / Errors     : {failed_count}")
    print(f"Latency Avg         : {avg_latency*1000:.2f} ms")
    print(f"Latency Min         : {min_latency*1000:.2f} ms")
    print(f"Latency Max         : {max_latency*1000:.2f} ms")
    print(f"====================================================")

if __name__ == "__main__":
    asyncio.run(main())
