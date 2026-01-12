/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#0A84FF',
        dark: {
          100: '#1c1c1e',
          200: '#222222',
          300: '#333333',
          400: '#444444',
          500: '#666666',
          900: '#000000'
        }
      },
      maxWidth: {
        'mobile': '430px'
      }
    },
  },
  plugins: [],
}
