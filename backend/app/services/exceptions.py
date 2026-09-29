from __future__ import annotations


class ServiceError(Exception):
    """
    Base exception for application service-layer errors.
    """


class ResourceNotFoundError(ServiceError):
    """
    Requested resource does not exist or is not visible
    to the current user.
    """


class ResourceAlreadyExistsError(ServiceError):
    """
    Resource conflicts with an existing resource.
    """


class OwnershipError(ServiceError):
    """
    Authenticated user does not own the requested resource.
    """


class ForbiddenOperationError(ServiceError):
    """
    User is authenticated but is not permitted to perform
    the requested business operation.
    """


class ValidationError(ServiceError):
    """
    Business-level validation failed.

    This is different from Pydantic request validation.
    """


class ConflictError(ServiceError):
    """
    Operation conflicts with current application/database state.
    """


class DependencyError(ServiceError):
    """
    Required related resource or dependency is unavailable.
    """


class ServiceOperationError(ServiceError):
    """
    Unexpected/controlled service-level operation failure.
    """