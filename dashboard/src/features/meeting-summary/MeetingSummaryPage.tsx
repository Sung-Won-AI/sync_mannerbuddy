// [기능 2] 화상 회의 요약 및 표현 수정
// 회의 개요 + 전반적인 매너 요약을 상단에 먼저 보여주고,
// 회의 내용 중 수정이 필요한 문장만 골라 수정 내용/이유와 함께 아래에 나열한다.

import type { ReactNode } from "react";
import { MOCK_FLAGGED_EXPRESSIONS, MOCK_MANNER_SUMMARY, MOCK_MEETING } from "./mockMeeting";
import "./MeetingSummaryPage.css";

function highlightQuote(original: string, highlighted: string): ReactNode {
  const index = original.indexOf(highlighted);
  if (index === -1) return original;

  return (
    <>
      {original.slice(0, index)}
      <mark>{highlighted}</mark>
      {original.slice(index + highlighted.length)}
    </>
  );
}

export function MeetingSummaryPage() {
  return (
    <main className="mm-page">
      <div className="mm-header">
        <div className="mm-header__icon" aria-hidden="true">
          🎥
        </div>
        <h1 className="mm-header__title">{MOCK_MEETING.title}</h1>
      </div>

      <section className="mm-card mm-info-card">
        <p className="mm-info-card__title">회의록</p>
        <div className="mm-info-card__row">
          <b>날짜:</b>
          {MOCK_MEETING.date}
        </div>
        <div className="mm-info-card__row">
          <b>참가자:</b>
          {MOCK_MEETING.participants.join(", ")}
        </div>
      </section>

      <div className="mm-grid">
        <div className="mm-recording">
          <div className="mm-recording__avatar" aria-hidden="true">
            <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.4">
              <circle cx="12" cy="8" r="4" />
              <path d="M4 20c0-4.4 3.6-7 8-7s8 2.6 8 7" />
            </svg>
          </div>
          <div className="mm-recording__duration">
            <span className="dot" />
            {MOCK_MEETING.durationLabel}
          </div>
          <div className="mm-recording__replay">⟳</div>
          <div className="mm-recording__speaker">{MOCK_MEETING.hostName}</div>
          <div className="mm-recording__audio">🔊</div>
        </div>

        <div className="mm-summary">
          <span className="mm-summary__flag" aria-hidden="true">
            {MOCK_MANNER_SUMMARY.countryFlag}
          </span>
          <p className="mm-summary__title">{MOCK_MANNER_SUMMARY.counterpartLabel}</p>
          <p className="mm-summary__text">{MOCK_MANNER_SUMMARY.content}</p>
        </div>
      </div>

      <h2 className="mm-section-title">수정이 필요한 표현</h2>
      <div className="mm-flagged-list">
        {MOCK_FLAGGED_EXPRESSIONS.map((item) => (
          <article className="mm-card mm-flagged-item" key={item.id}>
            <p className="mm-flagged-item__speaker">{item.speaker}</p>
            <p className="mm-flagged-item__quote">{highlightQuote(item.original, item.highlighted)}</p>
            <div className="mm-flagged-item__suggestion">
              <span className="mm-flagged-item__icon" aria-hidden="true">
                ✎
              </span>
              <span>
                <span className="mm-flagged-item__label">수정 제안</span>
                {item.suggested}
              </span>
            </div>
            <div className="mm-flagged-item__reason">
              <span className="mm-flagged-item__icon" aria-hidden="true">
                💡
              </span>
              <span>
                <span className="mm-flagged-item__label">이유</span>
                {item.reason}
              </span>
            </div>
          </article>
        ))}
      </div>
    </main>
  );
}
