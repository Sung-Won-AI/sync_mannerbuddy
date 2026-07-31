import random
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
from app.services.ai_client import get_ai_client
from app.services.masking_service import masking_service

_DEFAULT_COUNTRIES = ("US", "JP", "CN")
_OPTION_IDS = ("A", "B", "C")


class QuizService:
    def __init__(self) -> None:
        self._answers: dict[str, dict] = {}

    async def generate(self, limit: int) -> QuizSetResponse:
        analyses = repository.list_analyses(
            settings.demo_user_id,
            limit=50,
        )
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

        # 표현 교정 문제는 최대 limit개, 남는 자리는 국가별 매너 O/X 문제로 채운다.
        # accept한 게 하나도 없어도(신규 사용자) O/X 문제만으로 퀴즈가 성립한다.
        selected_sources = issue_sources[:limit]
        culture_count = limit - len(selected_sources)

        countries_seen = [analysis["target_country"] for analysis in analyses]
        country_pool = countries_seen or list(_DEFAULT_COUNTRIES)
        culture_countries = [
            country_pool[i % len(country_pool)] for i in range(culture_count)
        ]

        correction_inputs = [
            {
                "key": f"c{index}",
                "target_country": analysis["target_country"],
                # 원문에 남아있을 수 있는 개인정보가 오답 생성용 AI 호출에 그대로
                # 나가지 않도록 다시 마스킹한다.
                "original": masking_service.mask(issue["original"]).masked_text,
                "suggestion": masking_service.mask(issue["suggestion"]).masked_text,
                # insert형(권고문)과 replace형(실제 대체 문장)은 형태가 달라서,
                # 오답도 같은 형태로 만들어야 정답이 형식만으로 티나지 않는다.
                "fix_type": issue["fix_type"],
            }
            for index, (analysis, issue) in enumerate(selected_sources)
        ]

        ai_result = (
            await get_ai_client().generate_quiz_content(
                correction_sources=correction_inputs,
                culture_countries=culture_countries,
            )
            if correction_inputs or culture_countries
            else None
        )

        questions: list[QuizQuestion] = []

        if ai_result is not None:
            distractors_by_key = {
                item.key: item.distractors for item in ai_result.correction_distractor_sets
            }
            for index, (analysis, issue) in enumerate(selected_sources):
                distractors = distractors_by_key.get(f"c{index}", [])
                if len(distractors) < 2:
                    continue  # AI가 이 항목을 못 만들었으면 조용히 건너뛴다.

                question_id = str(uuid4())
                options = [
                    QuizOption(id=_OPTION_IDS[0], text=issue["suggestion"]),
                    QuizOption(id=_OPTION_IDS[1], text=distractors[0]),
                    QuizOption(id=_OPTION_IDS[2], text=distractors[1]),
                ]
                Random(question_id).shuffle(options)
                correct_option = next(
                    option.id for option in options if option.text == issue["suggestion"]
                )
                self._answers[question_id] = {
                    "correct_option_id": correct_option,
                    "explanation": issue["reason"],
                }
                questions.append(
                    QuizQuestion(
                        id=question_id,
                        type="correction",
                        category=str(issue["category"]),
                        country=analysis["target_country"],
                        prompt=(
                            f"다음 표현을 문화적으로 더 적절하게 수정한 문장은?\n"
                            f"{issue['original']}"
                        ),
                        options=options,
                    )
                )

            for item in ai_result.culture_items:
                question_id = str(uuid4())
                options = [
                    QuizOption(id=_OPTION_IDS[0], text=item.true_statement),
                    QuizOption(id=_OPTION_IDS[1], text=item.false_statements[0]),
                    QuizOption(id=_OPTION_IDS[2], text=item.false_statements[1]),
                ]
                Random(question_id).shuffle(options)
                correct_option = next(
                    option.id for option in options if option.text == item.true_statement
                )
                self._answers[question_id] = {
                    "correct_option_id": correct_option,
                    "explanation": f"맞는 설명은 이거예요: {item.true_statement}",
                }
                questions.append(
                    QuizQuestion(
                        id=question_id,
                        type="culture",
                        category="manners",
                        country=item.country,
                        prompt=f"다음 중 {item.country} 비즈니스 문화에 대해 맞는 설명은?",
                        options=options,
                    )
                )

        random.shuffle(questions)  # 교정 문제와 O/X 문제가 뒤섞여 나오도록.

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
