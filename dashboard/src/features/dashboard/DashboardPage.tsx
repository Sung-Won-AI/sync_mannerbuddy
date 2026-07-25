// [기능 3] 대시보드
// 금주 사용자의 수정 표현 개수, 언어, 비즈니스 매너 온도를 표시한다.

import { useEffect, useState } from "react";

interface WeeklySummary {
  correctedCount: number;
  languages: string[];
  mannerTemperature: number; // 0-100
}

interface WeeklySummaryApiResponse {
  corrected_count: number;
  languages: string[];
  manner_temperature: number;
}

export function DashboardPage() {
  const [summary, setSummary] = useState<WeeklySummary | null>(null);

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_BASE_URL}/api/dashboard/weekly-summary`)
      .then((res) => res.json())
      .then((data: WeeklySummaryApiResponse) =>
        setSummary({
          correctedCount: data.corrected_count,
          languages: data.languages,
          mannerTemperature: data.manner_temperature
        })
      )
      .catch((error) => console.error("주간 요약을 불러오지 못했습니다.", error));
  }, []);

  return (
    <main style={{ padding: 24 }}>
      <h1>이번 주 요약</h1>
      {summary ? (
        <ul>
          <li>수정한 표현 수: {summary.correctedCount}</li>
          <li>사용 언어: {summary.languages.join(", ")}</li>
          <li>비즈니스 매너 온도: {summary.mannerTemperature}°</li>
        </ul>
      ) : (
        <p>데이터를 불러오는 중입니다...</p>
      )}
    </main>
  );
}
