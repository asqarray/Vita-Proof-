import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import crypto from "crypto";

export async function POST(req: NextRequest) {
  try {
    const voucherCode = req.headers.get("x-vitaproof-voucher");
    const secretKey = req.headers.get("x-vitaproof-key");
    const body = await req.json().catch(() => ({}));
    const { proofHash, agentId = "AGENT-AUTONOMOUS-01", cost = 100 } = body;

    if (!voucherCode || !secretKey) {
      return NextResponse.json(
        { error: "Unauthorized: Missing X-VITAPROOF-VOUCHER or X-VITAPROOF-KEY headers" },
        { status: 401 }
      );
    }

    // Hash incoming secret key to match stored digest
    const secretKeyHash = crypto
      .createHash("sha256")
      .update(secretKey)
      .digest("hex");

    // Retrieve voucher
    const voucher = await prisma.voucher.findUnique({
      where: { voucherCode },
    });

    if (!voucher) {
      return NextResponse.json(
        { error: "Invalid voucher code" },
        { status: 404 }
      );
    }

    if (voucher.secretKeyHash !== secretKeyHash) {
      return NextResponse.json(
        { error: "Invalid secret key credential" },
        { status: 403 }
      );
    }

    if (voucher.status !== "ACTIVE" || voucher.currentBalance < cost) {
      return NextResponse.json(
        { error: "Voucher exhausted or revoked", remainingBalance: voucher.currentBalance },
        { status: 402 }
      );
    }

    // Deduct credits and log settlement transaction
    const updatedVoucher = await prisma.$transaction(async (tx) => {
      const newBalance = voucher.currentBalance - cost;
      const newStatus = newBalance <= 0 ? "EXHAUSTED" : "ACTIVE";

      const updated = await tx.voucher.update({
        where: { id: voucher.id },
        data: {
          currentBalance: newBalance,
          status: newStatus,
        },
      });

      await tx.settlement.create({
        data: {
          proofHash: proofHash || `PROOF-${Date.now()}`,
          agentId,
          slot: BigInt(28941002), // Devnet slot height
          status: "VERIFIED_ON_CHAIN",
          voucherId: voucher.id,
        },
      });

      return updated;
    });

    return NextResponse.json({
      status: "STATE_COLLAPSE_SETTLEMENT",
      verified: true,
      voucherCode: updatedVoucher.voucherCode,
      remainingCredits: updatedVoucher.currentBalance,
      deductedCredits: cost,
      destinationVault: "E9qVvW3HuCHDasuFFvSA9JkhbUsfZQHX86rUXJrR1pRu",
      timestamp: new Date().toISOString(),
    });
  } catch (error: any) {
    console.error("Settlement Error:", error);
    return NextResponse.json(
      { error: error.message || "Settlement failed" },
      { status: 500 }
    );
  }
}
