import { useEffect, useState, type CSSProperties } from "react";
import { answerQuiz, fetchQuiz } from "../lib/api";
import { COUNTRY_FLAG } from "../lib/constants";
import type { QuizAnswerResponse, QuizSetResponse } from "../shared/quizTypes";
import type { TargetCountry } from "../shared/meetingTypes";

type QuizState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | {
      status: "playing" | "finished";
      quiz: QuizSetResponse;
      index: number;
      results: Record<string, QuizAnswerResponse>;
      // 화면 표시용 상태라 재시작하면 리셋된다 — 서버에 저장하지 않는다.
      selections: Record<string, string>;
      streak: number;
      bestStreak: number;
    };

const LIMIT = 5;

function loadQuiz(): Promise<QuizState> {
  return fetchQuiz(LIMIT).then(
    (quiz): QuizState => ({
      status: "playing",
      quiz,
      index: 0,
      results: {},
      selections: {},
      streak: 0,
      bestStreak: 0
    }),
    (err: unknown): QuizState => ({
      status: "error",
      message: err instanceof Error ? err.message : "퀴즈를 불러오지 못했습니다."
    })
  );
}

export function QuizPage() {
  const [state, setState] = useState<QuizState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    loadQuiz().then((next) => {
      if (!cancelled) setState(next);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  function restart() {
    setState({ status: "loading" });
    loadQuiz().then(setState);
  }

  if (state.status === "loading") {
    return (
      <div className="quiz-page quiz-page--loading" aria-busy="true">
        불러오는 중...
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div className="quiz-page">
        <p className="app-shell__error" role="alert">
          {state.message}
        </p>
      </div>
    );
  }

  const { quiz, index, results, selections, bestStreak } = state;
  const total = quiz.questions.length;

  if (state.status === "finished") {
    const answered = Object.values(results);
    const correctCount = answered.filter((r) => r.correct).length;
    const totalScore = answered.reduce((sum, r) => sum + r.score_awarded, 0);
    const accuracy = total > 0 ? Math.round((correctCount / total) * 100) : 0;
    const celebrate = accuracy >= 80;

    return (
      <div className="quiz-page">
        <div className="quiz-summary">
          <div className="quiz-summary__burst" aria-hidden="true">
            {celebrate ? "🎉" : "💪"}
          </div>
          <span className="quiz-summary__eyebrow">복습 완료</span>
          <div className="quiz-summary__ring" style={{ "--pct": `${accuracy}%` } as CSSProperties}>
            <span className="quiz-summary__ring-value">{accuracy}%</span>
          </div>
          <h1 className="quiz-summary__title">
            {total}문제 중 {correctCount}개 맞혔어요
          </h1>
          <div className="quiz-summary__stats">
            <div className="quiz-summary__stat">
              <span className="quiz-summary__stat-value">+{totalScore}</span>
              <span className="quiz-summary__stat-label">획득 점수</span>
            </div>
            <div className="quiz-summary__stat">
              <span className="quiz-summary__stat-value">🔥 {bestStreak}</span>
              <span className="quiz-summary__stat-label">최고 연속 정답</span>
            </div>
          </div>
          <button type="button" className="quiz-summary__restart" onClick={restart}>
            다시 풀기
          </button>
        </div>
      </div>
    );
  }

  const question = quiz.questions[index];
  const result = results[question.id];
  const selectedOptionId = selections[question.id];
  const answeredCount = Object.keys(results).length;
  const progressPct = total > 0 ? (answeredCount / total) * 100 : 0;
  const flag = COUNTRY_FLAG[question.country as TargetCountry] ?? "🌐";

  function handleSelect(optionId: string) {
    if (result) return; // 이미 답변한 문제는 다시 제출하지 않는다.
    setState((prev) =>
      prev.status === "playing"
        ? { ...prev, selections: { ...prev.selections, [question.id]: optionId } }
        : prev
    );
    answerQuiz(question.id, optionId)
      .then((answer) => {
        setState((prev) => {
          if (prev.status !== "playing") return prev;
          const nextStreak = answer.correct ? prev.streak + 1 : 0;
          return {
            ...prev,
            results: { ...prev.results, [question.id]: answer },
            streak: nextStreak,
            bestStreak: Math.max(prev.bestStreak, nextStreak)
          };
        });
      })
      .catch((err: unknown) => {
        setState({
          status: "error",
          message: err instanceof Error ? err.message : "답변 제출에 실패했습니다."
        });
      });
  }

  function goNext() {
    setState((prev) => {
      if (prev.status !== "playing") return prev;
      const nextIndex = prev.index + 1;
      return nextIndex >= prev.quiz.questions.length
        ? { ...prev, status: "finished" }
        : { ...prev, index: nextIndex };
    });
  }

  return (
    <div className="quiz-page">
      <header className="quiz-page__header">
        <div className="quiz-page__progress-track" role="progressbar" aria-valuenow={answeredCount} aria-valuemin={0} aria-valuemax={total}>
          <div className="quiz-page__progress-fill" style={{ width: `${progressPct}%` }} />
        </div>
        <div className="quiz-page__meta">
          <span className="quiz-page__count">
            {index + 1} / {total}
          </span>
          {state.streak > 0 && (
            <span className="quiz-page__streak" key={state.streak}>
              🔥 {state.streak}연속
            </span>
          )}
        </div>
      </header>

      <div className={`quiz-card${result ? (result.correct ? " quiz-card--correct" : " quiz-card--wrong") : ""}`}>
        <span className="quiz-card__category">
          <span aria-hidden="true">{flag}</span>
          {question.category}
        </span>
        <p className="quiz-card__prompt">{question.prompt}</p>

        <div className="quiz-card__options">
          {question.options.map((option) => {
            const isCorrectOption = result && option.id === result.correct_option_id;
            const isSelected = option.id === selectedOptionId;
            const isWrongSelection = result && !result.correct && isSelected;

            let stateClass = "";
            if (result) {
              if (isCorrectOption) stateClass = " quiz-card__option--correct";
              else if (isWrongSelection) stateClass = " quiz-card__option--wrong";
              else stateClass = " quiz-card__option--muted";
            }

            return (
              <button
                key={option.id}
                type="button"
                className={`quiz-card__option${stateClass}`}
                onClick={() => handleSelect(option.id)}
                disabled={Boolean(result)}
              >
                <span className="quiz-card__option-text">{option.text}</span>
                {isCorrectOption && (
                  <span className="quiz-card__option-icon" aria-hidden="true">
                    ✓
                  </span>
                )}
                {isWrongSelection && (
                  <span className="quiz-card__option-icon" aria-hidden="true">
                    ✕
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {result && (
          <div className={`quiz-card__result${result.correct ? " quiz-card__result--correct" : " quiz-card__result--wrong"}`}>
            <span className="quiz-card__result-label">
              <span className="quiz-card__result-icon" aria-hidden="true">
                {result.correct ? "🎉" : "😅"}
              </span>
              {result.correct ? `정답이에요! +${result.score_awarded}점` : "아쉬워요, 오답이에요."}
            </span>
            <p className="quiz-card__result-explanation">{result.explanation}</p>
            <button type="button" className="quiz-card__next" onClick={goNext}>
              {index + 1 >= total ? "결과 보기" : "다음 문제"} →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
