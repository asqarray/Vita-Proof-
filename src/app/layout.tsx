import React from "react";

export const metadata = {
  title: "VITAPROOF Gateway",
  description: "Web3 Settlement Gateway POS Terminal",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <script src="https://cdn.tailwindcss.com"></script>
      </head>
      <body className="bg-[#090A0F] text-white antialiased">{children}</body>
    </html>
  );
}
