// 백엔드 미연동 상태에서 UI를 보여주기 위한 샘플 데이터.
// 실제 연동 시 POST /api/v1/analyses/email 응답의 issues[]로 교체하고,
// 이 파일은 지운다.

import type { AnalysisIssue } from "../shared/analysisTypes";

export const SAMPLE_TRIGGER = "今週金曜日までに数量をご連絡ください";

export const SAMPLE_ISSUE: AnalysisIssue = {
  issue_id: "sample-issue-1",
  original: SAMPLE_TRIGGER,
  start_index: 0,
  end_index: SAMPLE_TRIGGER.length,
  category: "tone",
  severity: "medium",
  reason: "일본 비즈니스에서는 직접적인 기한 제시보다 '괜찮으시다면'과 같은 완충 표현을 사용해요.",
  suggestion: "もし差し支えなければ、今週金曜日頃を目安にご意向をお聞かせいただけますと幸いです。"
};