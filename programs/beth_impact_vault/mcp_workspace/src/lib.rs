use solana_program::{
    account_info::AccountInfo, entrypoint, entrypoint::ProgramResult, msg, pubkey::Pubkey,
};

// Declare the program entrypoint.
entrypoint!(process_instruction);

/// # Accounts
///
/// 1. `[signer]` The account paying for the transaction.
/// 2. `[]` The program-derived address (PDA) of the vault.
pub fn process_instruction(
    _program_id: &Pubkey,
    _accounts: &[AccountInfo],
    _instruction_data: &[u8],
) -> ProgramResult {
    msg!("Beth Impact Vault: process_instruction");
    Ok(())
}