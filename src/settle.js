const { getRedisClient } = require('./lib/redis');

async function handleSettlement(req, res) {
  const voucherCode = req.headers['x-vitaproof-voucher'];
  const secretKey = req.headers['x-vitaproof-key'];
  const { proofHash, cost = 100 } = req.body;

  try {
    const redis = await getRedisClient();
    
    // 1. Fetch voucher state from Redis cache (Sub-millisecond lookup)
    const voucherKey = `voucher:${voucherCode}`;
    const voucherData = await redis.hGetAll(voucherKey);

    if (!voucherData || Object.keys(voucherData).length === 0) {
      return res.status(401).json({ error: "Invalid or expired voucher" });
    }

    if (voucherData.status !== "ACTIVE") {
      return res.status(403).json({ error: "Voucher is exhausted or revoked" });
    }

    const currentBalance = parseInt(voucherData.balance, 10);
    if (currentBalance < cost) {
      return res.status(402).json({ error: "Insufficient balance for state collapse" });
    }

    // 2. Atomic Balance Deduction in Redis
    const newBalance = await redis.hIncrBy(voucherKey, "balance", -cost);

    // 3. Process your on-chain Solana / Squads v4 verification here...
    return res.json({
      success: true,
      network: "solana-devnet",
      action: "STATE_COLLAPSE_SETTLEMENT",
      proofHash,
      costDeducted: cost,
      remainingBalance: newBalance,
      latencyMode: "in-memory-redis-cached",
      timestamp: new Date().toISOString(),
    });

  } catch (err) {
    console.error("Settlement error:", err);
    return res.status(500).json({ error: "Internal gateway settlement failure" });
  }
}

module.exports = { handleSettlement };
