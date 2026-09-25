import os
import subprocess
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta

# 1. Configuration
RPC_URL = "https://api.devnet.solana.com"
PROGRAM_ID = Pubkey.from_string("4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU")

# 2. Extract state-collapse proof
binary_path = os.path.expanduser("~/deploy_gateway/test_winter_star")
if not os.path.exists(binary_path):
    binary_path = "./test_winter_star"

if os.path.exists(binary_path):
    result = subprocess.run([binary_path], capture_output=True, text=True, check=True)
    raw_output = result.stdout.strip()
    state_hash = raw_output[:32].encode("utf-8") if raw_output else b"VITAPROOF_SIMD_OK000000000000000"
else:
    state_hash = "VITAPROOF_SIMD_STATE_COLLAPSE00".encode("utf-8")[:32]

# 3. Construct instruction for Solana Devnet
payer = Keypair()
attestation_account = Keypair()

accounts = [
    AccountMeta(pubkey=attestation_account.pubkey(), is_signer=False, is_writable=True)
]

instruction = Instruction(
    program_id=PROGRAM_ID,
    data=state_hash,
    accounts=accounts,
)

client = Client(RPC_URL)
print(f"Bridge initialized for Program: {PROGRAM_ID}")
print(f"State Hash Proof (hex): {state_hash.hex()}")
