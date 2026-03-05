/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./app/**/*.{js,ts,jsx,tsx}', './components/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        hl: {
          bg: '#0a0e1a',
          card: '#111827',
          border: '#1f2937',
          text: '#e5e7eb',
          muted: '#6b7280',
          green: '#00d4a0',
          red: '#ef4444',
          blue: '#3b82f6',
          yellow: '#f59e0b',
          purple: '#8b5cf6',
        },
      },
    },
  },
  plugins: [],
}
