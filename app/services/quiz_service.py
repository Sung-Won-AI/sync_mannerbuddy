from random import Random
from uuid import uuid4

from app.core.config import settings
from app.core.exceptions import ResourceNotFoundError
from app.repositories.memory_repository import repository
from app.schemas.quiz import (
    QuizAnswerRequest,
    QuizAnswerResponse,
    QuizOption,
    QuizQuestion,
    QuizSetResponse,
)


class QuizService:
    def __init__(self) -> None:
        self._answers: dict[str, dict] = {}

    def generate(self, limit: int) -> QuizSetResponse:
        analyses = repository.list_analyses(
            settings.demo_user_id,
            limit=50,
        )
        issue_sources = [
            (analysis, issue)
            for analysis in analyses
            for issue in analysis.get("issues", [])
        ]

        questions: list[QuizQuestion] = []
        for analysis, issue in issue_sources[:limit]:
            question_id = str(uuid4())
            options = [
                QuizOption(id="A", text=issue["suggestion"]),
                QuizOption(id="B", text=issue["original"]),
                QuizOption(id="C", text="No changes are necessary."),
            ]
            Random(question_id).shuffle(options)
            correct_option = next(
                option.id
                for option in options
                if option.text == issue["suggestion"]
            )
            self._answers[question_id] = {
                "correct_option_id": correct_option,
                "explanation": issue["reason"],
            }
            questions.append(
                QuizQuestion(
                    id=question_id,
                    category=str(issue["category"]),
                    country=analysis["target_country"],
                    prompt=(
                        f"다음 표현을 문화적으로 더 적절하게 수정한 문장은?\n"
                        f"{issue['original']}"
                    ),
                    options=options,
                )
            )

        if not questions:
            question_id = str(uuid4())
            self._answers[question_id] = {
                "correct_option_id": "A",
                "explanation": "정중한 요청형 표현은 명령형보다 완곡합니다.",
            }
            questions.append(
                QuizQuestion(
                    id=question_id,
                    category="tone",
                    country="JP",
                    prompt="더 정중한 비즈니스 요청 표현을 선택하세요.",
                    options=[
                        QuizOption(
                            id="A",
                            text="Could you please review this document?",
                        ),
                        QuizOption(id="B", text="Review this document now."),
                        QuizOption(id="C", text="You must review this."),
                    ],
                )
            )

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

