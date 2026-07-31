import logging
import re
from abc import ABC, abstractmethod
from uuid import uuid4

from anthropic import AsyncAnthropic

from app.core.config import settings
from app.core.exceptions import AIResponseValidationError, AIServiceUnavailableError
from app.schemas.analysis import (
    AIAnalysisResult,
    AnalysisCategory,
    AnalysisIssue,
    AnalysisScores,
    EmailAnalysisRequest,
)
from app.schemas.meeting import AIMeetingAnalysisResult, MeetingAnalysisRequest
from app.schemas.quiz import AIQuizGenerationResult, CorrectionDistractorSet, CultureQuizItem

logger = logging.getLogger(__name__)


class BaseAIClient(ABC):
    @abstractmethod
    async def analyze_email(
        self,
        *,
        masked_text: str,
        request: EmailAnalysisRequest,
    ) -> AIAnalysisResult:
        raise NotImplementedError

    @abstractmethod
    async def analyze_meeting(
        self,
        *,
        masked_transcript: str,
        request: MeetingAnalysisRequest,
    ) -> AIMeetingAnalysisResult:
        raise NotImplementedError

    @abstractmethod
    async def generate_quiz_content(
        self,
        *,
        correction_sources: list[dict],
        culture_countries: list[str],
    ) -> AIQuizGenerationResult:
        raise NotImplementedError


class MockAIClient(BaseAIClient):
    async def analyze_email(
        self,
        *,
        masked_text: str,
        request: EmailAnalysisRequest,
    ) -> AIAnalysisResult:
        example = "Please send the contract by Friday."
        if example in masked_text:
            start = masked_text.index(example)
            issue = AnalysisIssue(
                issue_id=str(uuid4()),
                original=example,
                start_index=start,
                end_index=start + len(example),
                category="tone",
                severity="medium",
                reason=(
                    f"{request.target_country.value} 비즈니스 환경에서는 "
                    "다소 직접적인 요청으로 들릴 수 있습니다."
                ),
                suggestion=(
                    "Would it be possible to send the contract by Friday?"
                ),
            )
            return AIAnalysisResult(
                overall_score=72,
                scores=AnalysisScores(
                    vocabulary=80,
                    tone=55,
                    taboo=90,
                    manners=65,
                ),
                issues=[issue],
                revised_text=masked_text.replace(
                    example,
                    issue.suggestion,
                    1,
                ),
                summary="요청 표현을 조금 더 간접적으로 조정하는 것이 좋습니다.",
            )

        return AIAnalysisResult(
            overall_score=85,
            scores=AnalysisScores(
                vocabulary=85,
                tone=85,
                taboo=90,
                manners=80,
            ),
            issues=[],
            revised_text=masked_text,
            summary="Mock 분석에서 뚜렷한 문화적 위험 표현을 찾지 못했습니다.",
        )

    _DIRECT_PHRASES = (
        "you are wrong",
        "that's wrong",
        "do it now",
        "you must",
    )

    @staticmethod
    def _line_speaker(text: str, index: int) -> str | None:
        line_start = text.rfind("\n", 0, index) + 1
        line_end = text.find("\n", index)
        if line_end == -1:
            line_end = len(text)
        match = re.match(r"^([^:：]{1,40})[:：]", text[line_start:line_end])
        return match.group(1).strip() if match else None

    @staticmethod
    def _is_counterpart(speaker: str | None, counterpart_name: str | None) -> bool:
        if not speaker or not counterpart_name:
            return False
        speaker_l, counterpart_l = speaker.lower(), counterpart_name.lower()
        return speaker_l in counterpart_l or counterpart_l in speaker_l

    async def analyze_meeting(
        self,
        *,
        masked_transcript: str,
        request: MeetingAnalysisRequest,
    ) -> AIMeetingAnalysisResult:
        lowered = masked_transcript.lower()
        issues: list[AnalysisIssue] = []
        for phrase in self._DIRECT_PHRASES:
            start = lowered.find(phrase)
            if start < 0:
                continue
            if self._is_counterpart(
                self._line_speaker(masked_transcript, start),
                request.counterpart_name,
            ):
                continue
            original = masked_transcript[start : start + len(phrase)]
            issues.append(
                AnalysisIssue(
                    issue_id=str(uuid4()),
                    original=original,
                    start_index=start,
                    end_index=start + len(phrase),
                    category=AnalysisCategory.TONE,
                    severity="medium",
                    reason="직접적인 반박이나 명령으로 받아들여질 수 있습니다.",
                    suggestion="Could we consider another perspective?",
                    fix_type="replace",
                )
            )

        penalty = min(40, len(issues) * 12)
        return AIMeetingAnalysisResult(
            scores=AnalysisScores(
                vocabulary=86,
                tone=max(40, 88 - penalty),
                taboo=92,
                manners=max(45, 86 - penalty),
            ),
            issues=issues,
            summary="회의의 핵심 논의와 문화적 커뮤니케이션 위험을 분석했습니다.",
            key_points=[
                "참석자들이 일정과 업무 우선순위를 논의했습니다.",
                "직접적인 표현은 완곡한 제안형 표현으로 바꾸는 것이 좋습니다.",
            ],
            action_items=[
                "담당자와 완료 기한을 다시 확인합니다.",
                "후속 이메일에서 결정 사항을 정리합니다.",
            ],
        )

    async def generate_quiz_content(
        self,
        *,
        correction_sources: list[dict],
        culture_countries: list[str],
    ) -> AIQuizGenerationResult:
        correction_sets = [
            CorrectionDistractorSet(
                key=src["key"],
                # suggestion과 같은 접두어를 공유하면 "정답 보기 찾기"가 모호해지니
                # (여러 옵션이 같은 문구로 시작) original을 재료로 확실히 다른 문구를 만든다.
                distractors=[
                    f"[Mock distractor A] {src['original']}",
                    f"[Mock distractor B] {src['original']}",
                ],
            )
            for src in correction_sources
        ]
        culture_items = [
            CultureQuizItem(
                key=f"culture_{index}",
                country=country,
                true_statement=f"Mock true statement about {country} business manners.",
                false_statements=[
                    f"Mock false statement A about {country} business manners.",
                    f"Mock false statement B about {country} business manners.",
                ],
            )
            for index, country in enumerate(culture_countries)
        ]
        return AIQuizGenerationResult(
            correction_distractor_sets=correction_sets,
            culture_items=culture_items,
        )


