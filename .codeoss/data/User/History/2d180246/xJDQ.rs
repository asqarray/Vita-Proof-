use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint,
    entrypoint::ProgramResult,
    msg,
    pubkey::Pubkey,
};

entrypoint!(process_instruction);

pub fn process_instruction(
    _program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let accounts_iter = &mut accounts.iter();
    let attestation_account = next_account_info(accounts_iter)?;

    if instruction_data.len() < 32 {
        msg!("Error: Invalid proof payload length.");
        return Err(solana_program::program_error::ProgramError::InvalidInstructionData);
    }

    msg!("VITAPROOF State-Collapse Verification Received.");
    // Write the 32-byte hash directly to the attestation account state
    let mut data = attestation_account.try_borrow_mut_data()?;
    data[..32].copy_from_slice(&instruction_data[..32]);

    Ok(())
}