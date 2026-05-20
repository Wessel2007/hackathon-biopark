/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#ebf8ff',
          100: '#bee3f8',
          500: '#3182ce',
          700: '#2b6cb0',
          900: '#1a365d',
        },
      },
    },
  },
  plugins: [],
}
