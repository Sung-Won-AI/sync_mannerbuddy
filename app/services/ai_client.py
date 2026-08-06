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
    IssueFixType,
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
  mind" 같은 완충 표현을 곁들이는 편이 좋다. 도입부 인사말은 "Dear [이름],"이
  가장 표준적이고 안전한 선택이고 "Hi [이름],"/"Hello [이름],"도 무난하다 —
  "Dear"가 과도하게 격식 있거나 차갑다는 이유로 지적하지 마라. "과도한 격식은
  어색하다"는 기준은 문장 중간의 불필요한 존칭 남발이나 지나치게 딱딱한 어휘
  선택에만 적용하고, 인사말 자체의 격식 수준(Dear vs Hi)은 문제 삼지 마라.
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

출력 언어 규칙(매우 중요, 예외 없음): reason과 summary 필드는 target_country나
이메일 본문이 어떤 언어(영어, 일본어, 중국어 등 무엇이든)로 쓰였는지와 전혀
관계없이 무조건 한국어로만 작성하세요. 이메일 본문 언어에 맞춰
suggestion/original/revised_text가 그 언어(영어/일본어/중국어 등)로 쓰이는 것과는
완전히 별개로, reason과 summary는 어떤 경우에도 예외 없이 한국어입니다 —
"본문이 이 언어니까 설명도 그 언어로 쓰는 게 자연스럽겠다"는 판단은 언어가
무엇이든 항상 틀렸습니다. 위 참고 기준에 나온 일본어/영어 예시 문구
(お世話になっております, Would it be possible... 등)는 suggestion이나
revised_text에 원문 언어 그대로 넣기 위한 참고용 예시일 뿐입니다.
reason과 summary에는 그 예시 문구를 절대 그대로 옮기지 말고, 한국어로
풀어서 설명하세요. 이 한국어 문장들은 예외 없이 전부 존댓말(~습니다/~해요체)로
작성하세요 — 반말 종결어미(~다, ~해, ~야, ~자 등)는 절대 쓰지 마세요. reason은
카드 UI에 좁은 박스로 표시되므로 아무리 길어도 4문장을 넘기지 말고, 왜
문제인지 핵심만 간결하게 쓰세요.

issue 범위 제한(매우 중요, 예외 없음): 하나의 issue가 가리키는 original은
마침표/느낌표/물음표로 끝나는 문장 "하나"를 절대 넘을 수 없습니다. 두 문장이
같은 주제(예: 같은 요청, 같은 협박조 어투)로 논리적으로 이어져 보이더라도,
그 이유로 두 문장을 하나의 original/issue로 묶지 마세요 — 반드시 문장마다
별도의 issue로 쪼개서 반환하세요. 단어/구 하나만 문제라면 그 단어/구만
가리키는 게 더 좋습니다(문장 전체를 가리킬 필요 없음).
나쁜 예(금지 — 두 문장을 하나로 묶음): 원문 "Your quotation is too expensive.
You should reduce the price by at least 20%, or we will find another
supplier." 전체를 original 하나로 잡고 4문장짜리 suggestion 하나로 다시 씀.
좋은 예: 위 원문을 두 개의 issue로 나눔 — issue1 original="Your quotation is
too expensive." (suggestion 1문장), issue2 original="You should reduce the
price by at least 20%, or we will find another supplier." (suggestion 1문장).
이렇게 쪼개면 각 suggestion이 1~2문장으로 짧아져 카드 UI가 늘어나 액션
버튼이 화면 밖으로 잘리는 문제도 함께 방지됩니다.

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
  suggestion은 절대로 사용자에게 무엇을 하라고 지시하는 문장이면 안 됩니다.
  suggestion은 프론트엔드가 original 자리에 그대로 끼워 넣는 "실제 텍스트"이지,
  사람이 읽고 따라야 할 안내문이 아닙니다.
  나쁜 예(금지): original="Hey,", suggestion="Remove this line and continue
  directly with the main request." — 이렇게 지시문을 넣으면 그 지시문 자체가
  이메일 본문에 그대로 삽입되어 버립니다.
  톤/격식이 안 맞는 표현(인사말 포함)은 원칙적으로 삭제가 아니라 어울리는 대체
  표현으로 교체하세요 — 예: original="Hey,", suggestion="Hi Smith," (또는
  "Hello Smith,"). suggestion을 빈 문자열("")로 반환하는 것은 그 문구 자체가
  중복되거나 완전히 불필요해서 자리에 아무것도 넣을 필요가 없는 경우에만 쓰는
  최후의 수단입니다 — "이 문구는 어차피 삭제할 수 있으니까"라는 이유만으로
  빈 문자열을 고르지 말고, 항상 먼저 적절한 대체 표현이 있는지 생각하세요.
