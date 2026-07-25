// [기능 1] 교정 제안 카드 UI
// 하이라이트된 문구를 클릭했을 때 뜨는 팝업. 제안 문구/이유를 보여주고 적용 여부를 선택하게 한다.

import type { CorrectionLang, CorrectionSuggestion } from "./mockSuggestions";

interface CorrectionCardProps {
  suggestion: CorrectionSuggestion;
  onApply: () => void;
  onDismiss: () => void;
  onClose: () => void;
}

// 원문 언어를 사용자가 바로 알 수 있도록 배지 라벨로 표시 (설명은 한국어, 수정본은 원문 언어 유지)
const LANG_LABEL: Record<CorrectionLang, string> = {
  ja: "일본어",
  en: "영어"
};

export function CorrectionCard({ suggestion, onApply, onDismiss, onClose }: CorrectionCardProps) {
  return (
    <div className="mb-card">
      <div className="mb-card__arrow" />
      <div className="mb-card__header">
        <span className="mb-card__icon" aria-hidden="true">
          💡
        </span>
        <span className="mb-card__title">더 예의바르게 표현해볼까요?</span>
        <span className="mb-card__lang-badge">{LANG_LABEL[suggestion.lang]} 교정</span>
        <button className="mb-card__close" onClick={onClose} aria-label="닫기">
          ✕
        </button>
      </div>
      <div className="mb-card__body">
        <div className="mb-card__suggestion" lang={suggestion.lang}>
          {suggestion.suggested}
        </div>
        <div className="mb-card__reason">{suggestion.reason}</div>
      </div>
      <div className="mb-card__actions">
        <button className="mb-card__btn mb-card__btn--primary" onClick={onApply}>
          ✎ 원문 수정하기
        </button>
        <button className="mb-card__btn mb-card__btn--secondary" onClick={onDismiss}>
          ✓ 괜찮아요
        </button>
      </div>
    </div>
  );
}
