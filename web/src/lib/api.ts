import type {
  ApiErrorResponse,
  MeetingAnalysisRequest,
  MeetingAnalysisResponse
} from "../shared/meetingTypes";

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
