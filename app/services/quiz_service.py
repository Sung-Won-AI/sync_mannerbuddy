import random
import re
from datetime import UTC, datetime, timedelta
from random import Random
from uuid import uuid4

from app.core.config import settings
from app.core.exceptions import ResourceNotFoundError
from app.repositories import repository
from app.schemas.quiz import (
    QuizAnswerRequest,
    QuizAnswerResponse,
    QuizOption,
    QuizQuestion,
    QuizSetResponse,
)
from app.services.ai_client import _unescape_literal_newlines, get_ai_client
from app.services.masking_service import masking_service

_DEFAULT_COUNTRIES = ("US", "JP", "CN")
_OPTION_IDS = ("A", "B", "C")

# 복습 퀴즈는 "이번 주에 실제로 받은 피드백"을 다시 보는 것이라, 오래된 분석까지
# 섞이면 의미가 옅어진다. 최근 며칠치만 대상으로 좁힌다.
_QUIZ_LOOKBACK_DAYS = 7

_MASK_TOKEN_LABELS = {"EMAIL": "이메일 주소", "PHONE": "전화번호", "MONEY": "금액"}
_MASK_TOKEN_PATTERN = re.compile(r"\[(EMAIL|PHONE|MONEY)_\d+\]")


def _desensitize(text: str) -> str:
    """[PHONE_1]/[EMAIL_1] 같은 마스킹 토큰은 실제 이메일 교정에서는 그대로
    유지해야 하지만, 퀴즈 보기/설명에 그대로 노출되면 개인정보 마스킹 구현
    디테일이 그대로 보여서 부자연스럽다. 화면에 보여줄 문자열만 자연스러운
    한국어 단어로 바꿔치기한다 — DB에 저장된 원본 데이터는 건드리지 않는다.
    AI가 JSON 문자열 안에 실제 개행 대신 리터럴 백슬래시+n을 넣는 과이스케이프
    실수(이메일 쪽에서 이미 겪은 것과 같은 문제)도 여기서 같이 되돌린다."""
    text = _unescape_literal_newlines(text)
    return _MASK_TOKEN_PATTERN.sub(lambda m: _MASK_TOKEN_LABELS[m.group(1)], text)


def _balance_by_country(
    issue_sources: list[tuple[dict, dict]],
    limit: int,
) -> list[tuple[dict, dict]]:
    """국가 하나의 피드백이 많다고 퀴즈가 그 나라 문제로만 채워지지 않도록,
    국가별로 라운드로빈으로 고르게 뽑는다. 여러 나라와 소통했다면 그 비율이
    자연스럽게 퀴즈에도 반영된다."""
    by_country: dict[str, list[tuple[dict, dict]]] = {}
    for pair in issue_sources:
        by_country.setdefault(pair[0]["target_country"], []).append(pair)

    selected: list[tuple[dict, dict]] = []
    while len(selected) < limit and by_country:
        for country in list(by_country.keys()):
            if len(selected) >= limit:
                break
            bucket = by_country[country]
            selected.append(bucket.pop(0))
            if not bucket:
                del by_country[country]
    return selected


