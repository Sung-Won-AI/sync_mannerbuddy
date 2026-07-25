// [기능 1] 데모용 목업 교정 데이터
// 백엔드 교정 API가 아직 없어서, UI 검증을 위해 트리거 문구 → 제안 문구를 하드코딩해둔다.
// 원문(trigger/suggested)은 실제 작성 언어(일본어/영어)를 유지하고, reason만 한국어로 설명한다.
// TODO: 백엔드 연동 시 이 배열 대신 /api/email-correction 응답을 사용한다.

export type CorrectionLang = "ja" | "en";

export interface CorrectionSuggestion {
  id: string;
  lang: CorrectionLang;
  trigger: string;
  suggested: string;
  reason: string;
}

export const MOCK_SUGGESTIONS: CorrectionSuggestion[] = [
  {
    id: "ja-deadline-1",
    lang: "ja",
    trigger: "今週金曜日までに数量を教えてください",
    suggested: "恐れ入りますが、今週金曜日頃までに数量をご教示いただけますと幸いです",
    reason: "직접적인 기한 제시보다 완곡한 요청 표현(恐れ入りますが/幸いです)을 쓰면 더 정중하게 전달됩니다."
  },
  {
    id: "ja-asap-1",
    lang: "ja",
    trigger: "早急に返信してください",
    suggested: "お忙しいところ恐縮ですが、ご返信いただけますと幸いです",
    reason: "'早急に'는 다소 강압적으로 느껴질 수 있어 완곡한 요청 표현으로 바꾸는 것이 좋습니다."
  },
  {
    id: "en-deadline-1",
    lang: "en",
    trigger: "Please let me know the quantity by this Friday.",
    suggested: "Could you kindly let me know the quantity by around this Friday, if possible?",
    reason: "직접적인 기한 제시보다 완곡한 요청 표현을 사용하면 더 정중하게 전달됩니다."
  }
];
