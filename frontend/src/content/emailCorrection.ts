// Gmail 작성창(compose box)에 입력되는 문장을 감지해 매너 교정이 필요한 부분에 하이라이트를 표시하고,
// 하이라이트 클릭 시 뜨는 카드(CorrectionCard)로 적용/무시를 선택하게 한다.
// 백엔드 미연동 단계 — 서버로 텍스트를 보내지 않고 로컬에서 바로 스캔한다.

import { scanAndHighlight } from "./highlightEngine";

const GMAIL_COMPOSE_SELECTOR = "div[aria-label='메시지 본문'], div[aria-label='Message Body']";
const SCAN_DEBOUNCE_MS = 800;

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
    debounceTimer = window.setTimeout(() => scanAndHighlight(composeBox), SCAN_DEBOUNCE_MS);
  });
}

observeComposeBoxes();