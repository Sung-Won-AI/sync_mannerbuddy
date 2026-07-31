import type { AnalysisScores, MeetingAnalysisResponse, TargetCountry } from "../shared/meetingTypes";
import { TranscriptLine } from "./TranscriptLine";

interface MeetingReviewProps {
  response: MeetingAnalysisResponse;
  transcript: string;
  counterpart: string;
  date: string;
  targetCountry: TargetCountry;
  onReset: () => void;
}

const COUNTRY_FLAG: Record<TargetCountry, string> = { US: "🇺🇸", JP: "🇯🇵", CN: "🇨🇳" };
const COUNTRY_NAME: Record<TargetCountry, string> = { US: "미국", JP: "일본", CN: "중국" };

const SCORE_LABEL: Record<keyof AnalysisScores, string> = {
  tone: "어조",
  taboo: "금기 표현",
  manners: "매너·구조",
  vocabulary: "어휘"
};

function temperatureTone(value: number): string {
  if (value >= 75) return "cool";
  if (value >= 50) return "warm";
  return "hot";
}

function linesWithOffsets(transcript: string) {
  let cursor = 0;
  return transcript.split("\n").map((line) => {
    const start = cursor;
    cursor += line.length + 1;
    return { line, start };
  });
}

export function MeetingReview({
  response,
  transcript,
  counterpart,
  date,
  targetCountry,
  onReset
}: MeetingReviewProps) {
  const lines = linesWithOffsets(transcript);
  const who = counterpart.trim().length > 0 ? counterpart.trim() : `${COUNTRY_NAME[targetCountry]} 파트너`;

  return (
    <div className="meeting-review">
      <header className="meeting-review__header">
        <div>
          <div className="meeting-review__eyebrow">회의록 리뷰 · 분석 완료</div>
          <h1 className="meeting-review__title">{response.title || "제목 없는 회의"}</h1>
          <p className="meeting-review__meta">
            {date} · {who}와의 회의
          </p>
        </div>
        <button className="meeting-review__reset" onClick={onReset}>
          새 회의록 분석하기
        </button>
      </header>

      <div className="meeting-review__top">
        <div className="score-panel">
          <div className="score-panel__primary">
            <span className={`score-panel__temp score-panel__temp--${temperatureTone(response.meeting_temperature)}`}>
              {response.meeting_temperature}°
            </span>
            <span className="score-panel__primary-label">매너 온도</span>
          </div>
          <div className="score-panel__grid">
            {(Object.keys(SCORE_LABEL) as (keyof AnalysisScores)[]).map((key) => (
              <div className="score-panel__cell" key={key}>
                <span className="score-panel__cell-value">{response.scores[key]}</span>
                <span className="score-panel__cell-label">{SCORE_LABEL[key]}</span>
              </div>
            ))}
          </div>
          {response.flow.length > 0 && (
            <div className="score-panel__flow" aria-hidden="true">
              {response.flow.map((point) => (
                <span
                  key={point.segment}
                  className="score-panel__flow-bar"
                  style={{ height: `${Math.max(12, point.temperature)}%` }}
                  title={`${point.label}: ${point.temperature}°`}
                />
              ))}
            </div>
          )}
        </div>

        <div className="insight-card">
          <div className="insight-card__flag">{COUNTRY_FLAG[targetCountry]}</div>
          <div>
            <h2 className="insight-card__title">{who}과의 회의 매너 요약</h2>
            <p className="insight-card__body">{response.summary}</p>
          </div>
        </div>
      </div>

      <div className="transcript-panel">
        {lines.map(({ line, start }, index) => (
          <TranscriptLine key={index} line={line} lineStart={start} issues={response.issues} />
        ))}
      </div>

      <div className="meeting-review__footer">
        <div className="footer-card">
          <h3>핵심 포인트</h3>
          <ul>
            {response.key_points.map((point, index) => (
              <li key={index}>{point}</li>
            ))}
          </ul>
        </div>
        <div className="footer-card">
          <h3>액션 아이템</h3>
          <ul>
            {response.action_items.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
