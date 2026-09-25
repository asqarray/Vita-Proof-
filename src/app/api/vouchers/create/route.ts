import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import crypto from "crypto";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { signature, voucherCode, secretKey, amount, currency = "SOL", walletAddress } = body;

    if (!signature || !voucherCode || !secretKey || !amount) {
      return NextResponse.json(
        { error: "Missing required fields" },
        { status: 400 }
      );
    }

    // Hash secret key for secure storage
    const secretKeyHash = crypto
      .createHash("sha256")
      .update(secretKey)
      .digest("hex");

    // Credit Rate:
    // 1 SOL = 10,000 Credits
    // 1 USDC = 100 Credits ($1.00 USD equivalent)
    const credits = currency === "USDC" 
      ? Math.floor(amount * 100) 
      : Math.floor(amount * 10000);

    // Calculate raw base units (Lamports for SOL [1e9], Micro-USDC [1e6])
    const rawUnits = currency === "USDC" 
      ? BigInt(Math.floor(amount * 1e6)) 
      : BigInt(Math.floor(amount * 1e9));

    // Persist transaction & voucher atomically
    const result = await prisma.$transaction(async (tx) => {
      let user = null;
      if (walletAddress) {
        user = await tx.user.upsert({
          where: { walletAddress },
          update: {},
          create: { walletAddress, role: "CLIENT" },
        });
      }

      const transactionRecord = await tx.transaction.create({
        data: {
          signature,
          amountLamports: rawUnits,
          type: "VOUCHER_PURCHASE",
          slot: 0,
          userId: user?.id,
        },
      });

      const voucherRecord = await tx.voucher.create({
        data: {
          voucherCode,
          secretKeyHash,
          initialBalance: credits,
          currentBalance: credits,
          status: "ACTIVE",
          userId: user?.id,
        },
      });

      return { transactionRecord, voucherRecord };
    });

    return NextResponse.json({
      success: true,
      voucherCode: result.voucherRecord.voucherCode,
      balance: result.voucherRecord.currentBalance,
      currency,
      signature: result.transactionRecord.signature,
    });
  } catch (error: any) {
    console.error("Voucher Creation Error:", error);
    return NextResponse.json(
      { error: error.message || "Failed to issue voucher" },
      { status: 500 }
    );
  }
}