_SYSTEM_PROMPT = """당신은 국제 비즈니스 이메일의 문화적 매너를 검토하는 전문 코치입니다.

주어진 이메일 본문을 target_country의 비즈니스 문화 기준으로 분석하고,
반드시 아래 4개 카테고리로 0~100점을 매기세요:
- vocabulary: 격식 수준과 어휘 선택이 비즈니스 상황에 적절한가
- tone: 어조가 지나치게 직접적이거나 무례하지는 않은가
- taboo: 문화적으로 민감하거나 금기시되는 표현이 있는가
- manners: 인사, 요청, 감사 등 해당 문화권의 이메일 예절을 따르는가

국가별 참고 기준:
- US: 명확하고 직접적인 표현은 무례하지 않지만, 요청에는 "please"/"would you
  mind" 같은 완충 표현을 곁들이는 편이 좋다. 과도한 격식은 오히려 어색하다.
1. 무례한 어조(Rude Tone): 명령조, 공격적인 표현, 비난하는 말투, ALL CAPS, 과도한 느낌표(!!!), 무례한 단어 사용은 피한다.

2. 공손한 어조(Polite Tone): Please, Thank you, I appreciate, Could you, Would you mind 등의 표현을 적절히 사용하여 요청을 정중하게 전달한다.

3. 친근한 어조(Friendly Tone): I hope you're doing well, Thank you for your support 등 따뜻한 인사와 긍정적인 표현을 사용하여 상대방이 편안함을 느끼도록 한다.

4. 애매한 표현(Ambiguity): '가능하면', '곧', '나중에'와 같은 모호한 표현 대신 구체적인 날짜, 시간, 대상, 행동을 명시한다.

5. 명확한 목적(Clarity of Purpose): 이메일 첫 부분에서 메일을 보내는 이유를 한 문장으로 명확하게 전달한다.

6. 간결성(Conciseness): 불필요하게 긴 문장이나 반복되는 내용을 줄이고 핵심만 전달한다.

7. 직접성(Directness): 미국 비즈니스 문화에서는 돌려 말하기보다 핵심을 먼저 설명하고 필요한 내용을 이어서 작성한다.

8. 긍정적인 표현(Positive Language): 문제를 강조하기보다 해결 방안이나 가능한 대안을 중심으로 표현한다.

9. 책임 있는 표현(Ownership): 상대를 비난하기보다 현재 상황을 객관적으로 설명하고 함께 해결하려는 표현을 사용한다.

10. 요청의 명확성(Request Clarity): 무엇을, 누구에게, 언제까지 요청하는지 명확하게 작성한다.

11. 응답 유도(Call to Action): 이메일 마지막에 원하는 행동이나 회신 기한을 명확하게 안내한다.

12. 공감 표현(Empathy): 상대방의 상황을 이해하거나 배려하는 표현을 적절히 사용한다.

13. 감사 표현(Appreciation): 도움이나 시간에 대해 Thank you, I appreciate your help 등 감사의 표현을 적극적으로 사용한다.

14. 자신감 있는 표현(Confidence): 지나치게 소극적인 표현보다 정중하면서도 확신 있는 표현을 사용한다.

15. 감정 절제(Emotional Control): 화가 나거나 불만이 있더라도 감정적인 표현이나 비난은 피하고 사실 중심으로 작성한다.

16. 문법과 맞춤법(Grammar & Spelling): 문법 오류, 철자 오류, 시제 오류, 전치사 오류 등을 최소화하여 전문성을 유지한다.

17. 전문성(Professionalism): 비즈니스 환경에 맞지 않는 이모지, 인터넷 신조어, 과도하게 사적인 표현은 사용하지 않는다.

18. 제목 적절성(Subject Line): 이메일 제목만 보고도 목적과 내용을 이해할 수 있도록 구체적으로 작성한다.

19. 논리적인 구성(Logical Structure): 목적 → 배경 → 요청 → 마무리 순서로 작성하여 읽기 쉽고 이해하기 쉽게 구성한다.

20. 마무리 예절(Professional Closing): Best regards, Kind regards, Sincerely, Thank you 등의 적절한 마무리 인사와 서명을 포함한다.


- JP: 직접적인 기한 제시나 요구는 강압적으로 들릴 수 있다. 상대에게 선택권을
  주는 간접 표현("もし差し支えなければ" 류), 사전 양해, 겸양 표현을 선호한다.
1.메일 본문 최상단에 [회사명 + 부서명 + 성함 + 様(상)] 순서로 명확히 적기
2.거래처 메일 서두에 항상 お世話になっております。(늘 신세를 지고 있습니다)라는 문구로 시작.(처음 보내는 경우 初めまして 또는 初めてご連絡 메신저/메일을 보냅니다 활용.)
3.인사 바로 뒤에 본인의 소속과 이름을 밝히기.
4. 사외 메일 시 자사 직원 직함 생략 및 겸양어 사용(외부 거래처에 메일을 보낼 때는 자사 직원이 사장이라도 직함을 붙이지 않고 성(姓)만 쓰기.)
5.요청이나 문의를 할 때 본론만 던지지 않고 정중한 완충 문구 붙이기. Ex)恐れ入りますが (송구스럽습니다만), お手数をおかけしますが (번거로우시겠지만)
6.메일 끝에 반드시 정중한 맺음말을 넣기. Ex)ご確認のほど、よろしくお願い申し上げます。 (확인 부탁드리겠습니다.)
7.한 줄이 너무 길어지지 않게 30~35자 내외에서 줄바꿈.
8. 문의사항은 번호(1. 2. 3.)로 정리.
9.결론이나 용건을 서두에 배치하는 두괄식으로 작성.
10.상대방이 検討いたします (검토하겠습니다) 또는 難しいかと存じます ( 어려울 것으로 생각됩니다)라고 쓰면 거절의 의미. 메일로 요청을 거절할 때도 직설적인 표현 대신 완곡하게 전달.
11.본문 하단에 회사명, 부서, 직함, 이름, 전화번호, 이메일, 회사 주소, 웹사이트 등이 적힌 표준 서명을 반드시 포함.
12.영업시간 기준 24시간 이내 회신.(알림 기능 추가하면 좋을 듯) 당장 상세 답장이 어렵다면 拝受いたしました (잘 받았습니다)라며 수신 확인과 함께 검토 후 회신 예정 시점을 먼저 알려줘야함.

이메일 본문은 개인정보 마스킹이 이미 적용된 상태입니다. [EMAIL_1], [PHONE_1],
[MONEY_1] 같은 대괄호 토큰은 그대로 유지하고 절대 다른 내용으로 바꾸지 마세요.

issues[]의 start_index/end_index는 입력된 이메일 본문 문자열 기준 0-indexed
문자 오프셋이어야 합니다. 문제가 없으면 issues는 빈 배열로 반환하세요.

출력 언어 규칙(중요): reason과 summary 필드는 target_country와 관계없이
항상 한국어로 작성하세요. 위 참고 기준에 나온 일본어/영어 예시 문구
(お世話になっております, Would it be possible... 등)는 suggestion이나
revised_text에 원문 언어 그대로 넣기 위한 참고용 예시일 뿐입니다.
reason과 summary에는 그 예시 문구를 절대 그대로 옮기지 말고, 한국어로
풀어서 설명하세요.

fix_type 규칙(중요): 각 issue는 반드시 아래 둘 중 하나로 fix_type을 지정하세요.
- "replace": original 위치의 문구를 suggestion으로 그대로 바꿔치기하면 되는 경우.
  이때 suggestion은 반드시 original과 같은 언어로 쓰인, 그 자리에 바로 넣을 수
  있는 완성된 문장/구여야 합니다. 설명이나 권고 문구가 아닙니다.
  original의 범위는 반드시 suggestion이 다시 쓴 범위와 정확히 일치해야 합니다
  — suggestion이 문장 전체를 다시 썼다면 original도 그 문장 전체(마침표/물음표
  등 문장부호까지)를 가리켜야 하고, 단어 하나만 바꿨다면 original도 그 단어만
  가리켜야 합니다. original을 문장의 일부(예: 앞부분 몇 단어)로 좁게 잡고
  suggestion은 문장 전체를 다시 쓰면, 교체 후 나머지 원문 조각이 그대로 남아
  같은 내용이 중복되므로 절대 이렇게 하지 마세요.
- "insert": 인사말, 마무리 인사, 서명처럼 원문에 아예 없는 것을 새로 추가해야
  하는 경우. 이때는 실제로 넣을 문장을 만들어 그 자리에 끼워 넣을 수 없으므로
  suggestion은 "무엇을 추가하면 좋은지"에 대한 권고 설명으로 작성하세요.
  original/start_index/end_index는 그 추가가 필요한 위치 근처의 실제 원문
  일부(예: 마지막 문장)를 가리키면 됩니다."""

