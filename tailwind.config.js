/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'neon-blue': '#00d4ff',
        'neon-red': '#ff3366',
        'gray-850': '#1a1d24',
      },
      backdropBlur: {
        xs: '2px',
      }
    },
  },
  plugins: [],
}