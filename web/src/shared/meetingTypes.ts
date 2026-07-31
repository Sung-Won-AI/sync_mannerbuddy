// 백엔드 app/schemas/meeting.py, app/schemas/analysis.py의 필드명을 그대로 따른다.

export type TargetCountry = "US" | "JP" | "CN";
export type AnalysisCategory = "vocabulary" | "tone" | "taboo" | "manners";
export type IssueSeverity = "low" | "medium" | "high";
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

export interface MeetingAnalysisRequest {
  transcript: string;
  target_country: TargetCountry;
  language?: string;
  title?: string;
  counterpart_name?: string;
  client_request_id?: string;
}

export interface MeetingFlowPoint {
  segment: number;
  temperature: number;
  label: string;
}

export interface MeetingAnalysisResponse {
  analysis_id: string;
  status: string;
  title: string;
  overall_score: number;
  meeting_temperature: number;
  scores: AnalysisScores;
  issues: AnalysisIssue[];
  summary: string;
  key_points: string[];
  action_items: string[];
  flow: MeetingFlowPoint[];
  request_id: string | null;
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