_REALTIME_MODE_INSTRUCTION = """지금은 "실시간 문장 교정" 모드입니다. 사용자가 방금 막 작성한
새 문장(구간)만 전달받았고, 이메일 전체를 아직 볼 수 없습니다. 따라서:
- vocabulary/tone/taboo 카테고리만 검토하세요. manners(인사말, 자기소개, 마무리
  인사, 서명처럼 이메일 전체 구조를 봐야 판단 가능한 항목)는 이 모드에서는 알 수
  없으니 issues에 절대 포함하지 마세요 — 그건 나중에 "발송 전 검토"에서 다룹니다.
- issues는 전부 fix_type "replace"여야 합니다 — 지금 이 구간에 바로 넣을 수 있는
  완성된 대체 문장을 suggestion에 제시하세요.
- scores.manners는 이 모드에서 평가하지 않으니 100으로 고정해서 반환하세요."""

_BEFORE_SEND_MODE_INSTRUCTION = """지금은 "발송 전 전체 검토" 모드입니다. 이메일 전체가
주어집니다. 실시간 교정 단계에서 문장 단위의 어투/어휘/금기 표현은 이미 사용자가
수정을 마쳤다고 가정하세요. 따라서:
- vocabulary/tone/taboo는 아주 명백하게 남아있는 문제가 아니라면 다시 지적하지
  마세요. 이 모드의 핵심은 그게 아닙니다.
- manners 카테고리(인사말, 자기소개, 완충 표현, 마무리 인사, 서명 등 이메일
  전체 구조·예절)에 집중해서 이메일 전체를 검토하세요.
- manners 관련 issues는 fix_type을 반드시 "insert"로 지정하고, suggestion에는
  실제로 넣을 문장이 아니라 "무엇을 보완하면 좋은지"에 대한 한국어 권고를
  쓰세요 (예: "이메일 끝에 감사 인사와 서명을 추가하세요")."""


