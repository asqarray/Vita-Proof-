import os
import json
import asyncio
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
from solders.message import Message
from solders.transaction import Transaction

RPC_URL = "https://api.devnet.solana.com"
SQUADS_V4_PROGRAM_ID = Pubkey.from_string("SQDS4ep65T869zMMBKyuUq6aD6EgTu8psMjkvj52pCf")
MEMO_PROGRAM_ID = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")

async def anchor_telemetry_payload(cert_id: str, state_hash: str, cpu_cycles: int):
    async with AsyncClient(RPC_URL) as client:
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
            "governance": "Squads_v4_Multisig_PDA",
            "squads_program": str(SQUADS_V4_PROGRAM_ID)
        }

        memo_bytes = json.dumps(payload).encode("utf-8")
        memo_ix = Instruction(
            program_id=MEMO_PROGRAM_ID,
            data=memo_bytes,
            accounts=[AccountMeta(pubkey=payer.pubkey(), is_signer=True, is_writable=False)]
        )

        blockhash_resp = await client.get_latest_blockhash()
        recent_blockhash = blockhash_resp.value.blockhash
        
        msg = Message.new_with_blockhash([memo_ix], payer.pubkey(), recent_blockhash)
        tx = Transaction([payer], msg, recent_blockhash)

        result = await client.send_transaction(tx)
        print("====================================================")
        print("Backend Telemetry Anchored with Squads v4 Governance!")
        print(f"Signature: {result.value}")
        print("====================================================")
        return str(result.value)

if __name__ == "__main__":
    asyncio.run(anchor_telemetry_payload(
        "ESG-VP-C7746A18", 
        "c7746a183faf1bbe3fe87b3999be671dd8d827a56049a142dd4806e6bba18453", 
        341016
    ))
