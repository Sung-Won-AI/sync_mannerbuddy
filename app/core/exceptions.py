class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 500,
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


class AIServiceUnavailableError(AppError):
    def __init__(self, message: str = "AI 분석 서비스를 사용할 수 없습니다.") -> None:
        super().__init__(
            "AI_UNAVAILABLE",
            message,
            status_code=503,
        )


class AIResponseValidationError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "AI_INVALID_RESPONSE",
            "AI 분석 결과의 형식이 올바르지 않습니다.",
            status_code=502,
        )


class ResourceNotFoundError(AppError):
    def __init__(self, resource: str) -> None:
        super().__init__(
            "RESOURCE_NOT_FOUND",
            f"{resource}을(를) 찾을 수 없습니다.",
            status_code=404,
        )
