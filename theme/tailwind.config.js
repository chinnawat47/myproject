/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./volunteer_app/templates/**/*.html",
    "./volunteer_app/static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#41A67E',      // สีเขียวหลัก
        darkBlue: '#05339C',     // สีน้ำเงินเข้ม
        blue: '#1055C9',         // สีน้ำเงิน
        gold: '#E5C95F',         // สีทอง
      },
    },
  },
  plugins: [],
}
