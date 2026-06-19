"""
Base application exception.

All domain-specific exceptions inherit from AppError.
The global exception handler in application.py converts AppError → JSONResponse
using status_code and detail — so routes don't need try/except for domain errors.

Usage in domain exceptions.py:

    from backend.shared.exceptions import AppError

    class OrderError(AppError):
        \"\"\"Base for orders domain.\"\"\"

    class OrderNotFoundError(OrderError):
        status_code = 404
        detail = "Order not found"

    class OrderForbiddenError(OrderError):
        status_code = 403
        detail = "Forbidden"

    class OrderConflictError(OrderError):
        status_code = 409
        detail = "Order already exists"

Usage in UseCase:

    raise OrderNotFoundError()                          # uses class defaults
    raise OrderNotFoundError("Order 123 not found")    # custom message
    raise OrderNotFoundError(status_code=410)          # override status

Usage in routes (NO try/except needed for domain errors):

    @router.get("/{id}", response_model=OrderDTO)
    async def get_order(id: UUID, usecase: FromDishka[GetOrderUseCase]) -> OrderDTO:
        return await usecase.execute(id)
        # OrderNotFoundError → 404 handled globally
"""


class AppError(Exception):
    """
    Base application exception.

    Class attributes set the default HTTP status code and response detail.
    Instances can override them per-raise.
    """

    status_code: int = 500
    detail: str = "An unexpected error occurred"

    def __init__(
        self,
        detail: str | None = None,
        *,
        status_code: int | None = None,
    ) -> None:
        self.detail = detail if detail is not None else self.__class__.detail
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.detail)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(status_code={self.status_code}, detail={self.detail!r})"
