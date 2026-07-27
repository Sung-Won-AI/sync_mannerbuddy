// [기능 2] 화상 회의 요약 + 표현 수정 데모용 목업 데이터
// 백엔드 교정 API가 아직 없어서 UI 검증용으로 하드코딩해둔다.
// TODO: 백엔드 연동 시 /api/meeting-summary 응답으로 교체

export interface MeetingInfo {
  title: string;
  date: string;
  participants: string[];
  durationLabel: string;
  hostName: string;
}

export interface MannerSummary {
  counterpartLabel: string;
  countryFlag: string;
  content: string;
}

export interface FlaggedExpression {
  id: string;
  speaker: string;
  original: string;
  highlighted: string; // original 안에서 강조할 부분 문자열
  suggested: string;
  reason: string;
}

export const MOCK_MEETING: MeetingInfo = {
  title: "[External] Marketing + Sales",
  date: "2026년 6월 18일",
  participants: ["Seoyun Yang (Manner Buddy)", "Joseph Miller (ABC Marketing)"],
  durationLabel: "24:01",
  hostName: "Joseph Miller"
};

export const MOCK_MANNER_SUMMARY: MannerSummary = {
  counterpartLabel: "Joseph(ABC Marketing)과의 회의 매너 요약",
  countryFlag: "🇺🇸",
  content:
    "아이스브레이킹으로 회의를 잘 시작했지만 호칭 부분에서 실수가 많았어요. 또한 같은 말이라도 한국에서는 배려의 표현으로, 미국에서는 무례한 표현으로 들릴 수 있어요."
};

export const MOCK_FLAGGED_EXPRESSIONS: FlaggedExpression[] = [
  {
    id: "naming-1",
    speaker: "Seoyun",
    original: "Hi, Joe! Nice to finally meet you. How's everything going?",
    highlighted: "Joe",
    suggested: "Hi, Joseph! Nice to finally meet you. How's everything going?",
    reason: "처음 본 사람에게 Joe와 같은 애칭형 이름을 부르는 것은 실례입니다. Joseph으로 부르는 것이 적절해요."
  },
  {
    id: "appearance-1",
    speaker: "Seoyun",
    original: "Great! By the way, you look a little tired today. Did you stay up late?",
    highlighted: "you look a little tired today",
    suggested: "Great! By the way, I hope you're having a great day!",
    reason:
      "한국에서는 배려의 표현일 수 있지만, 미국에서는 상대의 외모나 컨디션을 평가하는 말처럼 들릴 수 있어요. 첫 미팅에서는 \"I hope you're having a great day.\"와 같이 가벼운 안부 인사가 더 자연스럽습니다."
  },
  {
    id: "naming-2",
    speaker: "Seoyun",
    original:
      "So, Joe, I'd like to introduce Manner Buddy, an AI service that helps companies avoid cultural misunderstandings in global business communication.",
    highlighted: "Joe",
    suggested:
      "So, Joseph, I'd like to introduce Manner Buddy, an AI service that helps companies avoid cultural misunderstandings in global business communication.",
    reason: "동일한 이유로, 호칭은 처음 소개받은 대로(Joseph) 일관되게 사용하는 것이 좋습니다."
  }
];
