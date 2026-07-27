// Gmail 작성창 하이라이트 + 교정 제안 카드 엔진.
// 백엔드 응답 issues[]의 start_index/end_index(분석 시점 텍스트 기준 오프셋)로 구간을 찾아 하이라이트한다.

import { createElement } from "react";
import { createRoot, type Root } from "react-dom/client";
import { CorrectionCard } from "./CorrectionCard";
import type { AnalysisIssue } from "../shared/analysisTypes";
import "./styles.css";

const HIGHLIGHT_CLASS = "mb-highlight";

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

function openCard(anchor: HTMLElement, issue: AnalysisIssue): void {
  const { host, root } = ensureCardHost();
  const rect = anchor.getBoundingClientRect();

  host.style.top = `${rect.bottom + 10}px`;
  host.style.left = `${rect.left}px`;
  host.style.display = "block";

  root.render(
    createElement(CorrectionCard, {
      issue,
      onApply: () => {
        anchor.replaceWith(document.createTextNode(issue.suggestion));
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
