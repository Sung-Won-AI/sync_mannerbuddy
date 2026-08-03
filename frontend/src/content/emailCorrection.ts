// Gmail 작성창(compose box)에 입력되는 문장을 백엔드(app)로 보내 분석하고,
// 반환된 issues[]를 하이라이트로 표시한다. 하이라이트 클릭 시 뜨는 카드(CorrectionCard)로
// 적용/무시를 선택하게 한다. 실제 네트워크 호출은 src/background에서만 수행한다.
//
// 호출 비용을 줄이기 위해 매 입력마다 요청을 보내지 않고, 아래 두 조건 중 하나일 때만 분석한다:
//   1) 1.5초 동안 추가 입력이 없을 때 (타이핑 중단)
//   2) 문장이 마침표/물음표/느낌표로 끝났을 때 (문장 완성) — 이 경우 1.5초를 기다리지 않고 바로 분석한다.

import { scanAndHighlight, clearHighlights, getPlainText } from "./highlightEngine";
import type { EmailAnalysisRequest, TargetCountry } from "../shared/analysisTypes";
import type { AnalyzeEmailMessage, AnalyzeEmailResult } from "../shared/messages";

// aria-label은 Gmail 언어 설정에 따라 달라지므로(예: "메시지 본문"/"Message Body"),
// 로케일에 무관한 Gmail 작성창 클래스(Am/Al/editable)를 우선 사용하고 aria-label은 예비로 둔다.
const GMAIL_COMPOSE_SELECTOR =
  "div.Am.Al.editable[contenteditable='true'], div[aria-label='메시지 본문'], div[aria-label='Message Body']";

const IDLE_TRIGGER_MS = 1500;
const SENTENCE_END_PATTERN = /[.!?]\s*$/;
const MIN_TEXT_LENGTH = 10;

const HIRAGANA_KATAKANA_PATTERN = /[぀-ゟ゠-ヿ]/;
const CJK_IDEOGRAPH_PATTERN = /[一-鿿]/;

// target_country는 "이 글을 어느 나라 비즈니스 상대방이 읽는가" 기준이라
// 입력 문장 자체의 스크립트(가나/한자 포함 여부)로 추론한다.
// 가나가 있으면 일본어, 한자만 있으면 중국어, 그 외(라틴 문자 등)는 영미권으로 본다.
function inferLanguageContext(text: string): { targetCountry: TargetCountry; language: string } {
  if (HIRAGANA_KATAKANA_PATTERN.test(text)) return { targetCountry: "JP", language: "ja" };
  if (CJK_IDEOGRAPH_PATTERN.test(text)) return { targetCountry: "CN", language: "zh" };
  return { targetCountry: "US", language: "en" };
}

function observeComposeBoxes(): void {
  const scan = () => {
    document.querySelectorAll<HTMLElement>(GMAIL_COMPOSE_SELECTOR).forEach(attachCorrectionListener);
  };

  scan(); // content script가 주입되는 시점에 이미 열려 있는 작성창도 잡는다.

  const observer = new MutationObserver(scan);
  observer.observe(document.body, { childList: true, subtree: true });
}

type ReviewMode = "realtime" | "before-send";

const attachedBoxes = new WeakSet<HTMLElement>();
const idleTimers = new WeakMap<HTMLElement, number>();
// 이미 분석을 보낸 구간의 길이(문자 오프셋). 문장당 교정 기회는 한 번뿐이라,
// 다음 트리거부터는 이 지점 이후 새로 추가된 부분만 보낸다.
const reviewedOffsets = new WeakMap<HTMLElement, number>();
// 직전에 보낸 신규 구간. 같은 내용으로 중복 요청되는 걸 막는다.
const lastSentSegment = new WeakMap<HTMLElement, string>();
// 응답이 늦게 도착한 이전 요청이 최신 하이라이트를 덮어쓰지 않도록 상자별 요청 번호를 추적한다.
const latestRequestSeq = new WeakMap<HTMLElement, number>();
// 사용자가 선택한 검토 방식. 기본은 실시간.
const reviewModes = new WeakMap<HTMLElement, ReviewMode>();
// "발송 전 검토" 모드에서 이미 한 번 검토를 마쳤는지. 검토 후 수정 여부와 상관없이
// 두 번째 보내기부터는 다시 검토하지 않는다 — 검토 기회는 발송당 한 번뿐.
const hasReviewedBeforeSend = new WeakSet<HTMLElement>();

