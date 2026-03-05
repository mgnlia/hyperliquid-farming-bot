import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'hype-green': '#00ff88',
        'hype-blue': '#0088ff',
        'hype-purple': '#8800ff',
        'hype-dark': '#0a0a0f',
        'hype-card': '#12121a',
        'hype-border': '#1e1e2e',
      }
    },
  },
  plugins: [],
}
export default config
