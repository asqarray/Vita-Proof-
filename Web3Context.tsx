// Inside your deposit / mint handler
async function handleDepositAndMint(amountSol: number) {
  try {
    setIsProcessing(true);

    // 1. Send SOL to Squads v4 Vault
    const transaction = new Transaction().add(
      SystemProgram.transfer({
        fromPubkey: wallet.publicKey,
        toPubkey: new PublicKey("E9qVvW3HuCHDasuFFvSA9JkhbUsfZQHX86rUXJrR1pRu"),
        lamports: amountSol * LAMPORTS_PER_SOL,
      })
    );

    const signature = await sendTransaction(transaction, connection);
    await connection.confirmTransaction(signature, "confirmed");

    // 2. Generate Credentials
    const generatedVoucher = `VOUCH-${Math.random().toString(36).substring(2, 6).toUpperCase()}-${Math.random().toString(36).substring(2, 5).toUpperCase()}`;
    const generatedSecretKey = `sk_live_${crypto.randomUUID()}`;

    // 3. Persist to PostgreSQL via API
    const res = await fetch("/api/vouchers/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        signature,
        voucherCode: generatedVoucher,
        secretKey: generatedSecretKey,
        amountSol,
        walletAddress: wallet.publicKey.toBase58(),
      }),
    });

    const data = await res.json();

    if (!res.ok) throw new Error(data.error);

    // 4. Trigger Delivery Modal
    setVoucherData({
      voucherCode: generatedVoucher,
      secretKey: generatedSecretKey,
    });
    setShowDeliveryModal(true);
  } catch (err) {
    console.error("Payment failed:", err);
  } finally {
    setIsProcessing(false);
  }
}
