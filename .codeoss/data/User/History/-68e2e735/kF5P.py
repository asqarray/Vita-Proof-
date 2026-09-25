import subprocess
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta

# 1. Configuration
RPC_URL = "https://api.devnet.solana.com"
# Replace with the output from: solana-keygen pubkey target/deploy/vitaproof_settlement-keypair.json
PROGRAM_ID = Pubkey.from_string("4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU")

# 2. Execute C SIMD Binary to extract state-collapse proof
result = subprocess.run(["./test_winter_star"], capture_output=True, text=True, check=True)
state_hash = result.stdout.strip().encode("utf-8")[:32]

# 3. Construct instruction for Solana Devnet
payer = Keypair()  # Load your keypair here
attestation_account = Keypair()  # Target state account

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