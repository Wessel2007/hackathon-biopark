/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Geist', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['Geist Mono', 'JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      colors: {
        /* Quiet Pro palette */
        ink:     { DEFAULT: '#0a0a0a', 2: '#1f1f1d' },
        paper:   '#f7f7f5',
        surface: '#ffffff',
        line:    { DEFAULT: '#eeede8', 2: '#dfdeda' },
        muted:   { DEFAULT: '#7c7c78', faint: '#a8a8a4' },
        lime:    { DEFAULT: '#d4ff3a', deep: '#7a9112', soft: '#f0fbd6' },
        /* Status accents */
        brand: {
          50:  '#f4f6ff',
          100: '#e8eaff',
          200: '#c8ceff',
          300: '#9ba6ff',
          400: '#6b7bff',
          500: '#3454ff',
          600: '#2a44d6',
          700: '#2236a8',
          800: '#1b2a82',
          900: '#171f5e',
          950: '#0a0a0a',
        },
        accent: {
          amber:  '#ff8a2a',
          red:    '#e3463a',
          green:  '#2a8a55',
          blue:   '#3454ff',
        },
      },
      boxShadow: {
        card:   '0 1px 2px rgba(10,10,10,0.04), 0 0 0 1px rgba(10,10,10,0.04)',
        pop:    '0 8px 24px -8px rgba(10,10,10,0.12), 0 2px 6px rgba(10,10,10,0.06)',
        ring:   '0 0 0 4px #d4ff3a40',
      },
    },
  },
  plugins: [],
}
