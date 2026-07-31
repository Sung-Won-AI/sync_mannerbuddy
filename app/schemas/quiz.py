from pydantic import BaseModel, Field


class QuizOption(BaseModel):
    id: str
    text: str


class QuizQuestion(BaseModel):
    id: str
    type: str = "correction"  # "correction" | "culture"
    category: str
    country: str
    prompt: str
    options: list[QuizOption]


class QuizSetResponse(BaseModel):
    generated_from_analyses: int
    estimated_minutes: int = 3
    questions: list[QuizQuestion]


class CorrectionDistractorSet(BaseModel):
    """표현 교정 문제 1개에 들어갈 오답 보기. key는 quiz_service가 보낸 값을
    그대로 돌려받아 어떤 issue에 대한 오답인지 짝짓는 용도."""

    key: str
    distractors: list[str] = Field(min_length=2, max_length=2)


class CultureQuizItem(BaseModel):
    """국가별 비즈니스 매너 O/X 문제 1개."""

    key: str
    country: str
    true_statement: str
    false_statements: list[str] = Field(min_length=2, max_length=2)


class AIQuizGenerationResult(BaseModel):
    correction_distractor_sets: list[CorrectionDistractorSet]
    culture_items: list[CultureQuizItem]


class QuizAnswerRequest(BaseModel):
    option_id: str


class QuizAnswerResponse(BaseModel):
    correct: bool
    correct_option_id: str
    explanation: str
    score_awarded: int = Field(ge=0)
