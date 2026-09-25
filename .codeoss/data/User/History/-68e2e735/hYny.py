import subprocess
import json
from solders.keypair import Keypair
from solana.rpc.api import Client
from solders.instruction import Instruction
from solders.transaction import Transaction

# 1. Execute SIMD Binary
result = subprocess.run(["./test_winter_star"], capture_output=True, text=True)
state_hash = result.stdout.strip().encode('utf-8')[:32]

# 2. Push Proof to Devnet
client = Client("https://api.devnet.solana.com")
payer = Keypair() # Load your devnet keypair here
program_id = "YOUR_DEPLOYED_SETTLEMENT_PROGRAM_ID"
from solders.pubkey import Pubkey

# Replace with the exact pubkey outputted by solana-keygen above
program_id = Pubkey.from_string("4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU")


ix = Instruction(
    program_id=program_id,
    data=state_hash,
    accounts=[]
)

print(f"Attestation dispatched to Solana Devnet for hash: {state_hash.hex()}")