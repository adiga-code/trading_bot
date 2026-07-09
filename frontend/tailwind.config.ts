import type { Config } from 'tailwindcss'

// Дизайн-токены из design brief: премиальный fintech, тёмная тема
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0B0E14',
        card: '#12161F',
        card2: '#1A2029',
        stroke: 'rgba(255,255,255,0.06)',
        gold: { DEFAULT: '#E8B44C', dim: '#B98E3A' },
        up: '#34D399',
        down: '#F87171',
        t1: '#F1F5F9',
        t2: '#94A3B8',
        t3: '#5B6472',
      },
      fontFamily: {
        display: ['Manrope', 'Inter', 'system-ui', 'sans-serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        card: '16px',
        el: '12px',
      },
    },
  },
  plugins: [],
} satisfies Config
