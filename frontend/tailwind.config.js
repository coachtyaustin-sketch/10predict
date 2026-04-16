/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'strong-buy': '#16a34a',
        'buy': '#22c55e',
        'hold': '#6b7280',
        'sell': '#ef4444',
        'strong-sell': '#dc2626',
      },
    },
  },
  plugins: [],
}