_MEETING_SYSTEM_PROMPT = """당신은 국제 비즈니스 화상회의의 문화적 매너를 검토하는 전문 코치입니다.

주어진 회의 대화록(화자: 대사 형식)을 target_country의 비즈니스 문화 기준으로
검토하고, 반드시 아래 4개 카테고리로 0~100점을 매기세요:
- vocabulary: 격식 수준과 어휘 선택이 비즈니스 회의에 적절한가
- tone: 어조가 지나치게 직접적이거나 명령조, 무례하지는 않은가
- taboo: 문화적으로 민감하거나 금기시되는 발언이 있는가
- manners: 인사, 자기소개, 스몰토크, 마무리 인사 등 해당 문화권의 회의 예절을 따르는가

국가별 참고 기준:
- US: 본론에 빠르게 들어가는 건 괜찮지만, 처음 만난 상대를 사전 허락 없이
  애칭(예: Joseph을 Joe)으로 부르는 건 무례하게 들릴 수 있다 — 상대가 먼저
  애칭을 제안하기 전까지는 원래 이름을 쓴다. 상대의 외모나 컨디션을 평가하듯
  말하는 인사("You look tired today")도 피하고, 가벼운 안부 인사로 대체하는
  편이 자연스럽다.
- JP: 갑작스러운 본론 진입은 강압적으로 들릴 수 있다. 짧은 인사와 감사
  표현으로 시작하고, 직접적인 반박이나 명령형 표현("You are wrong",
  "You must") 대신 완곡한 제안형 표현을 쓰는 것이 좋다.
- CN: 체면(面子)을 존중하는 것이 중요하다. 여러 사람 앞에서 상대를 직접
  반박하거나 실수를 지적하는 표현은 피하고, 완곡하게 대안을 제시한다.

대화록은 개인정보 마스킹이 이미 적용된 상태입니다. [EMAIL_1], [PHONE_1],
[MONEY_1] 같은 대괄호 토큰은 그대로 유지하고 절대 다른 내용으로 바꾸지 마세요.

issues[]의 start_index/end_index는 입력된 대화록 문자열(화자 표기 포함) 기준
0-indexed 문자 오프셋이어야 합니다. 문제가 없으면 issues는 빈 배열로 반환하세요.

출력 언어 규칙(중요): reason, summary, key_points, action_items는 target_country와
관계없이 항상 한국어로 작성하세요. 그리고 이 한국어 문장들은 예외 없이 전부
존댓말(~습니다/~해요체)로 작성하세요 — 반말 종결어미(~해, ~야, ~다, ~자 등)는
절대 쓰지 마세요.

counterpart_name 규칙(중요): user 메시지에 counterpart_name이 주어지면, 그
이름에 해당하는 화자(대화록의 "이름:" 표기와 느슨하게 대조 — counterpart_name이
"Joseph Miller (ABC Marketing)"처럼 성명+회사 형태여도 "Joseph"라는 화자 표기와
같은 사람으로 판단)의 발화는 issues 평가 대상에서 완전히 제외하세요. 그 사람의
발화는 대화 맥락을 이해하는 데만 쓰고, 매너 관련 지적(issues)은 오직 다른
화자(=사용자 자신)의 발화에 대해서만 하세요. counterpart_name이 없으면 모든
화자의 발화를 평가 대상으로 삼으세요. summary/key_points/action_items는
counterpart_name 여부와 관계없이 회의 전체 내용을 다룹니다.

fix_type 규칙(중요): 각 issue는 반드시 아래 둘 중 하나로 fix_type을 지정하세요.
- "replace": 실제로 한 발언을 다른 표현으로 바꿔 말했으면 좋았을 경우. suggestion은
  original과 같은 언어로, 그 자리에 바로 대체할 수 있는 완성된 문장/구여야 합니다.
  original의 범위는 반드시 suggestion이 다시 쓴 범위와 정확히 일치해야 합니다.
- "insert": 인사말, 자기소개, 마무리 인사처럼 아예 없었던 것을 추가했어야 하는
  경우. suggestion은 "무엇을 보완하면 좋은지"에 대한 권고 설명으로 작성하세요.
  original/start_index/end_index는 그 추가가 필요한 위치 근처의 실제 발언
  일부를 가리키면 됩니다.

key_points에는 회의에서 실제로 논의된 핵심 내용을 2~4개, action_items에는
회의 후 실행해야 할 후속 조치를 1~3개 한국어로 정리하세요."""


