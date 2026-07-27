// [기능 1] Gmail 실시간 메일 문장 수정
// Gmail 작성창(compose box)에 입력되는 문장을 감지해 백엔드 분석 결과를 하이라이트로 표시하고,
// 하이라이트 클릭 시 뜨는 카드(CorrectionCard)로 적용/무시를 선택하게 한다.

import { applyHighlights, readComposeText } from "./highlightEngine";
import type { EmailAnalysisResponse, TargetCountry } from "../shared/analysisTypes";

const GMAIL_COMPOSE_SELECTOR = "div[aria-label='메시지 본문'], div[aria-label='Message Body']";
const SCAN_DEBOUNCE_MS = 800;
const MIN_ANALYSIS_LENGTH = 10; // 백엔드 EmailAnalysisRequest.text 최소 길이와 동일

// TODO: 국가 선택 UI(popup)가 생기기 전까지는 기본값으로 고정한다.
const DEFAULT_TARGET_COUNTRY: TargetCountry = "US";

function observeComposeBoxes(): void {
  const observer = new MutationObserver(() => {
    document.querySelectorAll<HTMLElement>(GMAIL_COMPOSE_SELECTOR).forEach(attachCorrectionListener);
  });

  observer.observe(document.body, { childList: true, subtree: true });
}

const attachedBoxes = new WeakSet<HTMLElement>();

function attachCorrectionListener(composeBox: HTMLElement): void {
  if (attachedBoxes.has(composeBox)) return;
  attachedBoxes.add(composeBox);

  let debounceTimer: number | undefined;
  composeBox.addEventListener("input", () => {
    window.clearTimeout(debounceTimer);
    debounceTimer = window.setTimeout(() => requestAnalysis(composeBox), SCAN_DEBOUNCE_MS);
  });
}

function requestAnalysis(composeBox: HTMLElement): void {
  const text = readComposeText(composeBox);
  if (text.trim().length < MIN_ANALYSIS_LENGTH) return;

  chrome.runtime.sendMessage(
    { type: "ANALYZE_EMAIL_TEXT", text, targetCountry: DEFAULT_TARGET_COUNTRY },
    (response: { ok: true; data: EmailAnalysisResponse } | { ok: false; error: string }) => {
      if (!response?.ok) {
        console.error("메일 분석 요청 실패", response?.error);
        return;
      }
      applyHighlights(composeBox, response.data.issues);
    }
  );
}

observeComposeBoxes();
