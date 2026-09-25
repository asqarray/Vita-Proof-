#!/usr/bin/env python3
"""
VITAPROOF /api/v1/verify stress-test & benchmark harness.

Two phases, run separately so you can review cost/behavior before escalating:

  PHASE 1 - SCALING SWEEP (cheap, sequential)
    Sends payloads of increasing size, several trials each, to build a real
    cycles-per-element curve instead of a single data point. This is what
    tells you whether cost scales linearly, and where (if anywhere) it stops.

  PHASE 2 - ADVERSARIAL + CONCURRENCY (more expensive - review Phase 1 first)
    - Edge-case payloads: all zeros, all identical value, extreme
      magnitudes, a single element, an empty array.
    - Concurrent load: N simultaneous requests of the same size, to see
      if latency/cycles degrade under contention (this is the part that
      actually stresses the deployed service, not just the algorithm).

Usage:
    python3 vitaproof_benchmark.py sweep
    python3 vitaproof_benchmark.py edge
    python3 vitaproof_benchmark.py concurrency --n 10 --size 100000
"""

import argparse
import json
import random
import statistics
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

ENDPOINT = "https://vitaproof-gateway-869469225283.us-central1.run.app/api/v1/verify"


def send(payload, client_id="benchmark", workload_type="avx2_state_collapse", timeout=60):
    body = json.dumps({
        "client_id": client_id,
        "workload_type": workload_type,
        "payload": payload,
    }).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT, data=body, headers={"Content-Type": "application/json"}
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            wall_time = time.perf_counter() - t0
            return json.loads(resp.read().decode("utf-8")), wall_time, None
    except urllib.error.HTTPError as e:
        wall_time = time.perf_counter() - t0
        return None, wall_time, f"HTTP {e.code}: {e.read().decode(errors='replace')}"
    except Exception as e:
        wall_time = time.perf_counter() - t0
        return None, wall_time, str(e)


def gen_payload(n, mode="random"):
    if mode == "random":
        return [round(random.uniform(0.0001, 1.0), 6) for _ in range(n)]
    if mode == "zeros":
        return [0.0] * n
    if mode == "identical":
        return [0.5] * n
    if mode == "extreme_small":
        return [1e-12] * n
    if mode == "extreme_large":
        return [1e12] * n
    if mode == "mixed_extreme":
        return [random.choice([1e-12, 1e12, 0.0, -1e12]) for _ in range(n)]
    raise ValueError(mode)


def phase_sweep(sizes, trials_per_size=3):
    print(f"{'size':>10} | {'trial':>5} | {'cycles':>12} | {'cyc/elem':>10} | "
          f"{'wall_s':>8} | {'hash_prefix':>12} | status")
    print("-" * 90)
    results = []
    for n in sizes:
        payload = gen_payload(n, "random")
        cycles_list = []
        for t in range(trials_per_size):
            data, wall, err = send(payload, client_id=f"sweep_{n}_{t}")
            if err:
                print(f"{n:>10} | {t:>5} | {'ERROR':>12} | {'-':>10} | {wall:>8.4f} | {'-':>12} | {err[:40]}")
                continue
            cycles = data.get("hardware_telemetry", {}).get("measured_cpu_cycles")
            h = data.get("state_hash_hex", "")[:10]
            cyc_per_elem = cycles / n if cycles else None
            cycles_list.append(cycles)
            print(f"{n:>10} | {t:>5} | {cycles:>12} | {cyc_per_elem:>10.4f} | "
                  f"{wall:>8.4f} | {h:>12} | {data.get('status')}")
        if cycles_list:
            results.append({
                "size": n,
                "mean_cycles": statistics.mean(cycles_list),
                "stdev_cycles": statistics.stdev(cycles_list) if len(cycles_list) > 1 else 0,
                "mean_cyc_per_elem": statistics.mean(cycles_list) / n,
            })
    print("\nSummary (mean cycles/element by size):")
    for r in results:
        print(f"  n={r['size']:>10}  mean_cyc/elem={r['mean_cyc_per_elem']:.5f}  "
              f"stdev={r['stdev_cycles']:.1f}")
    print("\nWhat to look for:")
    print("  - mean_cyc/elem roughly flat or smoothly decreasing -> linear-ish scaling (expected)")
    print("  - a sudden cliff at some size -> possible batching/shortcut in the kernel, worth asking about")
    print("  - stdev high relative to mean at same size -> data-dependent cost (explainable, but flag it)")


