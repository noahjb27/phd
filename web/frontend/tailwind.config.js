// tailwind.config.js
module.exports = {
  content: [
    './src/pages/**/*.{js,jsx,ts,tsx}', // Adjust if using TypeScript
    './src/components/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      animation: {
        'fade-in': 'fadeIn 0.6s ease-in',
        'fade-in-delayed': 'fadeIn 0.6s ease-in 0.3s forwards',
        'fade-in-delayed-more': 'fadeIn 0.6s ease-in 0.6s forwards',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        }
      },
      colors: {
        primary: '#1a73e8', // Custom color for buttons and highlights
        secondary: '#fbbc05', // Accent color for branding
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  variants: {
    extend: {},
  },
  plugins: [require('@tailwindcss/typography')],
};
