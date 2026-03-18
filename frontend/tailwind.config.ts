import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/lib/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        ink: "#0d1b1e",
        canvas: "#f4efe6",
        accent: "#0f766e",
        ember: "#c2410c",
        sand: "#e7d9bc"
      }
    }
  },
  plugins: []
};

export default config;
