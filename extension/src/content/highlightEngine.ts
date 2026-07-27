// [기능 1] Gmail 작성창 하이라이트 + 팝업 카드 엔진
// 백엔드 /api/v1/analyses/email 응답의 issues(start_index/end_index)를 작성창 텍스트에 매핑해
// 형광펜 스타일로 감싸고, 클릭 시 CorrectionCard를 문구 바로 아래에 띄워 적용/무시를 선택하게 한다.

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

interface TextSpan {
  node: Text;
  start: number;
  end: number;
}

function collectTextSpans(container: HTMLElement): { text: string; spans: TextSpan[] } {
  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, {
    acceptNode(node: Node): number {
      const parent = (node as Text).parentElement;
      if (parent?.closest(`.${HIGHLIGHT_CLASS}`)) {
        return NodeFilter.FILTER_REJECT;
      }
      return NodeFilter.FILTER_ACCEPT;
    }
  });

  const spans: TextSpan[] = [];
  let text = "";
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    const textNode = node as Text;
    const start = text.length;
    text += textNode.data;
    spans.push({ node: textNode, start, end: text.length });
  }
  return { text, spans };
}

function wrapIssue(span: TextSpan, issue: AnalysisIssue, localStart: number, localEnd: number): void {
  const range = document.createRange();
  range.setStart(span.node, localStart);
  range.setEnd(span.node, localEnd);

  const mark = document.createElement("span");
  mark.className = HIGHLIGHT_CLASS;
  mark.dataset.mbId = issue.issue_id;
  mark.addEventListener("click", (event) => {
    event.stopPropagation();
    openCard(mark, issue);
  });

  range.surroundContents(mark);
}

// 작성창의 텍스트 노드를 순서대로 이어붙인 문자열. 백엔드로 보내는 text도 반드시 이 함수로 만들어야
// 응답의 start_index/end_index가 여기서 계산하는 spans와 어긋나지 않는다.
export function readComposeText(container: HTMLElement): string {
  return collectTextSpans(container).text;
}

export function applyHighlights(container: HTMLElement, issues: AnalysisIssue[]): void {
  const { spans } = collectTextSpans(container);

  // 뒤쪽 issue부터 처리해야 한 텍스트 노드 안에 issue가 여러 개 있어도
  // surroundContents로 인한 노드 분할이 앞쪽 offset을 깨뜨리지 않는다.
  const byDescendingStart = [...issues].sort((a, b) => b.start_index - a.start_index);

  for (const issue of byDescendingStart) {
    // 문단 경계를 넘나드는 issue(두 텍스트 노드에 걸침)는 이번 범위에서 스킵한다.
    const span = spans.find((s) => issue.start_index >= s.start && issue.end_index <= s.end);
    if (!span) continue;
    wrapIssue(span, issue, issue.start_index - span.start, issue.end_index - span.start);
  }
}
