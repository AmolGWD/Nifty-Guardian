import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],

  server: {
    proxy: {
      "/signal": {
        target: "https://vigilant-xylophone-xxpw4jj75r2q5p-8000.app.github.dev",
        changeOrigin: true,
        secure: true,
      },
    },
  },
});