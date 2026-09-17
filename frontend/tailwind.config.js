/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        command: {
          950: '#090d16',
          900: '#0f172a',
          850: '#131c31',
          800: '#1e293b',
          700: '#334155',
          border: 'rgba(255, 255, 255, 0.08)'
        },
        water: {
          light: '#38bdf8',
          DEFAULT: '#0ea5e9',
          deep: '#0284c7',
          dark: '#0369a1'
        },
        hazard: {
          low: '#22c55e',
          medium: '#eab308',
          high: '#f97316',
          severe: '#ef4444'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['Fira Code', 'JetBrains Mono', 'monospace']
      }
    }
  },
  plugins: []
};
