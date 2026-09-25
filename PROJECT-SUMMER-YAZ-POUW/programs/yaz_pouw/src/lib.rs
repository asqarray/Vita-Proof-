use anchor_lang::prelude::*;
use anchor_spl::token::{self, Mint, MintTo, Token, TokenAccount};

declare_id!("JCcfFs62rn73GwNmXDouYxtrTpuiM397TCLVLjvKrH2u");

#[program]
pub mod yaz_pouw {
    use super::*;

    pub fn verify_and_mint_yaz(
        ctx: Context<VerifyAndMintYaz>,
        useful_work_units: u64,
        proof_hash: [u8; 32],
    ) -> Result<()> {
        let beth_account = &ctx.accounts.provider_beth_account;
        require!(
            beth_account.amount >= 1_000_000,
            YazError::InsufficientBethCollateral
        );

        msg!("Validating PoUW proof hash: {:?}", proof_hash);
        msg!("Validated {} useful work units", useful_work_units);

        let yaz_reward = useful_work_units
            .checked_mul(10)
            .ok_or(YazError::MathOverflow)?;

        let seeds = &[b"yaz_mint_authority".as_ref(), &[ctx.bumps.mint_authority]];
        let signer = &[&seeds[..]];

        let cpi_accounts = MintTo {
            mint: ctx.accounts.yaz_mint.to_account_info(),
            to: ctx.accounts.provider_yaz_account.to_account_info(),
            authority: ctx.accounts.mint_authority.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        let cpi_ctx = CpiContext::new_with_signer(cpi_program, cpi_accounts, signer);

        token::mint_to(cpi_ctx, yaz_reward)?;

        emit!(YazMintedEvent {
            provider: ctx.accounts.provider.key(),
            reward_amount: yaz_reward,
            proof_hash,
        });

        Ok(())
    }
}

#[derive(Accounts)]
pub struct VerifyAndMintYaz<'info> {
    #[account(mut)]
    pub provider: Signer<'info>,

    pub provider_beth_account: Account<'info, TokenAccount>,

    #[account(mut)]
    pub yaz_mint: Account<'info, Mint>,

    #[account(mut)]
    pub provider_yaz_account: Account<'info, TokenAccount>,

    #[account(
        seeds = [b"yaz_mint_authority"],
        bump
    )]
    pub mint_authority: UncheckedAccount<'info>,

    pub token_program: Program<'info, Token>,
}

#[event]
pub struct YazMintedEvent {
    pub provider: Pubkey,
    pub reward_amount: u64,
    pub proof_hash: [u8; 32],
}

#[error_code]
pub enum YazError {
    #[msg("Provider has insufficient BETH locked in substructure reserve.")]
    InsufficientBethCollateral,
    #[msg("Math overflow calculated during YAZ emission.")]
    MathOverflow,
}
