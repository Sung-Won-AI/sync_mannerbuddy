// [기능 1] 백그라운드 서비스 워커
// content script(emailCorrection.ts)로부터 분석 요청을 받아 백엔드 /api/v1/analyses/email을 호출하고
// 결과를 다시 content script로 전달하는 중계 역할을 한다.

import type { EmailAnalysisRequest, EmailAnalysisResponse } from "../shared/analysisTypes";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

interface AnalyzeEmailMessage {
  type: "ANALYZE_EMAIL_TEXT";
  text: string;
  targetCountry: EmailAnalysisRequest["target_country"];
}

type AnalyzeEmailResponse = { ok: true; data: EmailAnalysisResponse } | { ok: false; error: string };

chrome.runtime.onMessage.addListener((message: AnalyzeEmailMessage, _sender, sendResponse) => {
  if (message?.type !== "ANALYZE_EMAIL_TEXT") return;

  const payload: EmailAnalysisRequest = {
    text: message.text,
    target_country: message.targetCountry,
    language: "en", // TODO: 작성창 언어 자동 감지
    source: "gmail",
    mode: "automatic"
  };

  fetch(`${API_BASE_URL}/api/v1/analyses/email`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Request-ID": crypto.randomUUID()
    },
    body: JSON.stringify(payload)
  })
    .then((res) => res.json())
    .then((data: EmailAnalysisResponse) => sendResponse({ ok: true, data } satisfies AnalyzeEmailResponse))
    .catch((error) => sendResponse({ ok: false, error: String(error) } satisfies AnalyzeEmailResponse));

  return true; // 비동기 응답을 위해 true 반환
});
