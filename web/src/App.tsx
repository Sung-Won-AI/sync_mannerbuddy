import { useState } from "react";
import { MeetingForm, type MeetingFormValues } from "./components/MeetingForm";
import { MeetingReview } from "./components/MeetingReview";
import { DashboardPage } from "./components/DashboardPage";
import { QuizPage } from "./components/QuizPage";
import { analyzeMeeting } from "./lib/api";
import type { MeetingAnalysisResponse } from "./shared/meetingTypes";

type Page = "meeting" | "dashboard" | "quiz";

const NAV_ITEMS: { page: Page; label: string }[] = [
  { page: "dashboard", label: "대시보드" },
  { page: "meeting", label: "회의록 리뷰" },
  { page: "quiz", label: "퀴즈" }
];

type MeetingViewState =
  | { status: "form" }
  | { status: "loading"; values: MeetingFormValues }
  | { status: "result"; values: MeetingFormValues; response: MeetingAnalysisResponse }
  | { status: "error"; values: MeetingFormValues; message: string };

export function App() {
  const [page, setPage] = useState<Page>("dashboard");
  const [meetingState, setMeetingState] = useState<MeetingViewState>({ status: "form" });

  async function handleMeetingSubmit(values: MeetingFormValues) {
    setMeetingState({ status: "loading", values });
    try {
      const response = await analyzeMeeting({
        transcript: values.transcript,
        target_country: values.targetCountry,
        title: values.title || undefined,
        counterpart_name: values.counterpart || undefined
      });
      setMeetingState({ status: "result", values, response });
    } catch (error) {
      setMeetingState({
        status: "error",
        values,
        message: error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다."
      });
    }
  }

  return (
    <div className="app-root">
      <nav className="app-nav">
        <span className="app-nav__brand">Manner Buddy</span>
        <div className="app-nav__items">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.page}
              type="button"
              className={`app-nav__item${page === item.page ? " app-nav__item--active" : ""}`}
              onClick={() => setPage(item.page)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </nav>

      {page === "dashboard" && <DashboardPage onGoToQuiz={() => setPage("quiz")} />}

      {page === "meeting" &&
        (meetingState.status === "result" ? (
          <MeetingReview
            response={meetingState.response}
            transcript={meetingState.values.transcript}
            counterpart={meetingState.values.counterpart}
            date={meetingState.values.date}
            targetCountry={meetingState.values.targetCountry}
            onReset={() => setMeetingState({ status: "form" })}
          />
        ) : (
          <div className="app-shell">
            <MeetingForm onSubmit={handleMeetingSubmit} submitting={meetingState.status === "loading"} />
            {meetingState.status === "error" && (
              <p className="app-shell__error" role="alert">
                {meetingState.message}
              </p>
            )}
          </div>
        ))}

      {page === "quiz" && <QuizPage />}
    </div>
  );
}
