import React, { useState } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { X, Copy, Check, Eye, EyeOff, AlertTriangle } from 'lucide-react';

interface POSDeliveryModalProps {
  voucherCode: string;
  secretKey: string;
  onClose: () => void;
}

export const POSDeliveryModal: React.FC<POSDeliveryModalProps> = ({
  voucherCode,
  secretKey,
  onClose,
}) => {
  const [showSecretKey, setShowSecretKey] = useState(false);
  const [copiedVoucher, setCopiedVoucher] = useState(false);
  const [copiedSecret, setCopiedSecret] = useState(false);

  const qrPayload = JSON.stringify({
    endpoint: 'http://localhost:8080/v1/settle',
    voucher: voucherCode,
    key: secretKey,
  });

  const handleCopyVoucher = () => {
    navigator.clipboard.writeText(voucherCode);
    setCopiedVoucher(true);
    setTimeout(() => setCopiedVoucher(false), 2000);
  };

  const handleCopySecret = () => {
    navigator.clipboard.writeText(secretKey);
    setCopiedSecret(true);
    setTimeout(() => setCopiedSecret(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      {/* Background Radial Glow */}
      <div className="absolute w-96 h-96 bg-cyan-500/10 blur-3xl rounded-full pointer-events-none" />

      {/* Modal Container */}
      <div className="relative w-full max-w-lg backdrop-blur-xl bg-white/[0.03] border border-white/[0.08] rounded-2xl shadow-2xl p-6 sm:p-8 overflow-hidden">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/[0.05] transition-colors cursor-pointer"
          aria-label="Close modal"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header & Status */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center gap-2 mb-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <h2 className="text-xl font-bold tracking-wide text-emerald-400 font-sans">
              Verification Complete
            </h2>
          </div>
          <p className="text-sm text-slate-400 font-sans">
            Your transaction has been verified on-chain.
          </p>
        </div>

        {/* QR Code Section */}
        <div className="flex justify-center mb-6">
          <div className="bg-white p-4 rounded-xl shadow-lg">
            <QRCodeSVG
              value={qrPayload}
              size={180}
              level="H"
              includeMargin={false}
              className="rounded"
            />
          </div>
        </div>

        {/* Credentials Section */}
        <div className="space-y-4 mb-6">
          {/* Voucher Token Field */}
          <div>
            <label className="block text-xs font-mono uppercase tracking-wider text-slate-400 mb-1.5">
              X-VITAPROOF-VOUCHER
            </label>
            <div className="flex items-center justify-between gap-3 px-3.5 py-2.5 bg-black/50 border border-white/[0.08] rounded-lg">
              <span className="font-mono text-xs sm:text-sm text-cyan-400 truncate select-all">
                {voucherCode}
              </span>
              <button
                type="button"
                onClick={handleCopyVoucher}
                className="shrink-0 p-1.5 rounded text-slate-400 hover:text-white transition-colors cursor-pointer"
                title="Copy Voucher Code"
              >
                {copiedVoucher ? (
                  <Check className="w-4 h-4 text-emerald-400" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>

          {/* Secret Key Field */}
          <div>
            <label className="block text-xs font-mono uppercase tracking-wider text-slate-400 mb-1.5">
              X-VITAPROOF-KEY
            </label>
            <div className="flex items-center justify-between gap-3 px-3.5 py-2.5 bg-black/50 border border-white/[0.08] rounded-lg">
              <span className="font-mono text-xs sm:text-sm text-cyan-400 truncate select-all">
                {showSecretKey ? secretKey : '••••••••••••••••••••••••'}
              </span>
              <div className="flex items-center gap-1 shrink-0">
                <button
                  type="button"
                  onClick={() => setShowSecretKey(!showSecretKey)}
                  className="p-1.5 rounded text-slate-400 hover:text-white transition-colors cursor-pointer"
                  title={showSecretKey ? 'Hide Secret Key' : 'Reveal Secret Key'}
                >
                  {showSecretKey ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
                <button
                  type="button"
                  onClick={handleCopySecret}
                  className="p-1.5 rounded text-slate-400 hover:text-white transition-colors cursor-pointer"
                  title="Copy Secret Key"
                >
                  {copiedSecret ? (
                    <Check className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Security Warning Card */}
        <div className="flex items-start gap-3 p-3.5 bg-orange-500/10 border border-orange-500/20 rounded-xl text-orange-200">
          <AlertTriangle className="w-5 h-5 text-orange-400 shrink-0 mt-0.5" />
          <p className="text-xs leading-relaxed font-sans">
            Store your secret key securely. It is not saved on our servers and
            cannot be recovered if lost.
          </p>
        </div>
      </div>
    </div>
  );
};

export default POSDeliveryModal;
