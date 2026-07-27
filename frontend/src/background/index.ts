// extension-example/service-worker.js와 동일한 계약(POST /api/v1/analyses/email)으로
// 백엔드(app)와 통신하는 서비스 워커. content script는 이 워커에만 메시지를 보내고,
// 실제 네트워크 호출과 API_BASE_URL은 여기서만 다룬다.

import type { AnalyzeEmailMessage, AnalyzeEmailResult } from "../shared/messages";
import type { ApiErrorResponse, EmailAnalysisResponse } from "../shared/analysisTypes";

const API_BASE_URL = "http://127.0.0.1:8000";

chrome.runtime.onMessage.addListener((message: AnalyzeEmailMessage, _sender, sendResponse) => {
  if (message?.type !== "ANALYZE_EMAIL") {
    return undefined;
  }

  analyzeEmail(message)
    .then(sendResponse)
    .catch((error: unknown) =>
      sendResponse({
        ok: false,
        error: error instanceof Error ? error.message : "분석 요청에 실패했습니다."
      } satisfies AnalyzeEmailResult)
    );

  return true; // sendResponse를 비동기로 호출하기 위해 채널을 열어둔다.
});

async function analyzeEmail(message: AnalyzeEmailMessage): Promise<AnalyzeEmailResult> {
  const response = await fetch(`${API_BASE_URL}/api/v1/analyses/email`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Extension-Version": chrome.runtime.getManifest().version,
      "X-Request-ID": crypto.randomUUID()
    },
    body: JSON.stringify(message.payload)
  });

  const data = (await response.json()) as EmailAnalysisResponse | ApiErrorResponse;
  if (!response.ok || "error" in data) {
    const message_ = "error" in data ? data.error.message : "분석 요청에 실패했습니다.";
    return { ok: false, error: message_ };
  }

  return { ok: true, data };
}
