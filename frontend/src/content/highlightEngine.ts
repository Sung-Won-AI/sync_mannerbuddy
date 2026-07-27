// Gmail 작성창 하이라이트 + 교정 제안 카드 엔진.
// 백엔드 응답 issues[]의 start_index/end_index(분석 시점 텍스트 기준 오프셋)로 구간을 찾아 하이라이트한다.

import { createElement } from "react";
import { createRoot, type Root } from "react-dom/client";
import { CorrectionCard } from "./CorrectionCard";
import type { AnalysisIssue } from "../shared/analysisTypes";
import "./styles.css";

const HIGHLIGHT_CLASS = "mb-highlight";
// styles.css의 .mb-card width와 맞춘 값. 뷰포트 밖으로 잘리지 않게 위치 계산에 쓴다.
const CARD_WIDTH = 460;
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

function openCard(anchor: HTMLElement, issue: AnalysisIssue): void {
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
  host.style.display = "block";

  root.render(
    createElement(CorrectionCard, {
      issue,
      onApply: () => {
        if (issue.fix_type === "insert") {
          // suggestion은 "무엇을 추가하라"는 권고일 뿐 실제 삽입 문장이 아니므로,
          // 원문은 그대로 두고 사용자가 이어서 직접 쓸 수 있게 커서만 그 위치로 옮긴다.
          placeCursorAfter(anchor);
        } else {
          anchor.replaceWith(document.createTextNode(issue.suggestion));
        }
        closeCard();
      },
      onDismiss: () => {
        anchor.replaceWith(document.createTextNode(anchor.textContent ?? ""));
        closeCard();
      },
      onClose: closeCard
    })
  );
}

// 카드 바깥을 클릭하면 닫히도록. 하이라이트 클릭 핸들러는 stopPropagation으로 이 리스너를 막는다.
document.addEventListener("click", () => closeCard());

function collectTextNodes(container: HTMLElement): Text[] {
  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, {
    acceptNode(node: Node): number {
      const parent = (node as Text).parentElement;
      if (parent?.closest(`.${HIGHLIGHT_CLASS}`)) {
        return NodeFilter.FILTER_REJECT;
      }
      return NodeFilter.FILTER_ACCEPT;
    }
  });

  const nodes: Text[] = [];
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    nodes.push(node as Text);
  }
  return nodes;
}

export function clearHighlights(container: HTMLElement): void {
  container.querySelectorAll<HTMLElement>(`.${HIGHLIGHT_CLASS}`).forEach((span) => {
    span.replaceWith(document.createTextNode(span.textContent ?? ""));
  });
  container.normalize();
}

// 한 구간을 하이라이트하면 그 뒤 텍스트 노드가 쪼개지므로, 앞쪽 오프셋에 영향을 주지 않도록
// start_index가 큰 이슈부터(뒤에서 앞으로) 처리한다.
function highlightRange(container: HTMLElement, startIndex: number, endIndex: number, issue: AnalysisIssue): void {
  let offset = 0;
  for (const textNode of collectTextNodes(container)) {
    const nodeStart = offset;
    const nodeEnd = offset + textNode.data.length;
    offset = nodeEnd;

    if (endIndex <= nodeStart || startIndex >= nodeEnd) continue;

    const localStart = Math.max(startIndex, nodeStart) - nodeStart;
    const localEnd = Math.min(endIndex, nodeEnd) - nodeStart;
    if (localStart >= localEnd) return;

    const range = document.createRange();
    range.setStart(textNode, localStart);
    range.setEnd(textNode, localEnd);

    const span = document.createElement("span");
    span.className = HIGHLIGHT_CLASS;
    span.dataset.mbId = issue.issue_id;
    span.addEventListener("click", (event) => {
      event.stopPropagation();
      openCard(span, issue);
    });

    range.surroundContents(span);
    return; // 노드 경계를 넘나드는 구간은 첫 교차 노드까지만 감싼다.
  }
}

export function scanAndHighlight(container: HTMLElement, issues: AnalysisIssue[]): void {
  clearHighlights(container);
  if (issues.length === 0) return;

  const byStartDescending = [...issues].sort((a, b) => b.start_index - a.start_index);
  for (const issue of byStartDescending) {
    highlightRange(container, issue.start_index, issue.end_index, issue);
  }
}
