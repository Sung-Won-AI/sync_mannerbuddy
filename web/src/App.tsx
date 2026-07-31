import { useState } from "react";
import { MeetingForm, type MeetingFormValues } from "./components/MeetingForm";
import { MeetingReview } from "./components/MeetingReview";
import { analyzeMeeting } from "./lib/api";
import type { MeetingAnalysisResponse } from "./shared/meetingTypes";

type ViewState =
  | { status: "form" }
  | { status: "loading"; values: MeetingFormValues }
  | { status: "result"; values: MeetingFormValues; response: MeetingAnalysisResponse }
  | { status: "error"; values: MeetingFormValues; message: string };

export function App() {
  const [state, setState] = useState<ViewState>({ status: "form" });

  async function handleSubmit(values: MeetingFormValues) {
    setState({ status: "loading", values });
    try {
      const response = await analyzeMeeting({
        transcript: values.transcript,
        target_country: values.targetCountry,
        title: values.title || undefined,
        counterpart_name: values.counterpart || undefined
      });
      setState({ status: "result", values, response });
    } catch (error) {
      setState({
        status: "error",
        values,
        message: error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다."
      });
    }
  }

  if (state.status === "result") {
    return (
      <MeetingReview
        response={state.response}
        transcript={state.values.transcript}
        counterpart={state.values.counterpart}
        date={state.values.date}
        targetCountry={state.values.targetCountry}
        onReset={() => setState({ status: "form" })}
      />
    );
  }

  return (
    <div className="app-shell">
      <MeetingForm
        onSubmit={handleSubmit}
        submitting={state.status === "loading"}
      />
      {state.status === "error" && (
        <p className="app-shell__error" role="alert">
          {state.message}
        </p>
      )}
    </div>
  );
}