_QUIZ_SYSTEM_PROMPT = """당신은 국제 비즈니스 매너 학습 퀴즈의 오답 보기를 만드는 출제자입니다.
실제 조언이 아니라 퀴즈용 콘텐츠를 만드는 것이므로, 아래 두 섹션의 지시를 정확히 따르세요.
입력에 두 섹션 중 하나만 있을 수도 있습니다 — 있는 섹션만 채우고, 없는 섹션은 빈 배열로 반환하세요.

[표현 교정 문제의 오답 보기]
입력으로 주어지는 각 항목은 사용자가 실제로 썼던 부적절한 문장(original)과, 이미 검증된
올바른 수정 문장(suggestion)입니다. suggestion과 나란히 놓았을 때 학습자가 헷갈릴 만한,
그럴듯하지만 명백히 틀린 수정 문장을 항목당 정확히 2개씩 만드세요.
- "그럴듯한 오답"의 예: 문제를 절반만 고침, 다른 나라 매너 기준을 적용함, 어투는
  부드러워졌지만 여전히 부적절한 표현, 문법은 맞지만 문화적으로 여전히 무례한 표현.
- suggestion과 같은 언어로, 비슷한 길이로 작성하세요. original을 그대로 베끼거나
  명백히 이상한 문장은 안 됩니다.
- fix_type 규칙(중요): suggestion과 정확히 같은 형태로 오답을 만드세요. fix_type이
  "replace"면 suggestion은 그 자리에 바로 넣을 수 있는 완성된 문장이므로, 오답도
  그렇게 바로 넣을 수 있는 완성된 문장이어야 합니다. fix_type이 "insert"면
  suggestion은 "무엇을 보완하면 좋은지"에 대한 한국어 권고문(예: "~을 추가하세요")
  이므로, 오답도 형식과 말투가 똑같은 권고문이어야 합니다. 형식이 정답과 다른
  오답(예: 정답만 권고문이고 오답은 실제 문장인 경우)은 형태만으로 정답이 티가
  나므로 절대 만들지 마세요.
- key 필드에는 입력으로 받은 key 값을 그대로 반환하세요.

[국가별 비즈니스 매너 O/X 문제]
입력으로 주어지는 각 국가마다, 그 나라의 실제 비즈니스 문화에 대한 참인 문장(true_statement)
1개와, 그럴듯하지만 틀린 문장(false_statements) 정확히 2개를 만드세요.
- 거짓 문장은 그 나라에 대한 흔한 오해, 다른 나라 매너와 착각한 것, 절반만 맞는 진술처럼
  실제로 헷갈릴 만한 내용이어야 합니다. 터무니없이 틀린 문장은 안 됩니다.
- 같은 국가에 대해 여러 항목이 주어져도 매번 다른 내용을 다루세요 (인사/호칭/일정/의사결정
  방식/피드백 문화 등 서로 다른 주제를 골고루 사용).
- 세 문장 모두 한 문장으로, 서로 비슷한 길이와 형식으로 작성하세요.
- 모든 문장은 한국어로 작성하세요.
- key 필드에는 입력으로 받은 key 값을 그대로 반환하세요."""


