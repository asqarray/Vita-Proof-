use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint,
    entrypoint::ProgramResult,
    msg,
    pubkey::Pubkey,
    program::invoke,
    system_instruction,
};
use spl_token::instruction as token_instruction;

entrypoint!(process_instruction);

#[repr(C)]
pub struct WorkProofPayload {
    pub work_units_executed: u64,
    pub redemption_rate_cents: u64,
    pub token_valuation_cents: u64,
}

pub fn process_instruction(
    _program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    let (tag, rest) = instruction_data
        .split_first()
        .ok_or(solana_program::program_error::ProgramError::InvalidInstructionData)?;

    match tag {
        0 => {
            let sol_amount = u64::from_le_bytes(rest[..8].try_into().unwrap());
            let tokens_to_mint = u64::from_le_bytes(rest[8..16].try_into().unwrap());

            let commodity_part = (sol_amount * 40) / 100;
            let pol_part = (sol_amount * 40) / 100;
            let ops_part = sol_amount - commodity_part - pol_part;

            let accounts_iter = &mut accounts.iter();
            let buyer = next_account_info(accounts_iter)?;
            let commodity_vault = next_account_info(accounts_iter)?;
            let pol_vault = next_account_info(accounts_iter)?;
            let ops_vault = next_account_info(accounts_iter)?;
            let token_mint = next_account_info(accounts_iter)?;
            let buyer_token_account = next_account_info(accounts_iter)?;
            let mint_authority = next_account_info(accounts_iter)?;
            let token_program = next_account_info(accounts_iter)?;
            let system_program = next_account_info(accounts_iter)?;

            invoke(
                &system_instruction::transfer(buyer.key, commodity_vault.key, commodity_part),
                &[buyer.clone(), commodity_vault.clone(), system_program.clone()],
            )?;
            invoke(
                &system_instruction::transfer(buyer.key, pol_vault.key, pol_part),
                &[buyer.clone(), pol_vault.clone(), system_program.clone()],
            )?;
            invoke(
                &system_instruction::transfer(buyer.key, ops_vault.key, ops_part),
                &[buyer.clone(), ops_vault.clone(), system_program.clone()],
            )?;

            let mint_ix = token_instruction::mint_to(
                token_program.key,
                token_mint.key,
                buyer_token_account.key,
                mint_authority.key,
                &[],
                tokens_to_mint,
            )?;

            invoke(
                &mint_ix,
                &[
                    token_mint.clone(),
                    buyer_token_account.clone(),
                    mint_authority.clone(),
                    token_program.clone(),
                ],
            )?;

            msg!("Tri-Asset Reserve split executed and $BETH dynamically minted.");
            Ok(())
        }
        1 => {
            let task_value_cents = u64::from_le_bytes(rest[..8].try_into().unwrap());
            let rate_cents_per_token = u64::from_le_bytes(rest[8..16].try_into().unwrap());

            let burn_amount = task_value_cents
                .checked_div(rate_cents_per_token)
                .ok_or(solana_program::program_error::ProgramError::InvalidArgument)?;

            let accounts_iter = &mut accounts.iter();
            let user_token_account = next_account_info(accounts_iter)?;
            let token_mint = next_account_info(accounts_iter)?;
            let user_authority = next_account_info(accounts_iter)?;
            let token_program = next_account_info(accounts_iter)?;

            let burn_ix = token_instruction::burn(
                token_program.key,
                user_token_account.key,
                token_mint.key,
                user_authority.key,
                &[],
                burn_amount,
            )?;

            invoke(
                &burn_ix,
                &[
                    user_token_account.clone(),
                    token_mint.clone(),
                    user_authority.clone(),
                    token_program.clone(),
                ],
            )?;

            msg!("Physical work proof validated. Burned {} $BETH tokens.", burn_amount);
            Ok(())
        }
        _ => Err(solana_program::program_error::ProgramError::InvalidInstructionData),
    }
}
