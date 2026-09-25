use anchor_lang::prelude::*;
use anchor_spl::token::{self, Mint, Token, TokenAccount, Transfer};

declare_id!("9ujspCNYmJH68J1pGPhwbGRgxQg5fdWSDW2WzbwMs7QL");

#[program]
pub mod beth_impact_vault {
    use super::*;

    /// Initialize a corporate vesting vault with programmatic time locks
    pub fn create_vesting_account(
        ctx: Context<CreateVestingAccount>,
        total_amount: u64,
        start_time: i64,
        end_time: i64,
    ) -> Result<()> {
        // SECURITY FIX: Prevent Division by Zero & invalid timelines
        require!(end_time > start_time, VaultError::InvalidSchedule);
        require!(total_amount > 0, VaultError::ZeroAmount);

        let vesting_account = &mut ctx.accounts.vesting_account;
        vesting_account.beneficiary = ctx.accounts.beneficiary.key();
        vesting_account.mint = ctx.accounts.mint.key();
        vesting_account.total_amount = total_amount;
        vesting_account.released_amount = 0;
        vesting_account.start_time = start_time;
        vesting_account.end_time = end_time;
        vesting_account.bump = ctx.bumps.vesting_account;

        // Transfer BETH tokens from Treasury Issuer to Program Vault
        let cpi_accounts = Transfer {
            from: ctx.accounts.issuer_token_account.to_account_info(),
            to: ctx.accounts.vault_token_account.to_account_info(),
            authority: ctx.accounts.issuer.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        let cpi_ctx = CpiContext::new(cpi_program, cpi_accounts);
        token::transfer(cpi_ctx, total_amount)?;

        msg!("Vesting vault initialized for: {:?}", vesting_account.beneficiary);
        Ok(())
    }

    /// Claim unlocked BETH tokens based on linear time decay
    pub fn claim_unlocked_tokens(ctx: Context<ClaimTokens>) -> Result<()> {
        let vesting_account = &mut ctx.accounts.vesting_account;
        let clock = Clock::get()?;
        let current_time = clock.unix_timestamp;

        require!(current_time >= vesting_account.start_time, VaultError::VestingNotStarted);

        let time_passed = current_time.saturating_sub(vesting_account.start_time);
        let total_duration = vesting_account.end_time.saturating_sub(vesting_account.start_time);

        // Calculate linear vested entitlement
        let vested_amount = if current_time >= vesting_account.end_time {
            vesting_account.total_amount
        } else {
            (vesting_account.total_amount as u128)
                .checked_mul(time_passed as u128)
                .unwrap()
                .checked_div(total_duration as u128)
                .unwrap() as u64
        };

        let claimable = vested_amount.saturating_sub(vesting_account.released_amount);
        require!(claimable > 0, VaultError::NoTokensToClaim);

        // Update state before transferring to prevent Re-entrancy attacks
        vesting_account.released_amount = vesting_account.released_amount.checked_add(claimable).unwrap();

        // PDA signing seeds for automated vault transfer
        let mint_key = vesting_account.mint;
        let beneficiary_key = vesting_account.beneficiary;
        let bump = vesting_account.bump;
        let signer_seeds: &[&[&[u8]]] = &[&[
            b"vesting",
            beneficiary_key.as_ref(),
            mint_key.as_ref(),
            &[bump],
        ]];

        let cpi_accounts = Transfer {
            from: ctx.accounts.vault_token_account.to_account_info(),
            to: ctx.accounts.beneficiary_token_account.to_account_info(),
            authority: vesting_account.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        let cpi_ctx = CpiContext::new_with_signer(cpi_program, cpi_accounts, signer_seeds);
        token::transfer(cpi_ctx, claimable)?;

        msg!("Claimed {} base units of BETH.", claimable);
        Ok(())
    }
}

#[derive(Accounts)]
pub struct CreateVestingAccount<'info> {
    #[account(mut)]
    pub issuer: Signer<'info>,
    /// CHECK: Beneficiary public key (safe because we only use it as a passive pubkey for seeds/storage)
    pub beneficiary: AccountInfo<'info>,
    pub mint: Account<'info, Mint>,
    #[account(
        init,
        payer = issuer,
        space = 8 + 32 + 32 + 8 + 8 + 8 + 8 + 1,
        seeds = [b"vesting", beneficiary.key().as_ref(), mint.key().as_ref()],
        bump
    )]
    pub vesting_account: Account<'info, VestingAccount>,
    #[account(
        mut,
        constraint = issuer_token_account.owner == issuer.key(),
        constraint = issuer_token_account.mint == mint.key()
    )]
    pub issuer_token_account: Account<'info, TokenAccount>,
    
    // SECURITY FIX: Changed init_if_needed to init. 
    // This enforces vault isolation and fixes your Anchor compilation errors.
    #[account(
        init,
        payer = issuer,
        token::mint = mint,
        token::authority = vesting_account
    )]
    pub vault_token_account: Account<'info, TokenAccount>,
    
    pub system_program: Program<'info, System>,
    pub token_program: Program<'info, Token>,
    pub rent: Sysvar<'info, Rent>,
}

#[derive(Accounts)]
pub struct ClaimTokens<'info> {
    #[account(mut)]
    pub beneficiary: Signer<'info>,
    #[account(
        mut,
        seeds = [b"vesting", beneficiary.key().as_ref(), vesting_account.mint.as_ref()],
        bump = vesting_account.bump,
        has_one = beneficiary
    )]
    pub vesting_account: Account<'info, VestingAccount>,
    #[account(
        mut,
        constraint = vault_token_account.owner == vesting_account.key()
    )]
    pub vault_token_account: Account<'info, TokenAccount>,
    #[account(
        mut,
        constraint = beneficiary_token_account.owner == beneficiary.key()
    )]
    pub beneficiary_token_account: Account<'info, TokenAccount>,
    pub token_program: Program<'info, Token>,
}

#[account]
pub struct VestingAccount {
    pub beneficiary: Pubkey,
    pub mint: Pubkey,
    pub total_amount: u64,
    pub released_amount: u64,
    pub start_time: i64,
    pub end_time: i64,
    pub bump: u8,
}

#[error_code]
pub enum VaultError {
    #[msg("Vesting schedule has not commenced yet.")]
    VestingNotStarted,
    #[msg("No unlocked BETH tokens available for claim at this timestamp.")]
    NoTokensToClaim,
    #[msg("End time must be strictly greater than start time.")]
    InvalidSchedule,
    #[msg("Total vesting amount must be greater than zero.")]
    ZeroAmount,
}