function attachCorrectionListener(composeBox: HTMLElement): void {
  if (attachedBoxes.has(composeBox)) return;
  attachedBoxes.add(composeBox);

  attachModeToggle(composeBox);
  attachSendInterception(composeBox);

  composeBox.addEventListener("input", () => {
    if ((reviewModes.get(composeBox) ?? "realtime") !== "realtime") return; // 발송 전 검토 모드에서는 실시간 트리거를 쓰지 않는다.

    window.clearTimeout(idleTimers.get(composeBox));

    if (SENTENCE_END_PATTERN.test(getPlainText(composeBox))) {
      void maybeRequestAndHighlight(composeBox);
      return;
    }

    const timer = window.setTimeout(() => void maybeRequestAndHighlight(composeBox), IDLE_TRIGGER_MS);
    idleTimers.set(composeBox, timer);
  });
}

function attachModeToggle(composeBox: HTMLElement): void {
  const toggle = document.createElement("div");
  toggle.className = "mb-mode-toggle";
  toggle.innerHTML =
    '<button type="button" data-mode="realtime" class="mb-mode-toggle__btn mb-mode-toggle__btn--active">실시간 교정</button>' +
    '<button type="button" data-mode="before-send" class="mb-mode-toggle__btn">발송 전 검토</button>';

  toggle.addEventListener("click", (event) => {
    const button = (event.target as HTMLElement).closest<HTMLButtonElement>("button[data-mode]");
    if (!button) return;
    event.stopPropagation();

    const mode = button.dataset.mode as ReviewMode;
    reviewModes.set(composeBox, mode);

    toggle.querySelectorAll<HTMLButtonElement>(".mb-mode-toggle__btn").forEach((btn) => {
      btn.classList.toggle("mb-mode-toggle__btn--active", btn === button);
    });

    if (mode === "before-send") {
      window.clearTimeout(idleTimers.get(composeBox));
      clearHighlights(composeBox);
    }
  });

  composeBox.insertAdjacentElement("beforebegin", toggle);
}

const SEND_BUTTON_TEXT_PATTERN = /^(보내기|Send)$/;

function findSendButton(composeBox: HTMLElement): HTMLElement | null {
  const scope = composeBox.closest<HTMLElement>('[role="dialog"]') ?? document.body;
  const candidates = scope.querySelectorAll<HTMLElement>('div[role="button"]');
  for (const candidate of candidates) {
    if (SEND_BUTTON_TEXT_PATTERN.test(candidate.textContent?.trim() ?? "")) {
      return candidate;
    }
  }
  return null;
}

function attachSendInterception(composeBox: HTMLElement): void {
  let attachedButton: HTMLElement | null = null;

  const tryAttach = () => {
    if (attachedButton && document.contains(attachedButton)) return;

    const sendButton = findSendButton(composeBox);
    if (!sendButton) return;
    attachedButton = sendButton;

    sendButton.addEventListener(
      "click",
      (event) => {
        if ((reviewModes.get(composeBox) ?? "realtime") !== "before-send") return;
        if (hasReviewedBeforeSend.has(composeBox)) return; // 이미 한 번 검토했으면 더 막지 않는다.

        const fullText = getPlainText(composeBox).trim();
        if (fullText.length < MIN_TEXT_LENGTH) return; // 내용이 거의 없으면 검토 없이 그대로 보낸다.

        event.preventDefault();
        event.stopImmediatePropagation();
        void reviewBeforeSend(composeBox, sendButton);
      },
      true // Gmail 자체 발송 핸들러보다 먼저 가로채기 위해 캡처 단계에서 잡는다.
    );
  };

  tryAttach();
  const observer = new MutationObserver(tryAttach);
  observer.observe(document.body, { childList: true, subtree: true });
}

