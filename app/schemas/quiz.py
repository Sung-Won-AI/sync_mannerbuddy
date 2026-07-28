from pydantic import BaseModel, Field


class QuizOption(BaseModel):
    id: str
    text: str


class QuizQuestion(BaseModel):
    id: str
    category: str
    country: str
    prompt: str
    options: list[QuizOption]


class QuizSetResponse(BaseModel):
    generated_from_analyses: int
    estimated_minutes: int = 3
    questions: list[QuizQuestion]


class QuizAnswerRequest(BaseModel):
    option_id: str


class QuizAnswerResponse(BaseModel):
    correct: bool
    correct_option_id: str
    explanation: str
    score_awarded: int = Field(ge=0)
