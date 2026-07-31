from collections import Counter
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx

from app.core.config import settings
from app.repositories.base import Repository


def _normalize_base_url(raw: str) -> str:
    url = raw.strip().rstrip("/")
    if url.endswith("/rest/v1"):
        url = url[: -len("/rest/v1")]
    return url


class SupabaseRepository(Repository):
    """PostgREST(Supabase) 기반 저장소. 앱이 다루는 중첩 dict(scores/issues 등)를
    supabase/migrations/001_initial_schema.sql의 analyses 테이블 컬럼으로
    변환해서 읽고 쓴다. MVP 트래픽 규모라 httpx 동기 클라이언트로 충분하다고
    보고 골랐다 — 동시 요청이 늘어나면 비동기 클라이언트로 바꿔야 한다."""

    def __init__(self) -> None:
        if not settings.supabase_url or not settings.supabase_secret_key:
            raise RuntimeError(
                "STORAGE_BACKEND=supabase인데 SUPABASE_URL/SUPABASE_SECRET_KEY가 "
                "설정되지 않았습니다."
            )
        base_url = _normalize_base_url(settings.supabase_url)
        self._client = httpx.Client(
            base_url=f"{base_url}/rest/v1",
            headers={
                "apikey": settings.supabase_secret_key,
                "Authorization": f"Bearer {settings.supabase_secret_key}",
                "Content-Type": "application/json",
            },
            timeout=10.0,
        )

    @staticmethod
    def _to_row(record: dict) -> dict:
        scores = record.get("scores", {})
        created_at = record["created_at"]
        return {
            "id": record["analysis_id"],
            "user_id": record["user_id"],
            "kind": record["kind"],
            "target_country": record["target_country"],
            "title": record.get("title"),
            "overall_score": record["overall_score"],
            "vocabulary_score": scores.get("vocabulary"),
            "tone_score": scores.get("tone"),
            "taboo_score": scores.get("taboo"),
            "manners_score": scores.get("manners"),
            "meeting_temperature": record.get("meeting_temperature"),
            "revised_text": record.get("revised_text"),
            "summary": record.get("summary"),
            "issues": record.get("issues", []),
            "key_points": record.get("key_points", []),
            "action_items": record.get("action_items", []),
            "flow": record.get("flow", []),
            "client_request_id": record.get("client_request_id"),
            "extension_version": record.get("extension_version"),
            "processing_time_ms": record.get("processing_time_ms", 0),
            "created_at": (
                created_at.isoformat()
                if isinstance(created_at, datetime)
                else created_at
            ),
        }

    @staticmethod
    def _from_row(row: dict) -> dict:
        return {
            "analysis_id": row["id"],
            "user_id": row["user_id"],
            "kind": row["kind"],
            "target_country": row["target_country"],
            "title": row.get("title"),
            "overall_score": row["overall_score"],
            "scores": {
                "vocabulary": row["vocabulary_score"],
                "tone": row["tone_score"],
                "taboo": row["taboo_score"],
                "manners": row["manners_score"],
            },
            "meeting_temperature": row.get("meeting_temperature"),
            "revised_text": row.get("revised_text"),
            "summary": row["summary"],
            "issues": row.get("issues") or [],
            "key_points": row.get("key_points") or [],
            "action_items": row.get("action_items") or [],
            "flow": row.get("flow") or [],
            "client_request_id": row.get("client_request_id"),
            "extension_version": row.get("extension_version"),
            "processing_time_ms": row.get("processing_time_ms", 0),
            "created_at": datetime.fromisoformat(row["created_at"]),
        }

    def save_analysis(self, record: dict) -> dict:
        response = self._client.post(
            "/analyses",
            json=self._to_row(record),
            headers={"Prefer": "return=representation"},
        )
        response.raise_for_status()
        return self._from_row(response.json()[0])

    def get_analysis(self, analysis_id: str, user_id: str) -> dict | None:
        response = self._client.get(
            "/analyses",
            params={
                "id": f"eq.{analysis_id}",
                "user_id": f"eq.{user_id}",
                "limit": 1,
            },
        )
        response.raise_for_status()
        rows = response.json()
        return self._from_row(rows[0]) if rows else None

    def list_analyses(
        self,
        user_id: str,
        *,
        kind: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        params = {
            "user_id": f"eq.{user_id}",
            "order": "created_at.desc",
            "limit": limit,
        }
        if kind is not None:
            params["kind"] = f"eq.{kind}"
        response = self._client.get("/analyses", params=params)
        response.raise_for_status()
        return [self._from_row(row) for row in response.json()]

    def save_action(self, record: dict) -> dict:
        row = {
            "id": str(uuid4()),
            "analysis_id": record["analysis_id"],
            "issue_id": record["issue_id"],
            "user_id": record["user_id"],
            "action": record["action"],
        }
        response = self._client.post(
            "/analysis_actions",
            json=row,
            headers={"Prefer": "return=representation"},
        )
        response.raise_for_status()
        saved = response.json()[0]
        saved["created_at"] = datetime.fromisoformat(saved["created_at"])
        return saved

    def list_actions(
        self,
        user_id: str,
        *,
        action: str | None = None,
    ) -> list[dict]:
        params = {"user_id": f"eq.{user_id}"}
        if action is not None:
            params["action"] = f"eq.{action}"
        response = self._client.get("/analysis_actions", params=params)
        response.raise_for_status()
        rows = response.json()
        for row in rows:
            row["created_at"] = datetime.fromisoformat(row["created_at"])
        return rows

    def save_feedback(self, record: dict) -> dict:
        row = {
            "id": str(uuid4()),
            "user_id": record["user_id"],
            "analysis_id": record.get("analysis_id"),
            "rating": record["rating"],
            "is_helpful": record["is_helpful"],
            "comment": record.get("comment"),
        }
        response = self._client.post(
            "/feedback",
            json=row,
            headers={"Prefer": "return=representation"},
        )
        response.raise_for_status()
        saved = response.json()[0]
        saved["created_at"] = datetime.fromisoformat(saved["created_at"])
        return saved

    def save_quiz_answer(self, record: dict) -> dict:
        row = {
            "id": str(uuid4()),
            "user_id": record["user_id"],
            "question_id": record["question_id"],
            "selected_option_id": record["option_id"],
            "correct": record["correct"],
        }
        response = self._client.post(
            "/quiz_attempts",
            json=row,
            headers={"Prefer": "return=representation"},
        )
        response.raise_for_status()
        saved = response.json()[0]
        saved["created_at"] = datetime.fromisoformat(saved["created_at"])
        return saved

    def dashboard(self, user_id: str, period_days: int) -> dict:
        since = (datetime.now(UTC) - timedelta(days=period_days)).isoformat()
        response = self._client.get(
            "/analyses",
            params={"user_id": f"eq.{user_id}", "created_at": f"gte.{since}"},
        )
        response.raise_for_status()
        records = [self._from_row(row) for row in response.json()]

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
            "records": records,
            "country_counts": country_counts,
            "issue_counts": issue_counts,
            "fixed_issue_counts": fixed_issue_counts,
            "accepted_suggestions": len(accepted_actions),
        }
