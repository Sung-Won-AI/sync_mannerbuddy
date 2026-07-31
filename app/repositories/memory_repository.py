from collections import Counter
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from threading import Lock
from uuid import uuid4

from app.repositories.base import Repository


class MemoryRepository(Repository):
    """Demo persistence. See SupabaseRepository for the production backend."""

    def __init__(self) -> None:
        self._lock = Lock()
        self.reset()

    def reset(self) -> None:
        with getattr(self, "_lock", Lock()):
            self._analyses: dict[str, dict] = {}
            self._actions: list[dict] = []
            self._feedback: list[dict] = []
            self._quiz_answers: list[dict] = []

    def save_analysis(self, record: dict) -> dict:
        with self._lock:
            self._analyses[record["analysis_id"]] = deepcopy(record)
        return deepcopy(record)

    def get_analysis(self, analysis_id: str, user_id: str) -> dict | None:
        record = self._analyses.get(analysis_id)
        if not record or record["user_id"] != user_id:
            return None
        return deepcopy(record)

    def list_analyses(
        self,
        user_id: str,
        *,
        kind: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        records = [
            record
            for record in self._analyses.values()
            if record["user_id"] == user_id
            and (kind is None or record["kind"] == kind)
        ]
        records.sort(key=lambda item: item["created_at"], reverse=True)
        return deepcopy(records[:limit])

    def save_action(self, record: dict) -> dict:
        stored = {"id": str(uuid4()), **record, "created_at": datetime.now(UTC)}
        with self._lock:
            self._actions.append(stored)
        return deepcopy(stored)

    def list_actions(
        self,
        user_id: str,
        *,
        action: str | None = None,
    ) -> list[dict]:
        records = [
            record
            for record in self._actions
            if record["user_id"] == user_id
            and (action is None or record["action"] == action)
        ]
        return deepcopy(records)

    def save_feedback(self, record: dict) -> dict:
        stored = {"id": str(uuid4()), **record, "created_at": datetime.now(UTC)}
        with self._lock:
            self._feedback.append(stored)
        return deepcopy(stored)

    def save_quiz_answer(self, record: dict) -> dict:
        stored = {"id": str(uuid4()), **record, "created_at": datetime.now(UTC)}
        with self._lock:
            self._quiz_answers.append(stored)
        return deepcopy(stored)

    def dashboard(self, user_id: str, period_days: int) -> dict:
        since = datetime.now(UTC) - timedelta(days=period_days)
        records = [
            record
            for record in self._analyses.values()
            if record["user_id"] == user_id and record["created_at"] >= since
        ]

        if not records:
            return {
                "records": [],
                "country_counts": Counter(),
                "issue_counts": Counter(),
                "fixed_issue_counts": Counter(),
                "accepted_suggestions": 0,
            }

        country_counts = Counter(record["target_country"] for record in records)
        issue_counts = Counter(
            issue["category"]
            for record in records
            for issue in record.get("issues", [])
        )

        analysis_ids = {record["analysis_id"] for record in records}
        accepted_actions = [
            action
            for action in self.list_actions(user_id, action="accepted")
            if action["analysis_id"] in analysis_ids
        ]
        accepted_issue_ids_by_analysis: dict[str, set[str]] = {}
        for action in accepted_actions:
            accepted_issue_ids_by_analysis.setdefault(
                action["analysis_id"], set()
            ).add(action["issue_id"])

        fixed_issue_counts = Counter(
            issue["category"]
            for record in records
            for issue in record.get("issues", [])
            if issue["issue_id"]
            in accepted_issue_ids_by_analysis.get(record["analysis_id"], set())
        )

        return {
            "records": deepcopy(records),
            "country_counts": country_counts,
            "issue_counts": issue_counts,
            "fixed_issue_counts": fixed_issue_counts,
            "accepted_suggestions": len(accepted_actions),
        }

