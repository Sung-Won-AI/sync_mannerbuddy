// [기능 4] 복습 & 3분 퀴즈
// 금주에 수정한 표현들을 다시 복습하고, 3분 분량의 퀴즈로 학습을 강화한다.

import { useEffect, useState } from "react";

interface CorrectedExpression {
  id: string;
  original: string;
  corrected: string;
}

export function ReviewPage() {
  const [expressions, setExpressions] = useState<CorrectedExpression[]>([]);

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_BASE_URL}/api/review/weekly-expressions`)
      .then((res) => res.json())
      .then((data: CorrectedExpression[]) => setExpressions(data))
      .catch((error) => console.error("복습 표현을 불러오지 못했습니다.", error));
  }, []);

  return (
    <main style={{ padding: 24 }}>
      <h1>이번 주 복습</h1>
      {expressions.length === 0 ? (
        <p>복습할 표현이 없습니다.</p>
      ) : (
        <ul>
          {expressions.map((e) => (
            <li key={e.id}>
              {e.original} → {e.corrected}
            </li>
          ))}
        </ul>
      )}
      {/* TODO: 3분 퀴즈 컴포넌트 */}
    </main>
  );
}
