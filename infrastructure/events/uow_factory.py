# Unit Of Work context manager:
import contextlib
import sys
from typing import AsyncGenerator, Callable

from infrastructure.events.unit_of_work import (
    PostgresUnitOfWork,
    MockUnitOfWork,
    UnitOfWork,
)
from infrastructure.postgres import postgres_pool


@contextlib.asynccontextmanager
async def make_postgres_unit_of_work() -> AsyncGenerator[PostgresUnitOfWork, None]:
    # TODO: Prevent transactions inside transactions

    async with postgres_pool.get_pool().acquire() as conn:
        # TODO: Set isolation level to repeatable read
        transaction = conn.transaction()
        await transaction.start()

        uow = PostgresUnitOfWork(
            conn,  # type: ignore
            transaction,
        )

        try:
            yield uow

            await uow.commit()
        except BaseException:
            await uow.rollback()
            raise


@contextlib.asynccontextmanager
async def make_mock_unit_of_work() -> AsyncGenerator[MockUnitOfWork, None]:
    uow = MockUnitOfWork()

    yield uow


# TODO: Not the most reliable way, hide behind an abstraction
make_unit_of_work: Callable[
    [], contextlib.AbstractAsyncContextManager[UnitOfWork, None]
]
if "pytest" in sys.modules:
    make_unit_of_work = make_mock_unit_of_work  # type: ignore

else:
    make_unit_of_work = make_postgres_unit_of_work  # type: ignore
