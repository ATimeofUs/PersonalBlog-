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


class ValidationServiceError(ServiceError):
    default_code = "VALIDATION_ERROR"
    default_status_code = 422


class NotFoundServiceError(ServiceError):
    default_code = "NOT_FOUND"
    default_status_code = 404


class AuthenticationServiceError(ServiceError):
    default_code = "UNAUTHORIZED"
    default_status_code = 401


class PermissionDeniedServiceError(ServiceError):
    default_code = "FORBIDDEN"
    default_status_code = 403


class ConflictServiceError(ServiceError):
    default_code = "CONFLICT"
    default_status_code = 409


class DependencyServiceError(ServiceError):
    default_code = "DEPENDENCY_ERROR"
    default_status_code = 503


class DatabaseServiceError(ServiceError):
    default_code = "DATABASE_ERROR"
    default_status_code = 500


class FileStorageServiceError(ServiceError):
    default_code = "FILE_STORAGE_ERROR"
    default_status_code = 500


class RateLimitServiceError(ServiceError):
    default_code = "RATE_LIMITED"
    default_status_code = 429


class UserNotFoundError(NotFoundServiceError):
    def __init__(self, user_id: int | None = None, username: str | None = None):
        super().__init__(
            "用户不存在",
            code="USER_NOT_FOUND",
            context={"user_id": user_id, "username": username},
        )


class PostNotFoundError(NotFoundServiceError):
    def __init__(self, post_id: int | None = None, slug: str | None = None):
        super().__init__(
            "文章不存在",
            code="POST_NOT_FOUND",
            context={"post_id": post_id, "slug": slug},
        )


class CategoryNotFoundError(NotFoundServiceError):
    def __init__(self, category_id: int | None = None, slug: str | None = None):
        super().__init__(
            "分类不存在",
            code="CATEGORY_NOT_FOUND",
            context={"category_id": category_id, "slug": slug},
        )


class DuplicateSlugError(ConflictServiceError):
    def __init__(self, slug: str | None = None):
        super().__init__(
            "slug 已存在，请换一个",
            code="DUPLICATE_SLUG",
            context={"slug": slug},
        )


class PermissionDeniedError(PermissionDeniedServiceError):
    def __init__(self, action: str, resource: str):
        super().__init__(
            "无权执行该操作",
            code="PERMISSION_DENIED",
            context={"action": action, "resource": resource},
        )