def phase_edge():
    modes = ["zeros", "identical", "extreme_small", "extreme_large", "mixed_extreme"]
    n = 10000
    print(f"Edge-case payloads at n={n}\n")
    for mode in modes:
        payload = gen_payload(n, mode)
        data, wall, err = send(payload, client_id=f"edge_{mode}", workload_type="avx2_state_collapse")
        if err:
            print(f"[{mode:>15}] ERROR: {err[:100]}")
            continue
        cycles = data.get("hardware_telemetry", {}).get("measured_cpu_cycles")
        h = data.get("state_hash_hex", "")[:16]
        print(f"[{mode:>15}] status={data.get('status'):>10}  cycles={cycles!s:>10}  "
              f"hash={h}  wall={wall:.4f}s")
    print("\nWhat to look for:")
    print("  - does status stay VERIFIED for degenerate input (all zeros, huge magnitudes)?")
    print("  - does the hash still change across these distinct payloads?")
    print("  - any silent clamping, NaN, or unhandled-exception behavior?")

    print("\nEmpty / malformed payload checks:")
    for label, bad in [("empty_array", []), ("single_element", [0.42])]:
        data, wall, err = send(bad, client_id=f"edge_{label}")
        if err:
            print(f"[{label}] returned error (may be correct/expected): {err[:120]}")
        else:
            print(f"[{label}] status={data.get('status')}  raw={json.dumps(data)[:200]}")


def phase_concurrency(n_requests, size):
    print(f"Concurrency test: {n_requests} simultaneous requests, payload size={size}")
    print("NOTE: this will spike Cloud Run instance count / cost. Start small (n=5-10).\n")
    payload = gen_payload(size, "random")

    def one_call(i):
        data, wall, err = send(payload, client_id=f"concurrent_{i}")
        return i, data, wall, err

    latencies = []
    errors = 0
    with ThreadPoolExecutor(max_workers=n_requests) as ex:
        futures = [ex.submit(one_call, i) for i in range(n_requests)]
        for fut in as_completed(futures):
            i, data, wall, err = fut.result()
            if err:
                errors += 1
                print(f"  req {i:>3}: ERROR {err[:80]}")
            else:
                latencies.append(wall)
                cycles = data.get("hardware_telemetry", {}).get("measured_cpu_cycles")
                print(f"  req {i:>3}: wall={wall:.4f}s  cycles={cycles}  status={data.get('status')}")

    if latencies:
        print(f"\nLatency under concurrency: mean={statistics.mean(latencies):.4f}s  "
              f"max={max(latencies):.4f}s  min={min(latencies):.4f}s  errors={errors}/{n_requests}")
    print("\nWhat to look for:")
    print("  - error rate under load (rate limiting, cold-start failures, timeouts)")
    print("  - latency degradation vs. the single-request baseline from your sweep")
    print("  - all hashes for identical concurrent payloads should match each other")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="phase", required=True)

    p_sweep = sub.add_parser("sweep")
    p_sweep.add_argument("--sizes", type=int, nargs="+",
                          default=[10, 100, 1000, 10000, 100000, 1000000])
    p_sweep.add_argument("--trials", type=int, default=3)

    sub.add_parser("edge")

    p_conc = sub.add_parser("concurrency")
    p_conc.add_argument("--n", type=int, default=5)
    p_conc.add_argument("--size", type=int, default=100000)

    args = parser.parse_args()

    if args.phase == "sweep":
        phase_sweep(args.sizes, args.trials)
    elif args.phase == "edge":
        phase_edge()
    elif args.phase == "concurrency":
        phase_concurrency(args.n, args.size)