- "insert": 인사말, 마무리 인사, 서명처럼 원문에 아예 없는 것을 새로 추가해야
  하는 경우. 이때는 실제로 넣을 문장을 만들어 그 자리에 끼워 넣을 수 없으므로
  suggestion은 "무엇을 추가하면 좋은지"에 대한 권고 설명으로 작성하세요.
  original/start_index/end_index는 삽입이 필요한 위치 "근처의 아무 글자"가
  아니라, 그 위치를 표시하는 데 쓰이는 실제 하이라이트 대상이므로 반드시 원문에
  실제로 존재하는 완전한 한 단어 또는 한 줄 전체를 가리켜야 합니다. 단어를
  중간에서 잘라서 가리키는 것은 절대 금지입니다.
  나쁜 예(금지): 원문이 "Regards,\\nSeoyun Yang"일 때 original="ds," 또는
  original="Seoy" — 단어 중간을 자른 조각을 가리키면 안 됩니다.
  좋은 예: 마무리 인사 뒤에 정식 서명을 추가하라고 권고하려면 original="Seoyun
  Yang"(서명 줄 전체)처럼 온전한 줄을 가리키세요. 인사말 앞에 도입 문장을
  추가하라고 권고하려면 그 인사말 줄 전체(예: original="Dear Mr. Tanaka,")를
  가리키세요.
"""

_REALTIME_MODE_INSTRUCTION = """지금은 "실시간 문장 교정" 모드입니다. 사용자가 방금 막 작성한
새 문장(구간)만 전달받았고, 이메일 전체를 아직 볼 수 없습니다. 따라서:
- vocabulary/tone/taboo 카테고리만 검토하세요. manners(인사말, 자기소개, 마무리
  인사, 서명처럼 이메일 전체 구조를 봐야 판단 가능한 항목)는 이 모드에서는 알 수
  없으니 issues에 절대 포함하지 마세요 — 그건 나중에 "발송 전 검토"에서 다룹니다.
  이 규칙은 category 라벨을 무엇으로 붙이든 내용 자체에 적용됩니다: "서두에
  인사말(예: お世話になっております)이 없다", "자기소개가 없다", "마무리 인사가
  없다" 같은 지적은 vocabulary나 tone으로 분류해서라도 절대 issue로 만들지
  마세요 — 지금 받은 구간이 이메일의 첫 문장인지조차 알 수 없으므로 이런 지적은
  이 모드에서 원천적으로 근거가 없습니다.
- issues는 전부 fix_type "replace"여야 합니다 — 지금 이 구간에 바로 넣을 수 있는
  완성된 대체 문장을 suggestion에 제시하세요. suggestion은 그 구간을 대체할
  문장 "하나"만 담아야 합니다 — 같은 문구를 여러 번 반복하거나, 후보 표현
  여러 개를 줄바꿈으로 나열하거나, 원문에 없던 인사말/사과 문구를 앞에
  덧붙이는 것은 절대 금지입니다(그런 건 위 규칙대로 애초에 issue를 만들지 않아야
  하는 경우입니다). 톤이 안 맞는 인사말(예: "Hey,")도 삭제하지 말고 "Hi Smith,"
  같은 어울리는 대체 표현으로 바꾸세요. 이 모드에서는 "insert"를 쓸 수 없으니,
  정말로 대체할 표현 없이 그 문구 자체를 통째로 없애야만 하는 경우(중복 표현
  등)에 한해서만 suggestion을 빈 문자열("")로 반환하세요.
  (fix_type 규칙의 "replace" 예시 참고)
- scores.manners는 이 모드에서 평가하지 않으니 100으로 고정해서 반환하세요."""

_BEFORE_SEND_MODE_INSTRUCTION = """지금은 "발송 전 전체 검토" 모드입니다. 이메일 전체가
주어집니다. 실시간 교정 단계에서 문장 단위의 어투/어휘/금기 표현은 이미 사용자가
수정을 마쳤다고 가정하세요. 따라서:
- vocabulary/tone/taboo는 아주 명백하게 남아있는 문제가 아니라면 다시 지적하지
  마세요. 이 모드의 핵심은 그게 아닙니다.
