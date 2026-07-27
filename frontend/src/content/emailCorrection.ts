// Gmail 작성창(compose box)에 입력되는 문장을 백엔드(app)로 보내 분석하고,
// 반환된 issues[]를 하이라이트로 표시한다. 하이라이트 클릭 시 뜨는 카드(CorrectionCard)로
// 적용/무시를 선택하게 한다. 실제 네트워크 호출은 src/background에서만 수행한다.

import { scanAndHighlight, clearHighlights } from "./highlightEngine";
import type { EmailAnalysisRequest, TargetCountry } from "../shared/analysisTypes";
import type { AnalyzeEmailMessage, AnalyzeEmailResult } from "../shared/messages";

// aria-label은 Gmail 언어 설정에 따라 달라지므로(예: "메시지 본문"/"Message Body"),
// 로케일에 무관한 Gmail 작성창 클래스(Am/Al/editable)를 우선 사용하고 aria-label은 예비로 둔다.
const GMAIL_COMPOSE_SELECTOR =
  "div.Am.Al.editable[contenteditable='true'], div[aria-label='메시지 본문'], div[aria-label='Message Body']";
const SCAN_DEBOUNCE_MS = 800;
const MIN_TEXT_LENGTH = 10;
const TARGET_COUNTRY: TargetCountry = "JP";

function observeComposeBoxes(): void {
  const scan = () => {
    document.querySelectorAll<HTMLElement>(GMAIL_COMPOSE_SELECTOR).forEach(attachCorrectionListener);
  };

  scan(); // content script가 주입되는 시점에 이미 열려 있는 작성창도 잡는다.

  const observer = new MutationObserver(scan);
  observer.observe(document.body, { childList: true, subtree: true });
}

const attachedBoxes = new WeakSet<HTMLElement>();
// 응답이 늦게 도착한 이전 요청이 최신 하이라이트를 덮어쓰지 않도록 상자별 요청 번호를 추적한다.
const latestRequestSeq = new WeakMap<HTMLElement, number>();

function attachCorrectionListener(composeBox: HTMLElement): void {
  if (attachedBoxes.has(composeBox)) return;
  attachedBoxes.add(composeBox);

  let debounceTimer: number | undefined;
  composeBox.addEventListener("input", () => {
    window.clearTimeout(debounceTimer);
    debounceTimer = window.setTimeout(() => void requestAndHighlight(composeBox), SCAN_DEBOUNCE_MS);
  });
}

async function requestAndHighlight(composeBox: HTMLElement): Promise<void> {
  const text = composeBox.innerText.trim();
  if (text.length < MIN_TEXT_LENGTH) {
    clearHighlights(composeBox);
    return;
  }

  const seq = (latestRequestSeq.get(composeBox) ?? 0) + 1;
  latestRequestSeq.set(composeBox, seq);

  const payload: EmailAnalysisRequest = {
    text,
    target_country: TARGET_COUNTRY,
    language: "en",
    source: "gmail",
    mode: "automatic",
    client_request_id: crypto.randomUUID()
  };

  const message: AnalyzeEmailMessage = { type: "ANALYZE_EMAIL", payload };
  const result: AnalyzeEmailResult = await chrome.runtime.sendMessage(message);

  if (latestRequestSeq.get(composeBox) !== seq) return; // 그 사이 더 새 요청이 나갔다면 이 응답은 버린다.

  if (!result.ok) {
    console.warn("[MannerBuddy] 분석 요청 실패:", result.error);
    return;
  }

  scanAndHighlight(composeBox, result.data.issues);
}

observeComposeBoxes();
