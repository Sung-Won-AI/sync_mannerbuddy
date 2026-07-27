// Gmail 작성창 하이라이트 + 교정 제안 카드 엔진.
// 백엔드 연동 전이라 mockAnalysis.SAMPLE_TRIGGER 문자열을 찾아 하이라이트한다.
// 연동 시: 텍스트를 백엔드로 보내고, 응답 issues[]의 start_index/end_index로 이 부분을 대체하면 된다.

import { createElement } from "react";
import { createRoot, type Root } from "react-dom/client";
import { CorrectionCard } from "./CorrectionCard";
import { SAMPLE_ISSUE, SAMPLE_TRIGGER } from "./mockAnalysis";
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

export function scanAndHighlight(container: HTMLElement): void {
  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, {
    acceptNode(node: Node): number {
      const parent = (node as Text).parentElement;
      if (parent?.closest(`.${HIGHLIGHT_CLASS}`)) {
        return NodeFilter.FILTER_REJECT;
      }
      return NodeFilter.FILTER_ACCEPT;
    }
  });

  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    const textNode = node as Text;
    const matchIndex = textNode.data.indexOf(SAMPLE_TRIGGER);
    if (matchIndex === -1) continue;

    const range = document.createRange();
    range.setStart(textNode, matchIndex);
    range.setEnd(textNode, matchIndex + SAMPLE_TRIGGER.length);

    const span = document.createElement("span");
    span.className = HIGHLIGHT_CLASS;
    span.dataset.mbId = SAMPLE_ISSUE.issue_id;
    span.addEventListener("click", (event) => {
      event.stopPropagation();
      openCard(span, SAMPLE_ISSUE);
    });

    range.surroundContents(span);
    break; // 데모용 샘플이 하나뿐이라 첫 매치만 하이라이트한다.
  }
}