- manners 카테고리(인사말, 자기소개, 완충 표현, 마무리 인사, 서명 등 이메일
전체 구조·예절)에 집중해서 이메일 전체를 검토하세요.
- us 메일 구조: [인사말] Dear 이름, To whom it may concern [도입] I hope you are doing well [마무리] Best regards 혹은 Sincerely+발신자 이름
- manners 관련 issues는 fix_type을 반드시 "insert"로 지정하고, suggestion에는
  실제로 넣을 문장이 아니라 "무엇을 보완하면 좋은지"에 대한 한국어 권고를
  쓰세요 (예: "이메일 끝에 감사 인사와 서명을 추가하세요"). "insert" type에서는 "원문 수정하기" 버튼을 눌러도 하이라이트된 문장을 바꾸지 않습니다."""

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

출력 언어 규칙(매우 중요, 예외 없음): reason, summary, key_points, action_items는
target_country나 대화록 언어와 전혀 관계없이 무조건 한국어로만 작성하세요.
대화록이 전부 영어라고 해서 설명도 영어로 쓰면 안 됩니다. 그리고 이 한국어
문장들은 예외 없이 전부
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
  original/start_index/end_index는 그 추가가 필요한 위치를 표시하는 실제
  하이라이트 대상이므로, 대화록에 실제로 존재하는 완전한 한 단어 또는 한 발언
  전체를 가리켜야 합니다. 단어를 중간에서 잘라 가리키는 것은 절대 금지입니다
  (예: "Thanks"를 가리켜야 할 자리에 "nks"만 가리키면 안 됩니다).

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
- 마스킹 토큰 규칙(중요): original/suggestion에 [EMAIL_1], [PHONE_1], [MONEY_1] 같은
  대괄호 토큰이 있으면 오답에도 그 토큰을 그대로 옮기되, "(마스킹된 정보 유지)"처럼
  그 토큰에 대해 설명을 덧붙이지 마세요 — 또한 회사명처럼
  원문에 없는 정보가 필요할 때 [COMPANY_NAME] 같은 새 대괄호 placeholder를 만들어
  내지 마세요 — 그런 정보는 그냥 자연스러운 한국어 단어(예: "회사명")로 서술하거나
  생략하세요. 대괄호 토큰은 오직 입력에 이미 있던 [EMAIL_n]/[PHONE_n]/[MONEY_n]
  뿐이어야 합니다.
- key 필드에는 입력으로 받은 key 값을 그대로 반환하세요.

[국가별 비즈니스 매너 O/X 문제]
입력으로 주어지는 각 국가마다, 그 나라의 실제 비즈니스 문화에 대한 참인 문장(true_statement)
1개와, 그럴듯하지만 틀린 문장(false_statements) 정확히 2개를 만드세요.
- 거짓 문장은 그 나라에 대한 흔한 오해, 다른 나라 매너와 착각한 것, 절반만 맞는 진술처럼
  실제로 헷갈릴 만한 내용이어야 합니다. 터무니없이 틀린 문장은 안 됩니다.
- 같은 국가에 대해 여러 항목이 주어져도 매번 다른 내용을 다루세요 (인사/호칭/일정/의사결정
  방식/피드백 문화 등 서로 다른 주제를 골고루 사용).
- 세 문장 모두 한 문장으로, 서로 비슷한 길이와 형식으로 작성하세요.
- 출력 언어 규칙(매우 중요, 예외 없음): true_statement/false_statements는 country가
  어디든(미국/일본/중국 등 무엇이든) 무조건 한국어로만 작성하세요. country가 JP라고
  해서 일본어로, US라고 해서 영어로 쓰면 안 됩니다 — "그 나라 이야기니까 그 나라
  언어로 쓰는 게 자연스럽겠다"는 판단은 항상 틀렸습니다. 이건 학습자가 한국어로
  읽는 매너 O/X 퀴즈이지, 어학 문제가 아닙니다.
  나쁜 예(금지): country="JP", true_statement="日本では、直接的で明確な指示や要望を
  使うほうが、相手に対する尊重を示すとされています。" — 일본어로 통째로 쓰면 안 됩니다.
  좋은 예: country="JP", true_statement="일본에서는 직접적이고 명확한 지시보다
  완곡한 표현을 쓰는 것이 상대에 대한 존중으로 여겨집니다."
- key 필드에는 입력으로 받은 key 값을 그대로 반환하세요."""



_HANGUL_PATTERN = re.compile(r"[가-힣]")
_LETTER_PATTERN = re.compile(r"[^\W\d_]", re.UNICODE)


def _unescape_literal_newlines(text: str) -> str:
    """모델이 JSON 문자열 안에 실제 개행 대신 리터럴 백슬래시+n 두 글자를 넣는
    과이스케이프 실수가 가끔 있어("\\n"이 화면에 그대로 보임). 진짜 개행 문자는
    이 치환의 대상이 아니므로(파이썬 문자열에서 둘은 별개 문자) 안전하게 되돌릴
    수 있다."""
    return text.replace("\\n", "\n")


def _sanitize_email_result(result: AIAnalysisResult) -> AIAnalysisResult:
    result.summary = _unescape_literal_newlines(result.summary)
    result.revised_text = _unescape_literal_newlines(result.revised_text)
    for issue in result.issues:
        issue.suggestion = _unescape_literal_newlines(issue.suggestion)
        issue.reason = _unescape_literal_newlines(issue.reason)
    return result


