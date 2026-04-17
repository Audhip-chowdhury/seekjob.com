/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#003580",
        accent: "#F5A200",
        surface: "#F4F6F9",
        ink: "#1A1A2E",
      },
    },
  },
  plugins: [],
};