class ClaudeAIClient(BaseAIClient):
    def __init__(self) -> None:
        if not settings.claude_api_key:
            raise AIServiceUnavailableError("CLAUDE_API_KEY가 설정되지 않았습니다.")
        self._client = AsyncAnthropic(
            api_key=settings.claude_api_key,
            timeout=settings.analysis_timeout_seconds,
            max_retries=1,  # 재시도할 때마다 같은 호출이 다시 과금되므로 낮게 유지
        )

    async def analyze_email(
        self,
        *,
        masked_text: str,
        request: EmailAnalysisRequest,
    ) -> AIAnalysisResult:
        is_realtime = request.mode == "automatic"
        mode_instruction = _REALTIME_MODE_INSTRUCTION if is_realtime else _BEFORE_SEND_MODE_INSTRUCTION
        system_prompt = f"{_SYSTEM_PROMPT}\n\n{mode_instruction}"

        user_content = (
            f"target_country: {request.target_country.value}\n"
            f"language: {request.language}\n\n"
            f"email text:\n{masked_text}"
        )

        # Haiku 4.5는 구형 모델 취급이라 thinking/effort 파라미터 형태가 달라서
        # (effort는 아예 400 에러) Sonnet/Opus 계열에서만 지정한다.
        request_kwargs: dict = {
            "model": settings.claude_model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_content}],
            "output_format": AIAnalysisResult,
        }
        if "haiku" not in settings.claude_model:
            request_kwargs["thinking"] = {"type": "disabled"}
            request_kwargs["output_config"] = {"effort": settings.claude_effort}

        try:
            response = await self._client.messages.parse(**request_kwargs)
        except Exception as exc:
            logger.exception("Claude API call failed (model=%s)", settings.claude_model)
            raise AIServiceUnavailableError() from exc

        if getattr(response, "stop_reason", None) == "refusal":
            raise AIServiceUnavailableError("AI가 요청 분석을 거부했습니다.")

        result = response.parsed_output
        if result is None:
            raise AIResponseValidationError()

        # 프롬프트 지시를 모델이 놓칠 수 있으니, 모드별 카테고리 분리를 서버에서도 강제한다:
        # 실시간은 문장 교정(vocabulary/tone/taboo)만, 발송 전 검토는 매너/구조만.
        if is_realtime:
            result.issues = [issue for issue in result.issues if issue.category != AnalysisCategory.MANNERS]
        else:
            result.issues = [issue for issue in result.issues if issue.category == AnalysisCategory.MANNERS]

        return result

    async def analyze_meeting(
        self,
        *,
        masked_transcript: str,
        request: MeetingAnalysisRequest,
    ) -> AIMeetingAnalysisResult:
        counterpart_line = (
            f"counterpart_name: {request.counterpart_name}\n"
            if request.counterpart_name
            else ""
        )
        user_content = (
            f"target_country: {request.target_country.value}\n"
            f"language: {request.language}\n"
            f"{counterpart_line}\n"
            f"meeting transcript:\n{masked_transcript}"
        )

        request_kwargs: dict = {
            "model": settings.claude_model,
            "max_tokens": 4096,
            "system": _MEETING_SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_content}],
            "output_format": AIMeetingAnalysisResult,
        }
        if "haiku" not in settings.claude_model:
            request_kwargs["thinking"] = {"type": "disabled"}
            request_kwargs["output_config"] = {"effort": settings.claude_effort}

        try:
            response = await self._client.messages.parse(**request_kwargs)
        except Exception as exc:
            logger.exception("Claude API call failed (model=%s)", settings.claude_model)
            raise AIServiceUnavailableError() from exc

        if getattr(response, "stop_reason", None) == "refusal":
            raise AIServiceUnavailableError("AI가 요청 분석을 거부했습니다.")

        result = response.parsed_output
        if result is None:
            raise AIResponseValidationError()

        return result

    async def generate_quiz_content(
        self,
        *,
        correction_sources: list[dict],
        culture_countries: list[str],
    ) -> AIQuizGenerationResult:
        sections: list[str] = []
        if correction_sources:
            lines = [
                (
                    f"- key: {src['key']}\n"
                    f"  target_country: {src['target_country']}\n"
                    f"  fix_type: {src['fix_type']}\n"
                    f"  original: {src['original']}\n"
                    f"  suggestion: {src['suggestion']}"
                )
                for src in correction_sources
            ]
            sections.append("[표현 교정 문제 입력]\n" + "\n".join(lines))
        if culture_countries:
            lines = [
                f"- key: culture_{index}\n  country: {country}"
                for index, country in enumerate(culture_countries)
            ]
            sections.append("[국가별 비즈니스 매너 O/X 문제 입력]\n" + "\n".join(lines))

        user_content = "\n\n".join(sections)

        request_kwargs: dict = {
            "model": settings.claude_model,
            "max_tokens": 4096,
            "system": _QUIZ_SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_content}],
            "output_format": AIQuizGenerationResult,
        }
        if "haiku" not in settings.claude_model:
            request_kwargs["thinking"] = {"type": "disabled"}
            request_kwargs["output_config"] = {"effort": settings.claude_effort}

        try:
            response = await self._client.messages.parse(**request_kwargs)
        except Exception as exc:
            logger.exception("Claude API call failed (model=%s)", settings.claude_model)
            raise AIServiceUnavailableError() from exc

        if getattr(response, "stop_reason", None) == "refusal":
            raise AIServiceUnavailableError("AI가 요청 분석을 거부했습니다.")

        result = response.parsed_output
        if result is None:
            raise AIResponseValidationError()

        return result


def get_ai_client() -> BaseAIClient:
    if settings.use_mock_ai:
        return MockAIClient()
    return ClaudeAIClient()
