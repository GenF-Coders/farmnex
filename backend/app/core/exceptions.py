from typing import Any


class AppException(Exception):
    """
    Base application exception.

    Services/repositories can raise these exceptions without
    depending directly on FastAPI's HTTPException.
    """

    status_code: int = 500
    default_detail: str = "An unexpected application error occurred."

    def __init__(
        self,
        detail: str | None = None,
        *,
        headers: dict[str, str] | None = None,
        code: str | None = None,
        data: Any = None,
    ) -> None:
        self.detail = detail or self.default_detail
        self.headers = headers
        self.code = code
        self.data = data

        super().__init__(self.detail)


class BadRequestError(AppException):
    status_code = 400
    default_detail = "Bad request."


class UnauthorizedError(AppException):
    status_code = 401
    default_detail = "Authentication is required."


class ForbiddenError(AppException):
    status_code = 403
    default_detail = "You do not have permission to perform this action."


class NotFoundError(AppException):
    status_code = 404
    default_detail = "The requested resource was not found."


class ConflictError(AppException):
    status_code = 409
    default_detail = "The request conflicts with the current state."


class ValidationError(AppException):
    status_code = 422
    default_detail = "The provided data is invalid."


class UnprocessableEntityError(AppException):
    status_code = 422
    default_detail = "The request could not be processed."


class TooManyRequestsError(AppException):
    status_code = 429
    default_detail = "Too many requests."

ConflictError
class InternalServerError(AppException):
    status_code = 500
    default_detail = "Internal server error."


class ServiceUnavailableError(AppException):
    status_code = 503
    default_detail = "Service temporarily unavailable."
    

