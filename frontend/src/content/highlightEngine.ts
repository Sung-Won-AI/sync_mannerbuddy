// Gmail 작성창 하이라이트 + 교정 제안 카드 엔진.
// 백엔드 응답 issues[]의 start_index/end_index(분석 시점 텍스트 기준 오프셋)로 구간을 찾아 하이라이트한다.

import { createElement } from "react";
import { createRoot, type Root } from "react-dom/client";
import { CorrectionCard } from "./CorrectionCard";
import type { AnalysisIssue, SuggestionAction } from "../shared/analysisTypes";
import type { SaveActionMessage } from "../shared/messages";
import "./styles.css";

const HIGHLIGHT_CLASS = "mb-highlight";
// styles.css의 .mb-card width와 맞춘 값. 뷰포트 밖으로 잘리지 않게 위치 계산에 쓴다.
const CARD_WIDTH = 600;
const VIEWPORT_MARGIN = 12;

let cardHost: HTMLDivElement | null = null;
let cardRoot: Root | null = null;

function ensureCardHost(): { host: HTMLDivElement; root: Root } {
  if (!cardHost || !cardRoot) {
    cardHost = document.createElement("div");
    cardHost.className = "mb-card-host";
    cardHost.style.display = "none";
    document.body.appendChild(cardHost);
    cardRoot = createRoot(cardHost);
  }
  return { host: cardHost, root: cardRoot };
}

function closeCard(): void {
  if (!cardHost || !cardRoot) return;
  cardHost.style.display = "none";
  cardRoot.render(null);
}

// 백엔드에 적용/거부/닫기 결과를 기록한다. 실패해도(백엔드 다운 등) 편집 흐름을
// 막지 않도록 콘솔 경고만 남기고 조용히 넘어간다.
function sendAction(analysisId: string, issueId: string, action: SuggestionAction): void {
  const message: SaveActionMessage = {
    type: "SAVE_ACTION",
    payload: { analysisId, issueId, action }
  };
  chrome.runtime.sendMessage(message).catch((error: unknown) => {
    console.warn("[MannerBuddy] 액션 저장 실패:", error);
  });
}

// 하이라이트 span을 풀어 원문 텍스트는 그대로 두고, 그 바로 뒤에 커서를 둔다.
// "무엇을 추가하라"는 권고성 제안을 실제로 대신 타이핑해주지 않고, 사용자가 이어 쓰게 한다.
function placeCursorAfter(anchor: HTMLElement): void {
  const textNode = document.createTextNode(anchor.textContent ?? "");
  anchor.replaceWith(textNode);

  const range = document.createRange();
  range.setStartAfter(textNode);
  range.collapse(true);

  const selection = window.getSelection();
  selection?.removeAllRanges();
  selection?.addRange(range);

  textNode.parentElement?.closest<HTMLElement>('[contenteditable="true"]')?.focus();
}

// 하나의 issue가 DOM 텍스트 노드 경계를 넘나들면 highlightRange가 span을 여러 개로
// 쪼개어 감싼다(같은 data-mb-id 공유). 적용/무시 시 클릭된 anchor 하나만 고치면 나머지
// 조각이 원문에 그대로 남아 중복되므로, 같은 issue의 span을 전부 찾아 함께 처리한다.
function findSiblingSpans(anchor: HTMLElement, issue: AnalysisIssue): HTMLElement[] {
  const scope = anchor.closest<HTMLElement>('[contenteditable="true"]') ?? document.body;
  return Array.from(
    scope.querySelectorAll<HTMLElement>(`.${HIGHLIGHT_CLASS}[data-mb-id="${issue.issue_id}"]`)
  );
}

