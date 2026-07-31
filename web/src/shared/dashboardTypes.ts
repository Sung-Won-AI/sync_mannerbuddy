// 백엔드 app/schemas/dashboard.py의 필드명을 그대로 따른다.

import type { AnalysisScores } from "./meetingTypes";

export interface CountryUsage {
  country: string;
  count: number;
}

export interface CountryInsight {
  country: string;
  top_category: string;
  count: number;
}

export interface FrequentIssue {
  category: string;
  count: number;
}

export interface ScoreTrendPoint {
  date: string;
  average_score: number;
}

export interface DashboardSummary {
  period_days: number;
  total_analyses: number;
  email_analyses: number;
  meeting_analyses: number;
  average_score: number;
  manner_temperature: number;
  scores: AnalysisScores;
  country_usage: CountryUsage[];
  country_insights: CountryInsight[];
  frequent_issues: FrequentIssue[];
  fixed_issues: FrequentIssue[];
  score_trend: ScoreTrendPoint[];
  accepted_suggestions: number;
}