async function reviewBeforeSend(composeBox: HTMLElement, sendButton: HTMLElement): Promise<void> {
  const fullText = getPlainText(composeBox).trim();
  hasReviewedBeforeSend.add(composeBox); // 결과와 무관하게 이 발송 시도에서 검토 기회를 소진한다.

  const status = document.createElement("span");
  status.className = "mb-send-review-status";
  status.textContent = "매너 검토 중...";
  sendButton.insertAdjacentElement("afterend", status);

  try {
    const { targetCountry, language } = inferLanguageContext(fullText);
    const payload: EmailAnalysisRequest = {
      text: fullText,
      target_country: targetCountry,
      language,
      source: "gmail",
      mode: "manual",
      client_request_id: crypto.randomUUID()
    };
    const message: AnalyzeEmailMessage = { type: "ANALYZE_EMAIL", payload };

    let result: AnalyzeEmailResult;
    try {
      result = await chrome.runtime.sendMessage(message);
    } catch (error) {
      console.warn("[MannerBuddy] 발송 전 검토 실패, 그대로 발송합니다.", error);
      sendButton.click();
      return;
    }

    if (!result.ok || result.data.issues.length === 0) {
      sendButton.click();
      return;
    }

    scanAndHighlight(composeBox, result.data.analysis_id, result.data.issues);
    window.alert(
      `발송 전 검토에서 ${result.data.issues.length}건의 매너 교정 제안을 찾았습니다.\n` +
        "하이라이트된 부분을 확인해보시고, 그대로 보내시려면 보내기를 다시 눌러주세요."
    );
  } finally {
    status.remove();
  }
}

async function maybeRequestAndHighlight(composeBox: HTMLElement): Promise<void> {
  const fullText = getPlainText(composeBox);

  if (fullText.trim().length < MIN_TEXT_LENGTH) {
    reviewedOffsets.delete(composeBox);
    lastSentSegment.delete(composeBox);
    clearHighlights(composeBox);
    return;
  }

  // 이미 리뷰된 구간(reviewedUpTo) 이후, 새로 추가된 부분만 분석 대상으로 삼는다.
  const reviewedUpTo = Math.min(reviewedOffsets.get(composeBox) ?? 0, fullText.length);
  const newSegment = fullText.slice(reviewedUpTo);

  if (newSegment.trim().length < MIN_TEXT_LENGTH) return; // 새 구간이 아직 짧으면 더 입력될 때까지 대기
  if (newSegment === lastSentSegment.get(composeBox)) return; // 직전과 같은 신규 구간이면 다시 보내지 않는다.
  lastSentSegment.set(composeBox, newSegment);

  const seq = (latestRequestSeq.get(composeBox) ?? 0) + 1;
  latestRequestSeq.set(composeBox, seq);

  const { targetCountry, language } = inferLanguageContext(newSegment);
  const payload: EmailAnalysisRequest = {
    text: newSegment,
    target_country: targetCountry,
    language,
    source: "gmail",
    mode: "automatic",
    client_request_id: crypto.randomUUID()
  };

  const message: AnalyzeEmailMessage = { type: "ANALYZE_EMAIL", payload };
  let result: AnalyzeEmailResult;
  try {
    result = await chrome.runtime.sendMessage(message);
  } catch (error) {
    // 확장이 리로드/업데이트된 뒤 이 탭을 새로고침하지 않으면 chrome.runtime이 끊긴다.
    console.warn(
      "[MannerBuddy] 확장 프로그램과 통신할 수 없습니다. 이 탭을 새로고침해주세요.",
      error
    );
    return;
  }

  if (latestRequestSeq.get(composeBox) !== seq) return; // 그 사이 더 새 요청이 나갔다면 이 응답은 버린다.

  if (!result.ok) {
    console.warn("[MannerBuddy] 분석 요청 실패:", result.error);
    return; // 실패한 구간은 reviewedOffsets를 갱신하지 않아, 다음 트리거에서 다시 시도된다.
  }

  // 이 구간은 성공적으로 리뷰됐으니 다시 보내지 않는다 — 문장(구간)당 교정 기회는 한 번뿐.
  reviewedOffsets.set(composeBox, fullText.length);

  // 응답의 start_index/end_index는 newSegment 기준이므로, 문서 전체 기준으로 보정한다.
  // scanAndHighlight가 기존 하이라이트를 모두 지우고 새로 그리기 때문에, 이전에 검토된
  // 문장의 하이라이트는(사용자가 적용/무시하지 않았더라도) 자연히 사라진다.
  const offsetIssues = result.data.issues.map((issue) => ({
    ...issue,
    start_index: issue.start_index + reviewedUpTo,
    end_index: issue.end_index + reviewedUpTo
  }));

  scanAndHighlight(composeBox, result.data.analysis_id, offsetIssues);
}

observeComposeBoxes();
