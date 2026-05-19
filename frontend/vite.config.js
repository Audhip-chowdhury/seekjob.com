import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    allowedHosts: ["seekjob.audhip-projects.com"],
  },
  preview: {
    host: true,
    allowedHosts: ["seekjob.audhip-projects.com"],
  },
});
