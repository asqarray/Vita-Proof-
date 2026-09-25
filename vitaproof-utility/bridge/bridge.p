import os
import json
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
from solders.message import Message
from solders.transaction import Transaction

RPC_URL = "https://api.devnet.solana.com"
SQUADS_V4_PROGRAM_ID = Pubkey.from_string("SQDS426qNu2A3C1tfRd4230ad3c3s9eef49e8")
MEMO_PROGRAM_ID = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqpGDLGmfcHr")

def anchor_telemetry_payload(cert_id: str, state_hash: str, cpu_cycles: int):
    client = Client(RPC_URL)
    keypair_path = os.path.expanduser("~/.config/solana/id.json")
    
    if not os.path.exists(keypair_path):
        print(f"Error: Wallet keypair not found at {keypair_path}")
        return None

    with open(keypair_path, "r") as f:
        secret = json.load(f)
    payer = Keypair.from_bytes(bytes(secret))

    payload = {
        "cert_id": cert_id,
        "vp_hash": state_hash,
        "cpu_cycles": cpu_cycles,
        "governance": "Squads_v4_Multisig_PDA"
    }

    memo_bytes = json.dumps(payload).encode("utf-8")
    memo_ix = Instruction(
        program_id=MEMO_PROGRAM_ID,
        data=memo_bytes,
        accounts=[AccountMeta(pubkey=payer.pubkey(), is_signer=True, is_writable=False)]
    )

    recent_blockhash = client.get_latest_blockhash().value.blockhash
    msg = Message.new_with_blockhash([memo_ix], payer.pubkey(), recent_blockhash)
    tx = Transaction([payer], msg, recent_blockhash)

    result = client.send_transaction(tx)
    print("===================================================")
    print("Transaction Anchored Successfully!")
    print(f"Signature: {result.value}")
    print("===================================================")
    return str(result.value)

if __name__ == "__main__":
    anchor_telemetry_payload(
        "ESG-VP-C7746A18", 
        "c7746a183faf1bbe3fe87b3999be671dd8d827a56049a142dd4806e6bba18453", 
        341016
    )
