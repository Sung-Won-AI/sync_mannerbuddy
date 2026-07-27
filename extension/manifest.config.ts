import { defineManifest } from "@crxjs/vite-plugin";
import pkg from "./package.json";

export default defineManifest({
  manifest_version: 3,
  name: "MannerBuddy - 실시간 메일 매너 코치",
  version: pkg.version,
  description: "Gmail 작성 중 비즈니스 매너 표현을 실시간으로 교정합니다.",
  action: {
    default_popup: "src/popup/index.html"
  },
  background: {
    service_worker: "src/background/index.ts",
    type: "module"
  },
  content_scripts: [
    {
      matches: ["https://mail.google.com/*"],
      js: ["src/content/emailCorrection.ts"],
      run_at: "document_idle"
    }
  ],
  permissions: ["storage", "activeTab"],
  host_permissions: ["https://mail.google.com/*"]
});
