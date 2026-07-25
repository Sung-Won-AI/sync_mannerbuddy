// [기능 1] 백그라운드 서비스 워커
// content script(emailCorrection.ts)로부터 교정 요청을 받아 백엔드 API를 호출하고
// 결과를 다시 content script로 전달하는 중계 역할을 한다.

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== "CORRECT_EMAIL_TEXT") return;

  fetch(`${API_BASE_URL}/api/email-correction`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: message.text })
  })
    .then((res) => res.json())
    .then((data) => sendResponse({ ok: true, data }))
    .catch((error) => sendResponse({ ok: false, error: String(error) }));

  return true; // 비동기 응답을 위해 true 반환
});
