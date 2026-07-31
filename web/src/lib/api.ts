import type {
  ApiErrorResponse,
  MeetingAnalysisRequest,
  MeetingAnalysisResponse
} from "../shared/meetingTypes";
import type { DashboardSummary } from "../shared/dashboardTypes";
import type { QuizAnswerResponse, QuizSetResponse } from "../shared/quizTypes";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function analyzeMeeting(
  payload: MeetingAnalysisRequest
): Promise<MeetingAnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/meetings/transcript`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as ApiErrorResponse | null;
    throw new Error(body?.error?.message ?? `분석 요청이 실패했습니다 (${response.status}).`);
  }

  return (await response.json()) as MeetingAnalysisResponse;
}

export async function fetchDashboard(periodDays: number): Promise<DashboardSummary> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/dashboard/summary?period_days=${periodDays}`
  );

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as ApiErrorResponse | null;
    throw new Error(body?.error?.message ?? `대시보드를 불러오지 못했습니다 (${response.status}).`);
  }

  return (await response.json()) as DashboardSummary;
}

export async function fetchQuiz(limit: number): Promise<QuizSetResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/quizzes?limit=${limit}`);

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as ApiErrorResponse | null;
    throw new Error(body?.error?.message ?? `퀴즈를 불러오지 못했습니다 (${response.status}).`);
  }

  return (await response.json()) as QuizSetResponse;
}

export async function answerQuiz(
  questionId: string,
  optionId: string
): Promise<QuizAnswerResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/quizzes/${questionId}/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ option_id: optionId })
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as ApiErrorResponse | null;
    throw new Error(body?.error?.message ?? `답변 제출에 실패했습니다 (${response.status}).`);
  }

  return (await response.json()) as QuizAnswerResponse;
}
