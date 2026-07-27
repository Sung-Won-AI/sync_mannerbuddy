// [기능 1] Gmail 작성창 하이라이트 + 팝업 카드 엔진
// 작성창 텍스트에서 교정 대상 문구를 찾아 형광펜 스타일로 감싸고,
// 클릭 시 CorrectionCard를 문구 바로 아래에 띄워 적용/무시를 선택할 수 있게 한다.

import { createElement } from "react";
import { createRoot, type Root } from "react-dom/client";
import { CorrectionCard } from "./CorrectionCard";
import { MOCK_SUGGESTIONS, type CorrectionSuggestion } from "./mockSuggestions";
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

function openCard(anchor: HTMLElement, suggestion: CorrectionSuggestion): void {
  const { host, root } = ensureCardHost();
  const rect = anchor.getBoundingClientRect();

  host.style.top = `${rect.bottom + 10}px`;
  host.style.left = `${rect.left}px`;
  host.style.display = "block";

  root.render(
    createElement(CorrectionCard, {
      suggestion,
      onApply: () => {
        anchor.replaceWith(document.createTextNode(suggestion.suggested));
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

function wrapMatch(textNode: Text, suggestion: CorrectionSuggestion, matchIndex: number): void {
  const range = document.createRange();
  range.setStart(textNode, matchIndex);
  range.setEnd(textNode, matchIndex + suggestion.trigger.length);

  const span = document.createElement("span");
  span.className = HIGHLIGHT_CLASS;
  span.dataset.mbId = suggestion.id;
  span.addEventListener("click", (event) => {
    event.stopPropagation();
    openCard(span, suggestion);
  });

  range.surroundContents(span);
}

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

  const textNodes: Text[] = [];
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    textNodes.push(node as Text);
  }

  for (const textNode of textNodes) {
    const suggestion = MOCK_SUGGESTIONS.find((s) => textNode.data.includes(s.trigger));
    if (suggestion) {
      wrapMatch(textNode, suggestion, textNode.data.indexOf(suggestion.trigger));
    }
  }
}
