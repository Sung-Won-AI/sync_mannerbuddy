import type { EmailAnalysisRequest, EmailAnalysisResponse } from "./analysisTypes";

export interface AnalyzeEmailMessage {
  type: "ANALYZE_EMAIL";
  payload: EmailAnalysisRequest;
}

export type AnalyzeEmailResult =
  | { ok: true; data: EmailAnalysisResponse }
  | { ok: false; error: string };
