import { useEffect, useState } from "react";
import { answerQuiz, fetchQuiz } from "../lib/api";
import type { QuizAnswerResponse, QuizSetResponse } from "../shared/quizTypes";

type QuizState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | {
      status: "playing" | "finished";
      quiz: QuizSetResponse;
      index: number;
      results: Record<string, QuizAnswerResponse>;
    };

const LIMIT = 5;

function loadQuiz(): Promise<QuizState> {
  return fetchQuiz(LIMIT).then(
    (quiz): QuizState => ({ status: "playing", quiz, index: 0, results: {} }),
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

  const { quiz, index, results } = state;

  if (state.status === "finished") {
    const answered = Object.values(results);
    const correctCount = answered.filter((r) => r.correct).length;
    const totalScore = answered.reduce((sum, r) => sum + r.score_awarded, 0);

    return (
      <div className="quiz-page">
        <div className="quiz-summary">
          <span className="quiz-summary__eyebrow">복습 완료</span>
          <h1 className="quiz-summary__title">
            {quiz.questions.length}문제 중 {correctCount}개 맞혔어요
          </h1>
          <p className="quiz-summary__score">획득 점수 {totalScore}점</p>
          <button type="button" className="quiz-summary__restart" onClick={restart}>
            다시 풀기
          </button>
        </div>
      </div>
    );
  }

  const question = quiz.questions[index];
  const result = results[question.id];

  function handleSelect(optionId: string) {
    if (result) return; // 이미 답변한 문제는 다시 제출하지 않는다.
    answerQuiz(question.id, optionId)
      .then((answer) => {
        setState((prev) =>
          prev.status === "playing"
            ? { ...prev, results: { ...prev.results, [question.id]: answer } }
            : prev
        );
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
        <span className="quiz-page__eyebrow">이번 기간 표현 복습하기</span>
        <span className="quiz-page__progress">
          {index + 1} / {quiz.questions.length}
        </span>
      </header>

      <div className="quiz-card">
        <span className="quiz-card__category">{question.category}</span>
        <p className="quiz-card__prompt">{question.prompt}</p>

        <div className="quiz-card__options">
          {question.options.map((option) => {
            const isCorrect = result && option.id === result.correct_option_id;
            const stateClass = !result ? "" : isCorrect ? " quiz-card__option--correct" : " quiz-card__option--muted";

            return (
              <button
                key={option.id}
                type="button"
                className={`quiz-card__option${stateClass}`}
                onClick={() => handleSelect(option.id)}
                disabled={Boolean(result)}
              >
                {option.text}
              </button>
            );
          })}
        </div>

        {result && (
          <div className={`quiz-card__result${result.correct ? " quiz-card__result--correct" : " quiz-card__result--wrong"}`}>
            <span className="quiz-card__result-label">
              {result.correct ? `정답이에요! +${result.score_awarded}점` : "아쉬워요, 오답이에요."}
            </span>
            <p className="quiz-card__result-explanation">{result.explanation}</p>
            <button type="button" className="quiz-card__next" onClick={goNext}>
              {index + 1 >= quiz.questions.length ? "결과 보기" : "다음 문제"} →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
