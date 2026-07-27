// 백엔드(app/schemas/analysis.py, docs/extension-api-contract.md)의 필드명을 그대로 따른다.
// 응답을 변환 없이 그대로 사용할 수 있도록 이름과 타입을 맞춰둔다.

export type TargetCountry = "US" | "JP" | "CN";
export type AnalysisCategory = "vocabulary" | "tone" | "taboo" | "manners";
export type IssueSeverity = "low" | "medium" | "high";
// "replace": suggestion을 original 자리에 그대로 넣으면 되는 실제 대체 문장.
// "insert": 인사말/마무리처럼 원문에 없는 걸 새로 추가해야 하는 경우 — suggestion은
// "무엇을 넣으면 좋을지"에 대한 권고일 뿐, 그대로 삽입할 문장이 아니다.
export type IssueFixType = "replace" | "insert";

export interface AnalysisIssue {
  issue_id: string;
  original: string;
  start_index: number;
  end_index: number;
  category: AnalysisCategory;
  severity: IssueSeverity;
  reason: string;
  suggestion: string;
  fix_type: IssueFixType;
}

export interface AnalysisScores {
  vocabulary: number;
  tone: number;
  taboo: number;
  manners: number;
}

export interface EmailAnalysisRequest {
  text: string;
  target_country: TargetCountry;
  language?: string;
  source?: string;
  mode?: "manual" | "automatic";
  client_request_id?: string;
}

export interface EmailAnalysisResponse {
  analysis_id: string;
  status: string;
  request_id: string | null;
  overall_score: number;
  scores: AnalysisScores;
  issues: AnalysisIssue[];
  revised_text: string;
  summary: string;
  processing_time_ms: number;
  created_at: string;
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
    request_id: string | null;
  };
}