function openCard(anchor: HTMLElement, analysisId: string, issue: AnalysisIssue): void {
  const { host, root } = ensureCardHost();
  const rect = anchor.getBoundingClientRect();

  const maxLeft = window.innerWidth - CARD_WIDTH - VIEWPORT_MARGIN;
  const left = Math.min(rect.left, Math.max(maxLeft, VIEWPORT_MARGIN));

  // 아래쪽에 공간이 부족하면(화면 하단부 근처) 앵커 위쪽에 띄운다.
  const showAbove = rect.bottom + 10 > window.innerHeight * 0.7;
  const top = showAbove ? undefined : rect.bottom + 10;
  const bottom = showAbove ? window.innerHeight - rect.top + 10 : undefined;

  host.style.left = `${left}px`;
  host.style.top = top !== undefined ? `${top}px` : "";
  host.style.bottom = bottom !== undefined ? `${bottom}px` : "";
  // suggestion/reason이 길어 카드가 커져도 액션 버튼이 뷰포트 밖으로 밀려나지 않도록,
  // 카드가 실제로 놓인 위치 기준으로 남는 세로 공간만큼만 높이를 허용하고 넘치면
  // host 자체를 스크롤시킨다(styles.css의 overflow-y: auto와 함께 동작).
  const availableHeight =
    top !== undefined
      ? window.innerHeight - top - VIEWPORT_MARGIN
      : window.innerHeight - bottom! - VIEWPORT_MARGIN;
  host.style.maxHeight = `${Math.max(160, availableHeight)}px`;
  host.style.display = "block";

  root.render(
    createElement(CorrectionCard, {
      issue,
      onApply: () => {
        const spans = findSiblingSpans(anchor, issue);
        if (issue.fix_type === "insert") {
          // suggestion은 "무엇을 추가하라"는 권고일 뿐 실제 삽입 문장이 아니므로,
          // 원문은 그대로 두고 사용자가 이어서 직접 쓸 수 있게 커서만 그 위치로 옮긴다.
          placeCursorAfter(anchor);
          spans.filter((span) => span !== anchor).forEach((span) => span.replaceWith(document.createTextNode(span.textContent ?? "")));
        } else {
          // 여러 조각으로 나뉘어 있었다면 첫 조각만 suggestion으로 바꾸고 나머지는 통째로 지운다.
          spans[0]?.replaceWith(document.createTextNode(issue.suggestion));
          spans.slice(1).forEach((span) => span.remove());
        }
        sendAction(analysisId, issue.issue_id, "accepted");
        closeCard();
      },
      onDismiss: () => {
        findSiblingSpans(anchor, issue).forEach((span) => {
          span.replaceWith(document.createTextNode(span.textContent ?? ""));
        });
        sendAction(analysisId, issue.issue_id, "rejected");
        closeCard();
      },
      onClose: () => {
        sendAction(analysisId, issue.issue_id, "dismissed");
        closeCard();
      }
    })
  );
}

// 카드 바깥을 클릭하면 닫히도록. 하이라이트 클릭 핸들러는 stopPropagation으로 이 리스너를 막는다.
document.addEventListener("click", () => closeCard());

// scanAndHighlight가 항상 clearHighlights로 기존 하이라이트를 지운 뒤 호출되므로,
// 이 시점에는 .mb-highlight 안에 있는 텍스트 노드를 걸러낼 필요가 없다. 순수하게
// 텍스트 노드만 이어붙여야 getPlainText()가 만드는 문자열과 오프셋이 정확히 맞는다.
function collectTextNodes(container: HTMLElement): Text[] {
  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);

  const nodes: Text[] = [];
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    nodes.push(node as Text);
  }
  return nodes;
}

// 백엔드로 보내는 텍스트와 하이라이트 위치 계산에 쓰는 텍스트가 서로 다른 방식으로
// 뽑히면(예: innerText는 <div> 줄바꿈마다 합성 개행을 끼워 넣지만 텍스트 노드를
// 그냥 이어붙이면 그 개행이 없음) 오프셋이 어긋나 하이라이트가 단어 중간을 잘라버린다.
// 두 곳 모두 이 함수 하나로 텍스트를 뽑아써야 오프셋이 항상 일치한다.
export function getPlainText(container: HTMLElement): string {
  return collectTextNodes(container)
    .map((node) => node.data)
    .join("");
}

export function clearHighlights(container: HTMLElement): void {
  container.querySelectorAll<HTMLElement>(`.${HIGHLIGHT_CLASS}`).forEach((span) => {
    span.replaceWith(document.createTextNode(span.textContent ?? ""));
  });
  container.normalize();
}

// 한 구간을 하이라이트하면 그 뒤 텍스트 노드가 쪼개지므로, 앞쪽 오프셋에 영향을 주지 않도록
// start_index가 큰 이슈부터(뒤에서 앞으로) 처리한다.
function highlightRange(
  container: HTMLElement,
  analysisId: string,
  startIndex: number,
  endIndex: number,
  issue: AnalysisIssue
): void {
  let offset = 0;
  for (const textNode of collectTextNodes(container)) {
    const nodeStart = offset;
    const nodeEnd = offset + textNode.data.length;
    offset = nodeEnd;

    if (endIndex <= nodeStart || startIndex >= nodeEnd) continue;

    const localStart = Math.max(startIndex, nodeStart) - nodeStart;
    const localEnd = Math.min(endIndex, nodeEnd) - nodeStart;
    if (localStart >= localEnd) continue;

    const range = document.createRange();
    range.setStart(textNode, localStart);
    range.setEnd(textNode, localEnd);

    const span = document.createElement("span");
    span.className = HIGHLIGHT_CLASS;
    span.dataset.mbId = issue.issue_id;
    span.addEventListener("click", (event) => {
      event.stopPropagation();
      openCard(span, analysisId, issue);
    });

    range.surroundContents(span);

    // 이 구간이 여러 텍스트 노드에 걸쳐 있으면(문장 사이 줄바꿈 등으로 노드가 나뉜 경우)
    // 나머지 부분도 마저 감싸도록 다음 노드로 계속 진행한다. 여기서 return하면 뒷부분이
    // 하이라이트/치환 대상에서 빠져 원문이 그대로 남아버린다.
    if (endIndex <= nodeEnd) return;
  }
}

