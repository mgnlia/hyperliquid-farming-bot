import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        hype: {
          dark: '#0a0a0f',
          card: '#12121a',
          border: '#242438',
          green: '#00d395',
          blue: '#00a3ff',
          purple: '#9b7bff',
        },
      },
    },
  },
  plugins: [],
}

export default config
