import os
import struct
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta

# 1. Configuration
RPC_URL = "https://api.devnet.solana.com"
PROGRAM_ID = Pubkey.from_string("4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU")
SQUADS_MPROGRAM = Pubkey.from_string("SQDS426qXa2A8H8BR23ABy5zt225w3fW8LA9Q5L78fG")

def derive_capex_reserved_pda(client_pubkey: Pubkey, lease_years: int):
    """Derives a locked Squads Sub-Vault PDA for CapEx capital allowance claims."""
    seeds = [
        b"reserved_compute_slot",
        bytes(client_pubkey),
        struct.pack("<H", lease_years)  # 2-byte integer for lease term
    ]
    pda, bump = Pubkey.find_program_address(seeds, PROGRAM_ID)
    return pda, bump

def build_vault_instruction(client_keypair: Keypair, mode: str = "opex", lease_years: int = 1):
    """
    Constructs the on-chain allocation instruction:
    - mode="opex": Immediate utility voucher redemption to Squads Treasury Vault.
    - mode="capex": Lockup in dedicated Reserved Compute Slot PDA.
    """
    if mode == "capex":
        pda, bump = derive_capex_reserved_pda(client_keypair.pubkey(), lease_years)
        print(f"[CapEx Mode] Dedicated Reserved Compute Vault PDA: {pda} (Term: {lease_years} Yr)")
        
        # Discriminator 1 = CapEx Vault Lock
        data = bytes([1]) + struct.pack("<H", lease_years) + bytes([bump])
        accounts = [
            AccountMeta(pubkey=pda, is_signer=False, is_writable=True),
            AccountMeta(pubkey=client_keypair.pubkey(), is_signer=True, is_writable=True),
        ]
    else:
        print("[OpEx Mode] Instant Utility Voucher Settlement to Treasury Vault")
        # Discriminator 0 = OpEx Voucher Redemption
        data = bytes([0])
        accounts = [
            AccountMeta(pubkey=client_keypair.pubkey(), is_signer=True, is_writable=True),
        ]

    return Instruction(program_id=PROGRAM_ID, data=data, accounts=accounts)

if __name__ == "__main__":
    client = Client(RPC_URL)
    dummy_client = Keypair()

    print("--- 1. Testing OpEx Voucher Allocation ---")
    opex_ix = build_vault_instruction(dummy_client, mode="opex")
    
    print("
--- 2. Testing CapEx Reserved Compute Lease (3-Year) ---")
    capex_ix = build_vault_instruction(dummy_client, mode="capex", lease_years=3)

    print("
Vault Allocator initialized successfully.")
