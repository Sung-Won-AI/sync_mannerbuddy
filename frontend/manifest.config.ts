import { defineManifest } from "@crxjs/vite-plugin";
import pkg from "./package.json";

export default defineManifest({
  manifest_version: 3,
  name: "MannerBuddy - 실시간 메일 매너 코치",
  version: pkg.version,
  description: "Gmail 작성 중 비즈니스 매너 표현을 분석해 하이라이트하고 교정을 제안합니다.",
  background: {
    service_worker: "src/background/index.ts"
  },
  content_scripts: [
    {
      matches: ["https://mail.google.com/*"],
      js: ["src/content/emailCorrection.ts"],
      run_at: "document_idle"
    }
  ],
  permissions: [],
  host_permissions: ["https://mail.google.com/*", "http://127.0.0.1:8000/*"]
});
