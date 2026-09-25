import { 
  Transaction, 
  SystemProgram, 
  PublicKey, 
  LAMPORTS_PER_SOL 
} from "@solana/web3.js";
import { 
  getAssociatedTokenAddress, 
  createTransferInstruction, 
  createAssociatedTokenAccountInstruction, 
  getAccount 
} from "@solana/spl-token";

// Devnet Constants
const VAULT_PUBKEY = new PublicKey("E9qVvW3HuCHDasuFFvSA9JkhbUsfZQHX86rUXJrR1pRu");
const DEVNET_USDC_MINT = new PublicKey("4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU");

async function handlePurchase(amount: number, currency: "SOL" | "USDC") {
  try {
    setIsProcessing(true);
    const transaction = new Transaction();

    if (currency === "SOL") {
      // 1A. SOL Transfer
      transaction.add(
        SystemProgram.transfer({
          fromPubkey: wallet.publicKey,
          toPubkey: VAULT_PUBKEY,
          lamports: amount * LAMPORTS_PER_SOL,
        })
      );
    } else {
      // 1B. USDC (SPL Token) Transfer
      const userAtA = await getAssociatedTokenAddress(DEVNET_USDC_MINT, wallet.publicKey);
      const vaultAtA = await getAssociatedTokenAddress(DEVNET_USDC_MINT, VAULT_PUBKEY);

      // Check if Vault's USDC Associated Token Account exists, create if missing
      try {
        await getAccount(connection, vaultAtA);
      } catch (e) {
        transaction.add(
          createAssociatedTokenAccountInstruction(
            wallet.publicKey, // Payer
            vaultAtA,         // Associated Token Account
            VAULT_PUBKEY,     // Owner
            DEVNET_USDC_MINT  // Token Mint
          )
        );
      }

      // Add 6-decimal USDC transfer instruction (1 USDC = 1,000,000 micro-USDC)
      const usdcAmount = Math.floor(amount * 1e6);
      transaction.add(
        createTransferInstruction(
          userAtA,
          vaultAtA,
          wallet.publicKey,
          usdcAmount
        )
      );
    }

    // 2. Send and Confirm Transaction
    const signature = await sendTransaction(transaction, connection);
    await connection.confirmTransaction(signature, "confirmed");

    // 3. Generate Credentials
    const generatedVoucher = `VOUCH-${Math.random().toString(36).substring(2, 6).toUpperCase()}-${Math.random().toString(36).substring(2, 5).toUpperCase()}`;
    const generatedSecretKey = `sk_live_${crypto.randomUUID()}`;

    // 4. Save to Database
    const res = await fetch("/api/vouchers/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        signature,
        voucherCode: generatedVoucher,
        secretKey: generatedSecretKey,
        amount,
        currency,
        walletAddress: wallet.publicKey.toBase58(),
      }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error);

    // 5. Display POS Delivery Modal
    setVoucherData({
      voucherCode: generatedVoucher,
      secretKey: generatedSecretKey,
    });
    setShowDeliveryModal(true);
  } catch (err: any) {
    console.error("Payment failed:", err);
  } finally {
    setIsProcessing(false);
  }
}