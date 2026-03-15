from typing import Any


class ServiceError(Exception):
    """基础业务异常：统一携带状态码、错误码与结构化上下文。"""

    default_code = "SERVICE_ERROR"
    default_status_code = 400

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        detail: Any = None,
        context: dict[str, Any] | None = None,
    ):
        self.message = message
        self.code = code or self.default_code
        self.status_code = status_code or self.default_status_code
        self.detail = detail
        self.context = context or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.detail is not None:
            payload["detail"] = self.detail
        if self.context:
            payload["context"] = self.context
        return payload
