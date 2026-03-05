import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Hyperliquid Farming Bot',
  description: 'HyperEVM Airdrop Farming Dashboard — $HYPE Season 3',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-hype-dark">{children}</body>
    </html>
  )
}
