// 백엔드 app/schemas/quiz.py의 필드명을 그대로 따른다.

export interface QuizOption {
  id: string;
  text: string;
}

export type QuizQuestionType = "correction" | "culture";

export interface QuizQuestion {
  id: string;
  type: QuizQuestionType;
  category: string;
  country: string;
  prompt: string;
  options: QuizOption[];
}

export interface QuizSetResponse {
  generated_from_analyses: number;
  estimated_minutes: number;
  questions: QuizQuestion[];
}

export interface QuizAnswerResponse {
  correct: boolean;
  correct_option_id: string;
  explanation: string;
  score_awarded: number;
}
