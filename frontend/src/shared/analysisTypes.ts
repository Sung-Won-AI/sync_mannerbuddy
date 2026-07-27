// 백엔드(app/schemas/analysis.py)의 필드명을 그대로 따른다. 지금은 백엔드 미연동이라
// 이 타입은 목업 데이터에만 쓰이지만, 나중에 실제 응답을 받을 때 변환 없이 그대로 쓸 수 있게 맞춰둔다.

export type TargetCountry = "US" | "JP" | "CN";
export type AnalysisCategory = "vocabulary" | "tone" | "taboo" | "manners";
export type IssueSeverity = "low" | "medium" | "high";

export interface AnalysisIssue {
  issue_id: string;
  original: string;
  start_index: number;
  end_index: number;
  category: AnalysisCategory;
  severity: IssueSeverity;
  reason: string;
  suggestion: string;
}