// original과 정확히 같은 문구가 이메일 안에 여러 번 나올 수 있으므로(반복되는 인사말 등),
// 모든 occurrence 중 서버가 준 start_index(약간 어긋났더라도 대략적인 위치는 맞음)에 가장
// 가까운 것을 고른다 — 단순히 첫 번째 occurrence를 쓰면 이미 지나간 구간의 같은 문구를
// 잘못 짚을 수 있다.
function findClosestOccurrence(fullText: string, needle: string, hint: number): number {
  if (!needle) return -1;
  let best = -1;
  let bestDistance = Infinity;
  for (let index = fullText.indexOf(needle); index !== -1; index = fullText.indexOf(needle, index + 1)) {
    const distance = Math.abs(index - hint);
    if (distance < bestDistance) {
      bestDistance = distance;
      best = index;
    }
  }
  return best;
}

// AI가 반환하는 original/오프셋은 프롬프트로 아무리 강조해도 가끔 단어 중간에서
// 잘린다("Your"의 "Y"를 빠뜨리고 "our..."부터 잡거나, "Please"의 "P"까지만 포함하고
// "lease"를 남기는 식). fix_type "replace"에서 이 상태로 그대로 치환하면 잘려나간
// 앞/뒤 글자가 고아처럼 남아 문장이 깨지므로, 최종 범위는 항상 온전한 단어 경계로
// 넓혀 스냅시킨다 — AI가 무엇을 반환하든 마지막 방어선 역할을 한다.
const WORD_CHAR_PATTERN = /[\p{L}\p{N}]/u;

function isWordChar(char: string | undefined): boolean {
  return char !== undefined && WORD_CHAR_PATTERN.test(char);
}

function snapToWordBoundaries(fullText: string, start: number, end: number): { start: number; end: number } {
  let snappedStart = start;
  while (snappedStart > 0 && isWordChar(fullText[snappedStart - 1]) && isWordChar(fullText[snappedStart])) {
    snappedStart--;
  }
  let snappedEnd = end;
  while (snappedEnd < fullText.length && isWordChar(fullText[snappedEnd - 1]) && isWordChar(fullText[snappedEnd])) {
    snappedEnd++;
  }
  return { start: snappedStart, end: snappedEnd };
}

// 서버 오프셋은 클라이언트가 뽑아낸 텍스트와 완전히 같은 방식으로 세어졌다는 가정에
// 의존하는데, Gmail은 문단마다 별도 <div>를 쓰고 빈 줄도 특수하게 구성돼 있어 그 가정이
// 쉽게 깨진다. AI가 원문 그대로 베낀 issue.original을 실제 DOM 텍스트에서 직접 찾는 편이
// 훨씬 안정적이므로 오프셋은 검색 실패 시의 폴백으로만 쓴다.
function resolveIssueRange(fullText: string, issue: AnalysisIssue): { start: number; end: number } | null {
  const found = findClosestOccurrence(fullText, issue.original, issue.start_index);
  if (found !== -1) {
    return snapToWordBoundaries(fullText, found, found + issue.original.length);
  }
  if (issue.start_index < issue.end_index && issue.end_index <= fullText.length) {
    return snapToWordBoundaries(fullText, issue.start_index, issue.end_index);
  }
  return null;
}

export function scanAndHighlight(container: HTMLElement, analysisId: string, issues: AnalysisIssue[]): void {
  clearHighlights(container);
  if (issues.length === 0) return;

  const fullText = getPlainText(container);
  const resolved = issues
    .map((issue) => {
      const range = resolveIssueRange(fullText, issue);
      return range && { issue, ...range };
    })
    .filter((entry): entry is { issue: AnalysisIssue; start: number; end: number } => Boolean(entry));

  const byStartDescending = resolved.sort((a, b) => b.start - a.start);
  for (const { issue, start, end } of byStartDescending) {
    highlightRange(container, analysisId, start, end, issue);
  }
}
