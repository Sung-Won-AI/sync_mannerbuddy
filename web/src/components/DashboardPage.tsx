import { useEffect, useState } from "react";
import { fetchDashboard } from "../lib/api";
import { COUNTRY_FLAG, COUNTRY_NAME } from "../lib/constants";
import type { CountryInsight, DashboardSummary } from "../shared/dashboardTypes";
import type { TargetCountry } from "../shared/meetingTypes";
import { CategoryBars } from "./CategoryBars";
import { MannerMeter } from "./MannerMeter";

const PERIOD_OPTIONS = [
  { value: 7, label: "최근 7일" },
  { value: 30, label: "최근 30일" }
];

const CATEGORY_INSIGHT: Record<string, (country: string, count: number) => string> = {
  taboo: (country, count) =>
    `${country} 파트너와의 소통에서 금기시되는 표현이 ${count}건 감지됐어요. 문화적으로 민감한 주제는 특히 조심하세요.`,
  tone: (country, count) =>
    `${country} 파트너에게는 다소 직설적인 어조의 표현이 ${count}건 있었어요. 완곡한 표현을 더 써보는 건 어떨까요?`,
  manners: (country, count) =>
    `${country} 파트너와의 소통에서 인사말·마무리 같은 매너 구조가 ${count}건 아쉬웠어요.`,
  vocabulary: (country, count) =>
    `${country} 파트너에게는 격식 있는 어휘 선택이 아쉬운 표현이 ${count}건 있었어요.`
};

// 미국은 top_category/count와 무관하게 항상 이 문구로 고정한다. 일본 등
// 다른 국가는 기존 CATEGORY_INSIGHT 로직을 그대로 쓴다.
const US_FIXED_INSIGHT =
  "미국 파트너에게 캐주얼한 영어를 많이 사용했어요. 좀 더 예의바른 비즈니스 영어를 사용해보는건 어떨까요?";

function insightText(insight: CountryInsight): string {
  if (insight.country === "US") return US_FIXED_INSIGHT;

  const countryName = COUNTRY_NAME[insight.country as TargetCountry] ?? insight.country;
  const template = CATEGORY_INSIGHT[insight.top_category];
  return template
    ? template(countryName, insight.count)
    : `${countryName} 파트너와의 소통에서 개선할 표현이 ${insight.count}건 있었어요.`;
}

interface DashboardPageProps {
  onGoToQuiz: () => void;
}

export function DashboardPage({ onGoToQuiz }: DashboardPageProps) {
  const [periodDays, setPeriodDays] = useState(7);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    fetchDashboard(periodDays)
      .then((data) => {
        if (!cancelled) setSummary(data);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "대시보드를 불러오지 못했습니다.");
      });
    return () => {
      cancelled = true;
    };
  }, [periodDays]);

  if (error) {
    return (
      <div className="dashboard-page">
        <p className="app-shell__error" role="alert">
          {error}
        </p>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="dashboard-page dashboard-page--loading" aria-busy="true">
        불러오는 중...
      </div>
    );
  }

  const hasData = summary.total_analyses > 0;

  return (
    <div className="dashboard-page">
      <header className="dashboard-page__header">
        <div>
          <div className="dashboard-page__eyebrow">Manner Buddy 리포트</div>
          <h1 className="dashboard-page__title">이번 기간 어떤 비즈니스 매너를 배우셨나요?</h1>
        </div>
        <div className="dashboard-page__period" role="group" aria-label="기간 선택">
          {PERIOD_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              className={`dashboard-page__period-btn${
                option.value === periodDays ? " dashboard-page__period-btn--active" : ""
              }`}
              onClick={() => setPeriodDays(option.value)}
            >
              {option.label}
            </button>
          ))}
        </div>
      </header>

      {!hasData ? (
        <p className="dashboard-page__empty">이 기간에는 아직 분석 기록이 없어요. 이메일이나 회의록을 분석하면 여기에 통계가 쌓여요.</p>
      ) : (
        <>
          <div className="stat-row">
            <div className="stat-tile">
              <span className="stat-tile__icon" aria-hidden="true">
                📧
              </span>
              <span className="stat-tile__value">{summary.email_analyses}건</span>
              <span className="stat-tile__label">이메일 분석</span>
            </div>
            <div className="stat-tile">
              <span className="stat-tile__icon" aria-hidden="true">
                🎥
              </span>
              <span className="stat-tile__value">{summary.meeting_analyses}건</span>
              <span className="stat-tile__label">회의록 분석</span>
            </div>
            <div className="stat-tile">
              <span className="stat-tile__icon" aria-hidden="true">
                📊
              </span>
              <span className="stat-tile__value">{summary.total_analyses}건</span>
              <span className="stat-tile__label">전체 분석</span>
            </div>
            <div className="stat-tile">
              <span className="stat-tile__icon" aria-hidden="true">
                ✅
              </span>
              <span className="stat-tile__value">{summary.accepted_suggestions}건</span>
              <span className="stat-tile__label">실제로 고친 표현</span>
            </div>
          </div>

          {summary.country_insights.length > 0 && (
            <section>
              <h2 className="dashboard-page__section-title">이번 기간 나의 비즈니스 매너는?</h2>
              <div className="insight-list">
                {summary.country_insights.map((insight) => (
                  <div className="insight-card insight-card--compact" key={insight.country}>
                    <div className="insight-card__flag">
                      {COUNTRY_FLAG[insight.country as TargetCountry] ? (
                        <img
                          src={COUNTRY_FLAG[insight.country as TargetCountry]}
                          alt={`${insight.country} 국기`}
                        />
                      ) : (
                        "🌐"
                      )}
                    </div>
                    <div>
                      <h3 className="insight-card__title">
                        {COUNTRY_NAME[insight.country as TargetCountry] ?? insight.country}
                      </h3>
                      <p className="insight-card__body">{insightText(insight)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          <div className="dashboard-page__bottom">
            <div className="dashboard-card">
              <h2 className="dashboard-card__title">이번 기간 매너 카테고리는?</h2>
              <CategoryBars frequent={summary.frequent_issues} fixed={summary.fixed_issues} />
            </div>

            <div className="dashboard-card">
              <MannerMeter value={summary.manner_temperature} trend={summary.score_trend} />
            </div>

            <div className="dashboard-card dashboard-card--cta">
              <span className="dashboard-card__cta-icon" aria-hidden="true">
                📖
              </span>
              <h2 className="dashboard-card__title">이번 기간 표현 복습하기</h2>
              <p className="dashboard-card__cta-body">실제로 고친 표현들을 퀴즈로 다시 확인해보세요.</p>
              <button type="button" className="dashboard-card__cta-btn" onClick={onGoToQuiz}>
                복습하기 →
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
