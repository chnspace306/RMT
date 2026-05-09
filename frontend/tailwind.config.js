/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        iosBlue: '#0A84FF',
        iosGreen: '#32D74B',
        iosRed: '#FF453A',
        iosOrange: '#FF9F0A',
      }
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
