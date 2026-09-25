"use client";

import { useState } from "react";
import POSDeliveryModal from "../components/pos/POSDeliveryModal";

export default function Home() {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <main className="min-h-screen bg-[#090A0F] text-white flex flex-col items-center justify-center p-6">
      <button
        onClick={() => setIsOpen(true)}
        className="px-6 py-3 bg-gradient-to-r from-violet-600 to-cyan-500 rounded-xl font-medium shadow-lg hover:opacity-90 transition-opacity"
      >
        Open POS Voucher Modal
      </button>

      {isOpen && (
        <POSDeliveryModal
          voucherCode="VOUCH-7782-X92"
          secretKey="sk_live_550e8400-e29b-41d4-a716-446655440000"
          onClose={() => setIsOpen(false)}
        />
      )}
    </main>
  );
}