class QuizService:
    def __init__(self) -> None:
        self._answers: dict[str, dict] = {}

    async def generate(self, limit: int) -> QuizSetResponse:
        analyses = repository.list_analyses(
            settings.demo_user_id,
            limit=50,
        )
        # "이번 주에 실제로 받은 피드백"을 복습하는 게 목적이라, 오래된 분석까지
        # 섞이면 의미가 옅어진다. 최근 며칠치만 대상으로 좁힌다.
        since = datetime.now(UTC) - timedelta(days=_QUIZ_LOOKBACK_DAYS)
        analyses = [analysis for analysis in analyses if analysis["created_at"] >= since]

        # 복습 퀴즈는 "실제로 고친 표현"을 대상으로 해야 의미가 있다. AI가
        # 지적했지만 사용자가 거부(rejected)했거나 아무 조치도 안 한 issue까지
        # 퀴즈로 내면 본인이 동의하지 않은 내용을 복습시키는 셈이라 accepted만 쓴다.
        accepted_pairs = {
            (action["analysis_id"], action["issue_id"])
            for action in repository.list_actions(
                settings.demo_user_id,
                action="accepted",
            )
        }
        issue_sources = [
            (analysis, issue)
            for analysis in analyses
            for issue in analysis.get("issues", [])
            if (analysis["analysis_id"], issue["issue_id"]) in accepted_pairs
        ]

        # 두 섹션으로 나눈다: 다중보기(표현 교정)는 replace형만, O/X는 insert형
        # (인사말·서명 같은 구조 문제) 위주로 다룬다 — 형식이 서로 안 맞기 때문이다.
        replace_sources = [pair for pair in issue_sources if pair[1]["fix_type"] == "replace"]
        insert_sources = [pair for pair in issue_sources if pair[1]["fix_type"] == "insert"]

        # 다중보기 문제는 최대 limit개. 국가별 라운드로빈으로 뽑아서, 이번 주 여러
        # 나라와 소통했다면 그 비율이 고르게 반영되게 한다.
        selected_corrections = _balance_by_country(replace_sources, limit)

        # O/X 문제에 쓸 국가 목록 — 이번 주 실제로 받은 insert형 피드백의 국가를
        # 우선으로 하고(라운드로빈으로 비율 유지), 모자라면 최근 소통 국가 →
        # 기본 국가 순으로 채운다. O/X 콘텐츠 자체는 ai_client의 국가별 매너
        # 지식(_QUIZ_SYSTEM_PROMPT)으로 생성하되, "어떤 나라를 물어볼지"는 이렇게
        # 실제 피드백 이력에서 가져온다.
        insert_countries = [pair[0]["target_country"] for pair in _balance_by_country(insert_sources, limit)]
        countries_seen = [analysis["target_country"] for analysis in analyses]
        country_pool = insert_countries or countries_seen or list(_DEFAULT_COUNTRIES)
        ox_countries = [country_pool[i % len(country_pool)] for i in range(limit)]

        correction_inputs = [
            {
                "key": f"c{index}",
                "target_country": analysis["target_country"],
                # 원문에 남아있을 수 있는 개인정보가 오답 생성용 AI 호출에 그대로
                # 나가지 않도록 다시 마스킹한다.
                "original": masking_service.mask(issue["original"]).masked_text,
                "suggestion": masking_service.mask(issue["suggestion"]).masked_text,
                "fix_type": issue["fix_type"],
            }
            for index, (analysis, issue) in enumerate(selected_corrections)
        ]

        ai_result = (
            await get_ai_client().generate_quiz_content(
                correction_sources=correction_inputs,
                culture_countries=ox_countries,
            )
            if correction_inputs or ox_countries
            else None
        )

        correction_questions: list[QuizQuestion] = []
        ox_questions: list[QuizQuestion] = []

        if ai_result is not None:
            distractors_by_key = {
                item.key: item.distractors for item in ai_result.correction_distractor_sets
            }
            for index, (analysis, issue) in enumerate(selected_corrections):
                distractors = distractors_by_key.get(f"c{index}", [])
                if len(distractors) < 2:
                    continue  # AI가 이 항목을 못 만들었으면 조용히 건너뛴다.

                question_id = str(uuid4())
                # [PHONE_1]/[EMAIL_1] 같은 마스킹 토큰은 실제 교정에는 필요하지만
                # 퀴즈 화면에 그대로 보이면 구현 디테일이 노출돼 부자연스럽다.
                correct_text = _desensitize(issue["suggestion"])
                options = [
                    QuizOption(id=_OPTION_IDS[0], text=correct_text),
                    QuizOption(id=_OPTION_IDS[1], text=_desensitize(distractors[0])),
                    QuizOption(id=_OPTION_IDS[2], text=_desensitize(distractors[1])),
                ]
                Random(question_id).shuffle(options)
                correct_option = next(
                    option.id for option in options if option.text == correct_text
                )
                self._answers[question_id] = {
                    "correct_option_id": correct_option,
                    "explanation": _desensitize(issue["reason"]),
                }
                correction_questions.append(
                    QuizQuestion(
                        id=question_id,
                        type="correction",
                        category=str(issue["category"]),
                        country=analysis["target_country"],
                        prompt=(
                            "다음 표현을 문화적으로 더 적절하게 수정한 문장은?\n"
                            f"{_desensitize(issue['original'])}"
                        ),
                        options=options,
                    )
                )

            # O/X: 문장 하나를 보여주고 그게 맞는 설명인지(⭕) 틀린 설명인지(❌)
            # 판단하게 한다 — "셋 중 맞는 것 고르기"인 다중보기와는 다른, 진짜
            # O/X 형식이다. AI가 만들어준 참인 설명과 거짓 설명 중 하나를 무작위로
            # 골라 보여주고, 정답은 그에 따라 O 또는 X가 된다.
            for item in ai_result.culture_items:
                true_text = _desensitize(item.true_statement)
                false_text = _desensitize(item.false_statements[0])
                show_true = random.random() < 0.5
                statement = true_text if show_true else false_text
                correct_option = "O" if show_true else "X"

                question_id = str(uuid4())
                self._answers[question_id] = {
                    "correct_option_id": correct_option,
                    "explanation": (
                        f"맞아요! {true_text}"
                        if show_true
                        else f"아니에요. 맞는 설명은 이거예요: {true_text}"
                    ),
                }
                ox_questions.append(
                    QuizQuestion(
                        id=question_id,
                        type="ox",
                        category="manners",
                        country=item.country,
                        prompt=f"다음 설명이 맞으면 ⭕, 틀리면 ❌를 골라보세요.\n{statement}",
                        options=[
                            QuizOption(id="O", text="⭕ 맞아요"),
                            QuizOption(id="X", text="❌ 아니에요"),
                        ],
                    )
                )

        random.shuffle(ox_questions)
        random.shuffle(correction_questions)
        # O/X 섹션이 먼저, 다중보기 섹션이 그 다음에 나오도록 순서를 고정한다
        # (두 섹션을 뒤섞지 않는다).
        questions = ox_questions + correction_questions

        return QuizSetResponse(
            generated_from_analyses=len(analyses),
            questions=questions,
        )

    def answer(
        self,
        question_id: str,
        payload: QuizAnswerRequest,
    ) -> QuizAnswerResponse:
        answer = self._answers.get(question_id)
        if answer is None:
            raise ResourceNotFoundError("퀴즈 문제")
        correct = payload.option_id == answer["correct_option_id"]
        repository.save_quiz_answer(
            {
                "user_id": settings.demo_user_id,
                "question_id": question_id,
                "option_id": payload.option_id,
                "correct": correct,
            }
        )
        return QuizAnswerResponse(
            correct=correct,
            correct_option_id=answer["correct_option_id"],
            explanation=answer["explanation"],
            score_awarded=10 if correct else 0,
        )


quiz_service = QuizService()
