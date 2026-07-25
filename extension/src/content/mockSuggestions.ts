// [기능 1] 데모용 목업 교정 데이터
// 백엔드 교정 API가 아직 없어서, UI 검증을 위해 트리거 문구 → 제안 문구를 하드코딩해둔다.
// TODO: 백엔드 연동 시 이 배열 대신 /api/email-correction 응답을 사용한다.

export interface CorrectionSuggestion {
  id: string;
  trigger: string;
  suggested: string;
  reason: string;
}

export const MOCK_SUGGESTIONS: CorrectionSuggestion[] = [
  {
    id: "deadline-1",
    trigger: "이번주 금요일까지 수량을 알려주세요",
    suggested: "가능하시다면 이번 주 금요일경 수량을 알려주시면 감사하겠습니다",
    reason: "직접적인 기한 제시보다 완곡한 요청 표현을 사용하면 더 정중하게 전달됩니다."
  },
  {
    id: "asap-1",
    trigger: "빨리 답장 주세요",
    suggested: "바쁘신 와중에 죄송하지만, 회신 부탁드려도 될까요?",
    reason: "'빨리'와 같은 표현은 다소 강압적으로 느껴질 수 있어 완곡한 요청으로 바꾸는 것이 좋습니다."
  }
];
