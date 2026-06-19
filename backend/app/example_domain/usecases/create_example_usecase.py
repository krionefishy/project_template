import logging
import uuid

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.deps import AuthContext
from backend.app.example_domain.db_models import ExampleModel
from backend.app.example_domain.domain import CreateExampleRequest
from backend.app.example_domain.dto import ExampleDTO
from backend.app.example_domain.exceptions import ExampleForbiddenError

logger = logging.getLogger(__name__)


class CreateExampleUseCase:
    ALLOWED_ROLES: frozenset[str] = frozenset({"admin", "manager"})

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def execute(self, request: CreateExampleRequest, ctx: AuthContext) -> ExampleDTO:
        if ctx.role not in self.ALLOWED_ROLES:
            logger.warning("Forbidden: role=%r cannot create examples", ctx.role)
            raise ExampleForbiddenError(f"Role {ctx.role!r} is not allowed to create examples")

        result = await self.session.execute(
            insert(ExampleModel)
            .values(
                id=uuid.uuid4(),
                title=request.title,
                description=request.description,
                status=request.status,
            )
            .returning(ExampleModel)
        )
        example = result.scalar_one()
        await self.session.commit()

        return ExampleDTO.model_validate(example)
