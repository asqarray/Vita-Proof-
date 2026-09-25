use anchor_lang::prelude::*;
use anchor_spl::token::{self, Mint, Token, TokenAccount, Transfer};

declare_id!("Vitaproof111111111111111111111111111111111111");

#[program]
pub mod vitaproof_settlement {
    use super::*;

    /// Initialize the 40% USDC Escrow Vault PDA for an enterprise license
    pub fn initialize_escrow(
        ctx: Context<InitializeEscrow>,
        _license_id: String,
    ) -> Result<()> {
        let escrow_account = &mut ctx.accounts.escrow_account;
        escrow_account.authority = ctx.accounts.authority.key();
        escrow_account.usdc_vault = ctx.accounts.usdc_vault.key();
        escrow_account.total_locked = 0;
        escrow_account.is_active = true;
        msg!("VITAPROOF IAS 7 Escrow Vault Initialized.");
        Ok(())
    }

    /// Deposit 40% USDC service refund reserve into the PDA vault
    pub fn deposit_escrow(
        ctx: Context<DepositEscrow>,
        amount_usdc: u64,
        reseller_fee_usdc: u64,
    ) -> Result<()> {
        // 1. Transfer 40% USDC reserve into the Escrow Vault PDA
        let cpi_accounts = Transfer {
            from: ctx.accounts.payer_usdc.to_account_info(),
            to: ctx.accounts.usdc_vault.to_account_info(),
            authority: ctx.accounts.payer.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        token::transfer(CpiContext::new(cpi_program, cpi_accounts), amount_usdc)?;

        // 2. Transfer Reseller Commission Fee directly to the affiliate
        if reseller_fee_usdc > 0 {
            let reseller_cpi = Transfer {
                from: ctx.accounts.payer_usdc.to_account_info(),
                to: ctx.accounts.reseller_usdc.to_account_info(),
                authority: ctx.accounts.payer.to_account_info(),
            };
            token::transfer(CpiContext::new(ctx.accounts.token_program.to_account_info(), reseller_cpi), reseller_fee_usdc)?;
        }

        let escrow_account = &mut ctx.accounts.escrow_account;
        escrow_account.total_locked += amount_usdc;

        msg!("Locked {} micro-USDC into IAS 7 Escrow Vault.", amount_usdc);
        Ok(())
    }
}

#[derive(Accounts)]
#[instruction(license_id: String)]
pub struct InitializeEscrow<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + 32 + 32 + 8 + 1,
        seeds = [b"escrow", license_id.as_bytes()],
        bump
    )]
    pub escrow_account: Account<'info, EscrowAccount>,
    #[account(
        init,
        payer = authority,
        token::mint = usdc_mint,
        token::authority = escrow_account,
        seeds = [b"vault", license_id.as_bytes()],
        bump
    )]
    pub usdc_vault: Account<'info, TokenAccount>,
    pub usdc_mint: Account<'info, Mint>,
    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
    pub token_program: Program<'info, Token>,
    pub rent: Sysvar<'info, Rent>,
}

#[derive(Accounts)]
pub struct DepositEscrow<'info> {
    #[account(mut)]
    pub escrow_account: Account<'info, EscrowAccount>,
    #[account(mut)]
    pub usdc_vault: Account<'info, TokenAccount>,
    #[account(mut)]
    pub payer_usdc: Account<'info, TokenAccount>,
    #[account(mut)]
    pub reseller_usdc: Account<'info, TokenAccount>,
    pub payer: Signer<'info>,
    pub token_program: Program<'info, Token>,
}

#[account]
pub struct EscrowAccount {
    pub authority: Pubkey,
    pub usdc_vault: Pubkey,
    pub total_locked: u64,
    pub is_active: bool,
}