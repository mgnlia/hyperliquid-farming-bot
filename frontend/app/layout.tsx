import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "Hyperliquid Farming Bot",
  description: "SIMULATION_MODE dashboard for Hyperliquid HyperEVM airdrop farming",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
