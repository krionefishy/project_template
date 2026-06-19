from backend.shared.exceptions import AppError


class ExampleError(AppError):
    """Base exception for example_domain."""


class ExampleNotFoundError(ExampleError):
    status_code = 404
    detail = "Example not found"


class ExampleForbiddenError(ExampleError):
    status_code = 403
    detail = "Forbidden"


class ExampleFileUploadError(ExampleError):
    status_code = 503
    detail = "File upload queue unavailable"
