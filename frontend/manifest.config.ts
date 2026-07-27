import { defineManifest } from "@crxjs/vite-plugin";
import pkg from "./package.json";

export default defineManifest({
  manifest_version: 3,
  name: "MannerBuddy - 실시간 메일 매너 코치 (UI 프로토타입)",
  version: pkg.version,
  description: "Gmail 작성 중 비즈니스 매너 표현을 하이라이트하는 UI 프로토타입. 백엔드 연동 전 단계입니다.",
  content_scripts: [
    {
      matches: ["https://mail.google.com/*"],
      js: ["src/content/emailCorrection.ts"],
      run_at: "document_idle"
    }
  ],
  permissions: [],
  host_permissions: ["https://mail.google.com/*"]
});
