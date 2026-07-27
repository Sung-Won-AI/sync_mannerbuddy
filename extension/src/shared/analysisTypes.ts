// [기능 1] 백엔드 POST /api/v1/analyses/email 요청·응답 타입
// backend/app/schemas/analysis.py 와 동일한 계약을 유지한다.

export type TargetCountry = "US" | "JP" | "CN";
export type AnalysisCategory = "vocabulary" | "tone" | "taboo" | "manners";
export type IssueSeverity = "low" | "medium" | "high";

export interface EmailAnalysisRequest {
  text: string;
  target_country: TargetCountry;
  language?: string;
  source?: string;
  mode?: "manual" | "automatic";
  client_request_id?: string;
}

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

export interface AnalysisScores {
  vocabulary: number;
  tone: number;
  taboo: number;
  manners: number;
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
