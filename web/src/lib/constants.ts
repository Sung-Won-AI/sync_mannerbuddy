// 회의록 리뷰/대시보드 화면이 공유하는 국가·카테고리 표기, 매너 온도 등급.

import type { AnalysisScores, TargetCountry } from "../shared/meetingTypes";
import cnFlag from "../assets/flags/cn.svg";
import jpFlag from "../assets/flags/jp.svg";
import usFlag from "../assets/flags/us.svg";

// 국기 이모지는 폰트/OS에 따라 "US"/"JP" 같은 지역 코드 텍스트로 깨져 보이는
// 경우가 있어(특히 헤드리스/일부 Windows 환경), 실제 이미지 파일을 쓴다.
export const COUNTRY_FLAG: Record<TargetCountry, string> = { US: usFlag, JP: jpFlag, CN: cnFlag };
export const COUNTRY_NAME: Record<TargetCountry, string> = { US: "미국", JP: "일본", CN: "중국" };

// score-panel/dashboard 양쪽에서 같은 순서로 렌더링해 화면 간 통일감을 준다.
export const CATEGORY_LABEL: Record<keyof AnalysisScores, string> = {
  tone: "어조",
  taboo: "금기 표현",
  manners: "매너·구조",
  vocabulary: "어휘"
};

export type TemperatureTone = "cool" | "warm" | "hot";

// 매너 온도 등급 — 색은 상태(양호/보통/위험)를 나타내므로 값 구간에 따라 바뀐다.
// 카테고리 막대처럼 "이름이 있는 항목"과 달리, 이 값 하나만 상태색을 쓴다.
export function temperatureTone(value: number): TemperatureTone {
  if (value >= 75) return "cool";
  if (value >= 50) return "warm";
  return "hot";
}
