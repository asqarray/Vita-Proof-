import os
import json
import httpx
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.instruction import Instruction
from solders.message import Message
from solders.transaction import Transaction
from solana.rpc.api import Client

SERVICE_URL = os.getenv("SERVICE_URL", "https://vitaproof-gateway-869469225283.us-central1.run.app")
API_KEY = os.getenv("API_KEY", "vp_secure_dev_key_2026")
RPC_URL = "https://api.devnet.solana.com"
EXPECTED_PUBKEY = "CCMTpKqTGQDhRw9HmQ9paPVJ3yZad94t3pLpV2jYGkN2"
MEMO_PROGRAM_ID = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")

# Load Keypair
keypair_path = os.path.expanduser("~/.config/solana/id.json")
with open(keypair_path, "r") as f:
    secret_key = json.load(f)
payer = Keypair.from_bytes(bytes(secret_key))

print(f"[+] Loaded Solana Fee Payer: {payer.pubkey()}")

if str(payer.pubkey()) != EXPECTED_PUBKEY:
    print(f"[!] Warning: Loaded pubkey {payer.pubkey()} does not match target {EXPECTED_PUBKEY}")

# Fetch latest telemetry record from Cloud Run
headers = {"X-API-Key": API_KEY}
response = httpx.get(f"{SERVICE_URL}/records", headers=headers)
records = response.json()

if not records:
    print("[-] No records found to anchor.")
    exit(0)

latest = records[0]
memo_data = f"VITAPROOF|ID:{latest['id']}|CERT:{latest['cert_id']}|HASH:{latest['state_hash'][:16]}...".encode("utf-8")

print(f"[+] Anchoring Record #{latest['id']} ({latest['cert_id']})...")

# Construct Memo Instruction
memo_instruction = Instruction(
    program_id=MEMO_PROGRAM_ID,
    data=memo_data,
    accounts=[]
)

# Connect RPC & Fetch Recent Blockhash
solana_client = Client(RPC_URL)
recent_blockhash = solana_client.get_latest_blockhash().value.blockhash

# Sign & Send Transaction
msg = Message([memo_instruction], payer.pubkey())
tx = Transaction([payer], msg, recent_blockhash)

result = solana_client.send_transaction(tx)
tx_sig = result.value

print("\n====================================================")
print("  VITAPROOF STATE ANCHORED TO SOLANA DEVNET  ")
print("====================================================")
print(f"Record ID : {latest['id']}")
print(f"Cert ID   : {latest['cert_id']}")
print(f"Fee Payer : {payer.pubkey()}")
print(f"Tx Hash   : {tx_sig}")
print(f"Explorer  : https://explorer.solana.com/tx/{tx_sig}?cluster=devnet")
print("====================================================\n")
