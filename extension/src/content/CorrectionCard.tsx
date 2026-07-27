// [기능 1] 교정 제안 카드 UI
// 하이라이트된 문구를 클릭했을 때 뜨는 팝업. 제안 문구/이유를 보여주고 적용 여부를 선택하게 한다.

import type { AnalysisCategory, AnalysisIssue } from "../shared/analysisTypes";

interface CorrectionCardProps {
  issue: AnalysisIssue;
  onApply: () => void;
  onDismiss: () => void;
  onClose: () => void;
}

// 어떤 종류의 문제인지 사용자가 바로 알 수 있도록 배지 라벨로 표시
const CATEGORY_LABEL: Record<AnalysisCategory, string> = {
  vocabulary: "어휘",
  tone: "말투",
  taboo: "금기 표현",
  manners: "매너"
};

export function CorrectionCard({ issue, onApply, onDismiss, onClose }: CorrectionCardProps) {
  return (
    <div className="mb-card">
      <div className="mb-card__arrow" />
      <div className="mb-card__header">
        <span className="mb-card__icon" aria-hidden="true">
          💡
        </span>
        <span className="mb-card__title">더 예의바르게 표현해볼까요?</span>
        <span className="mb-card__lang-badge">{CATEGORY_LABEL[issue.category]}</span>
        <button className="mb-card__close" onClick={onClose} aria-label="닫기">
          ✕
        </button>
      </div>
      <div className="mb-card__body">
        <div className="mb-card__suggestion">{issue.suggestion}</div>
        <div className="mb-card__reason">{issue.reason}</div>
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
