import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/api/process": {
        target: "https://disabilityai-223088873408.us-central1.run.app",
        changeOrigin: true,
        secure: true,
        // Cloud Run serves POST / ; local app still calls /api/process
        rewrite: (path) => path.replace(/^\/api\/process/, "/"),
      },
    },
  },
});
