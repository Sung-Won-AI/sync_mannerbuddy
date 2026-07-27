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


class BaseAIClient(ABC):
    @abstractmethod
    async def analyze_email(
        self,
        *,
        masked_text: str,
        request: EmailAnalysisRequest,
    ) -> AIAnalysisResult:
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


def get_ai_client() -> BaseAIClient:
    if settings.use_mock_ai:
        return MockAIClient()
    return ClaudeAIClient()
