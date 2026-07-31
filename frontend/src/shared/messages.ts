import type { EmailAnalysisRequest, EmailAnalysisResponse, SuggestionAction } from "./analysisTypes";

export interface AnalyzeEmailMessage {
  type: "ANALYZE_EMAIL";
  payload: EmailAnalysisRequest;
}

export type AnalyzeEmailResult =
  | { ok: true; data: EmailAnalysisResponse }
  | { ok: false; error: string };

export interface SaveActionMessage {
  type: "SAVE_ACTION";
  payload: {
    analysisId: string;
    issueId: string;
    action: SuggestionAction;
  };
}

export type SaveActionResult = { ok: true } | { ok: false; error: string };
