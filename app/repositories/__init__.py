"""Persistence repositories."""

from app.core.config import settings
from app.repositories.base import Repository


def _build_repository() -> Repository:
    if settings.storage_backend == "supabase":
        from app.repositories.supabase_repository import SupabaseRepository

        return SupabaseRepository()

    from app.repositories.memory_repository import MemoryRepository

    return MemoryRepository()


repository: Repository = _build_repository()
