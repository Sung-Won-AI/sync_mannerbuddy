// 하이라이트된 문구를 클릭했을 때 뜨는 교정 제안 카드.
// 왼쪽: 제안 문구 + 액션 버튼 / 오른쪽: 제안 이유. (이미지 시안 레이아웃 기준)

import type { AnalysisIssue } from "../shared/analysisTypes";

interface CorrectionCardProps {
  issue: AnalysisIssue;
  onApply: () => void;
  onDismiss: () => void;
  onClose: () => void;
}

export function CorrectionCard({ issue, onApply, onDismiss, onClose }: CorrectionCardProps) {
  return (
    <div className="mb-card">
      <div className="mb-card__arrow" />
      <div className="mb-card__header">
        <span className="mb-card__icon" aria-hidden="true">
          💡
        </span>
        <span className="mb-card__title">더 예의바르게 표현해볼까요?</span>
        <button className="mb-card__close" onClick={onClose} aria-label="닫기">
          ✕
        </button>
      </div>
      <div className="mb-card__body">
        <div className="mb-card__left">
          <div className="mb-card__suggestion" lang="ja">
            {issue.suggestion}
          </div>
          <div className="mb-card__actions">
            <button className="mb-card__btn mb-card__btn--primary" onClick={onApply}>
              {issue.fix_type === "insert" ? "✎ 여기에 이어쓰기" : "✎ 원문 수정하기"}
            </button>
            <button className="mb-card__btn mb-card__btn--secondary" onClick={onDismiss}>
              ✓ 괜찮아요
            </button>
          </div>
        </div>
        <div className="mb-card__reason">{issue.reason}</div>
      </div>
    </div>
  );
}