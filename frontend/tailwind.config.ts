import type { Config } from 'tailwindcss'

// Дизайн-токены из design brief: премиальный fintech, тёмная тема
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#000000',
        card: '#15171C',
        // sheet keeps the previous card color, dedicated to bottom sheets/modals
        sheet: '#12161F',
        card2: '#1C1E24',
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
        card: '18px',
        row: '16px',
        hero: '22px',
        pill: '999px',
        stat: '14px',
        el: '12px',
      },
      backgroundImage: {
        'gold-cta': 'linear-gradient(180deg,#F3C868 0%,#E8B44C 55%,#D8A23A 100%)',
        'gold-hero': 'linear-gradient(180deg,#FFD76B 0%,#F2B742 100%)',
      },
    },
  },
  plugins: [],
} satisfies Config