def _is_mostly_korean(text: str) -> bool:
    """reason/summary가 통째로 다른 언어로 쓰인 건 아닌지 대략적으로 판정한다.
    프롬프트 지시상 문장 안에서 원문 구절을 짧게 인용하는 건 정상이므로, 전체
    글자 수 대비 한글 비율로 판단한다. 텍스트가 너무 짧으면 판단하지 않고
    통과시켜 오탐을 줄인다."""
    letters = _LETTER_PATTERN.findall(text)
    if len(letters) < 10:
        return True
    hangul = _HANGUL_PATTERN.findall(text)
    return len(hangul) / len(letters) >= 0.4


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

        # reason/summary는 프롬프트로 여러 번 강조해도 가끔 이메일 본문 언어(영어/일본어 등)
        # 그대로 새어나온다. 한 번 더 강하게 재지시해서 재시도한다 — 그래도 실패하면
        # 응답 자체를 막지는 않고(가용성 우선) 원래 결과를 그대로 쓴다.
        if not _is_mostly_korean(result.summary) or any(
            not _is_mostly_korean(issue.reason) for issue in result.issues
        ):
            logger.warning("reason/summary 언어 검증 실패, 재시도합니다 (model=%s)", settings.claude_model)
            retry_kwargs = {
                **request_kwargs,
                "system": system_prompt
                + "\n\n[재시도 안내] 방금 응답에서 reason 또는 summary를 한국어가 아닌"
                " 다른 언어로 반환하는 실수가 있었습니다. 이번에는 reason과 summary를"
                " 처음부터 끝까지 예외 없이 100% 한국어로만 작성하세요.",
            }
            try:
                retry_response = await self._client.messages.parse(**retry_kwargs)
                if (
                    getattr(retry_response, "stop_reason", None) != "refusal"
                    and retry_response.parsed_output is not None
                ):
                    result = retry_response.parsed_output
            except Exception:
                logger.exception("언어 검증 재시도 호출 실패 (model=%s)", settings.claude_model)

        # 프롬프트 지시를 모델이 놓칠 수 있으니, 모드별 카테고리 분리를 서버에서도 강제한다:
        # 실시간은 문장 교정(vocabulary/tone/taboo)만, 발송 전 검토는 매너/구조만.
        if is_realtime:
            result.issues = [issue for issue in result.issues if issue.category != AnalysisCategory.MANNERS]
        else:
            result.issues = [issue for issue in result.issues if issue.category == AnalysisCategory.MANNERS]
            # manners issue는 항상 "무엇을 보완하면 좋은지"에 대한 권고문이지, 그 자리에 바로
            # 끼워 넣을 완성 문장이 아니다. suggestion이 영어 문장처럼 보이면 모델이 fix_type을
            # "replace"로 착각해 반환할 때가 있는데, 그러면 프론트엔드가 그 권고문을 원문에
            # 그대로 삽입해버리므로 발송 전 검토 결과는 여기서 전부 "insert"로 강제한다.
            for issue in result.issues:
                issue.fix_type = IssueFixType.INSERT

        return _sanitize_email_result(result)

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

        # true_statement/false_statements는 country와 무관하게 항상 한국어여야
        # 하는데, country가 일본/중국이면 그 나라 언어로 새는 경우가 있다(reason/
        # summary에서 이미 겪은 것과 같은 문제). 위반 시 한 번 더 강하게
        # 재지시해서 재시도한다. correction_distractor_sets는 suggestion과 같은
        # 언어여야 하므로(영어/일본어일 수 있음) 이 검사 대상이 아니다.
        if any(
            not _is_mostly_korean(item.true_statement)
            or any(not _is_mostly_korean(stmt) for stmt in item.false_statements)
            for item in result.culture_items
        ):
            logger.warning("퀴즈 O/X 언어 검증 실패, 재시도합니다 (model=%s)", settings.claude_model)
            retry_kwargs = {
                **request_kwargs,
                "system": _QUIZ_SYSTEM_PROMPT
                + "\n\n[재시도 안내] 방금 응답에서 O/X 문제의 true_statement/"
                "false_statements를 한국어가 아닌 다른 언어로 반환하는 실수가"
                " 있었습니다. 이번에는 country와 무관하게 예외 없이 100% 한국어로만"
                " 작성하세요.",
            }
            try:
                retry_response = await self._client.messages.parse(**retry_kwargs)
                if (
                    getattr(retry_response, "stop_reason", None) != "refusal"
                    and retry_response.parsed_output is not None
                ):
                    result = retry_response.parsed_output
            except Exception:
                logger.exception("퀴즈 O/X 언어 검증 재시도 호출 실패 (model=%s)", settings.claude_model)

        return result


def get_ai_client() -> BaseAIClient:
    if settings.use_mock_ai:
        return MockAIClient()
    return ClaudeAIClient()
