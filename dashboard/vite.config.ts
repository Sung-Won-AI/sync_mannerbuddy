import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
  envDir: "../" // 프로젝트 루트의 .env를 공유해서 사용
});
