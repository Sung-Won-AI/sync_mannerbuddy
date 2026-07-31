from abc import ABC, abstractmethod


class Repository(ABC):
    @abstractmethod
    def save_analysis(self, record: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_analysis(self, analysis_id: str, user_id: str) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def list_analyses(
        self,
        user_id: str,
        *,
        kind: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def save_action(self, record: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def list_actions(
        self,
        user_id: str,
        *,
        action: str | None = None,
    ) -> list[dict]:
        raise NotImplementedError

    @abstractmethod
    def save_feedback(self, record: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def save_quiz_answer(self, record: dict) -> dict:
        raise NotImplementedError

    @abstractmethod
    def dashboard(self, user_id: str, period_days: int) -> dict:
        raise NotImplementedError
