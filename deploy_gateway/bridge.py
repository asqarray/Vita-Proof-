import urllib.request
import struct
import json
from pathlib import Path
from solders.pubkey import Pubkey
from solders.instruction import Instruction
from solders.message import MessageV0
from solders.transaction import VersionedTransaction
from solders.keypair import Keypair
from solana.rpc.api import Client
from solana.rpc.types import TxOpts

GATEWAY_URL = "https://vitaproof-gateway-869469225283.us-central1.run.app/api/v1/verify"
PROGRAM_ID = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")
RPC_CLIENT = Client("https://api.devnet.solana.com")
KEYPAIR_PATH = Path.home() / ".config" / "solana" / "id.json"

def get_persistent_keypair():
    with open(KEYPAIR_PATH, "r") as f:
        secret_bytes = json.load(f)
    return Keypair.from_bytes(bytes(secret_bytes))

def fetch_proof():
    print("1. Fetching hardware proof from VITAPROOF Gateway...")
    floats = [0.001 * (i % 100) for i in range(10000)]
    raw_bytes = struct.pack(f"<{len(floats)}f", *floats)

    req = urllib.request.Request(
        GATEWAY_URL,
        data=raw_bytes,
        headers={
            "Content-Type": "application/octet-stream",
            "X-Client-Id": "solana_bridge_daemon"
        }
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def anchor_on_devnet():
    proof = fetch_proof()
    state_hash_hex = proof["state_hash_hex"]
    cert_id = proof["carbon_audit"]["esg_certificate_id"]
    cycles = proof["hardware_telemetry"]["measured_cpu_cycles"]

    # Structure telemetry payload as valid UTF-8 JSON for SPL Memo
    memo_payload = json.dumps({
        "vp_hash": state_hash_hex,
        "cert_id": cert_id,
        "cpu_cycles": cycles
    }, separators=(',', ':'))
    
    ix_data = memo_payload.encode("utf-8")

    payer = get_persistent_keypair()
    print(f"2. Bridge Keypair: {payer.pubkey()}")

    print("3. Fetching recent blockhash from Devnet...")
    recent_blockhash = RPC_CLIENT.get_latest_blockhash().value.blockhash

    print("4. Constructing & Signing Versioned Transaction...")
    ix = Instruction(
        program_id=PROGRAM_ID,
        accounts=[],
        data=ix_data
    )

    msg = MessageV0.try_compile(
        payer=payer.pubkey(),
        instructions=[ix],
        address_lookup_table_accounts=[],
        recent_blockhash=recent_blockhash
    )

    tx = VersionedTransaction(msg, [payer])

    print("5. Broadcasting transaction to Solana Devnet...")
    res = RPC_CLIENT.send_transaction(tx, opts=TxOpts(skip_preflight=False))
    tx_sig = str(res.value)

    print("\n================ ON-CHAIN ANCHOR SUCCESSFUL ================")
    print(f"Transaction Signature: {tx_sig}")
    print(f"Explorer URL:          https://solscan.io/tx/{tx_sig}?cluster=devnet")
    print(f"Program ID:            {PROGRAM_ID}")
    print(f"State Hash Hex:        {state_hash_hex}")
    print(f"ESG Certificate ID:    {cert_id}")
    print(f"Measured CPU Cycles:   {cycles}")

if __name__ == "__main__":
    anchor_on_devnet()
