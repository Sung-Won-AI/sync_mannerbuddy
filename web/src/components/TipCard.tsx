import type { AnalysisIssue } from "../shared/meetingTypes";

interface TipCardProps {
  issue: AnalysisIssue;
  onClose: () => void;
}

const SEVERITY_LABEL: Record<AnalysisIssue["severity"], string> = {
  low: "참고",
  medium: "주의",
  high: "중요"
};

export function TipCard({ issue, onClose }: TipCardProps) {
  return (
    <div className="tip-card" role="dialog">
      <div className="tip-card__arrow" />
      <div className="tip-card__header">
        <span className="tip-card__mark" aria-hidden="true">
          ◆
        </span>
        <span className={`tip-card__severity tip-card__severity--${issue.severity}`}>
          {SEVERITY_LABEL[issue.severity]}
        </span>
        <button className="tip-card__close" onClick={onClose} aria-label="닫기">
          ✕
        </button>
      </div>
      <p className="tip-card__reason">{issue.reason}</p>
      <div className="tip-card__suggestion">
        <span className="tip-card__suggestion-label">
          {issue.fix_type === "insert" ? "이렇게 보완해보세요" : "이렇게 말해보세요"}
        </span>
        {issue.suggestion}
      </div>
    </div>
  );
}
