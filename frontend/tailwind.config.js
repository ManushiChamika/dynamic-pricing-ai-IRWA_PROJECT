/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      sans: ['Inter', 'sans-serif'],
    },
  },
  darkMode: "class", // Enables class-based dark mode
  plugins: [],
}
