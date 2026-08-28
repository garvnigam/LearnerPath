/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Source Serif 4', 'Georgia', 'Cambria', 'Times New Roman', 'serif'],
        display: ['EB Garamond', 'Georgia', 'Times New Roman', 'serif'],
      },
      animation: {
        'gradient': 'gradient 8s ease infinite',
        'float': 'float 6s ease-in-out infinite',
        'float-slow': 'float 10s ease-in-out infinite',
        'pulse-travel': 'pulse-travel 3.5s ease-in-out infinite',
        'edu-drift': 'edu-drift 16s ease-in-out infinite',
      },
      keyframes: {
        gradient: {
          '0%, 100%': { 'background-position': '0% 50%' },
          '50%': { 'background-position': '100% 50%' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        'pulse-travel': {
          '0%': { top: '0%', opacity: '0' },
          '8%': { opacity: '1' },
          '92%': { opacity: '1' },
          '100%': { top: '100%', opacity: '0' },
        },
        'edu-drift': {
          '0%': { transform: 'translate(0, 0) rotate(0deg)', opacity: '0' },
          '12%': { opacity: '1' },
          '50%': { transform: 'translate(var(--edu-dx, 24px), -48px) rotate(var(--edu-rot, 10deg))' },
          '88%': { opacity: '1' },
          '100%': { transform: 'translate(0, 0) rotate(0deg)', opacity: '0' },
        },
      }
    }
  },
  plugins: []
}
