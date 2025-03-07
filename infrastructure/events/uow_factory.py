import contextlib
from typing import AsyncGenerator, Callable

from config.env import environment, EnvType
from infrastructure.events.unit_of_work import (
    PostgresUnitOfWork,
    MockUnitOfWork,
    UnitOfWork,
)
from infrastructure.postgres import postgres_pool


@contextlib.asynccontextmanager
async def make_postgres_unit_of_work() -> AsyncGenerator[PostgresUnitOfWork, None]:
    async with postgres_pool.get_pool().acquire() as conn:
        transaction = conn.transaction(isolation="repeatable_read")
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


make_unit_of_work: Callable[
    [], contextlib.AbstractAsyncContextManager[UnitOfWork, None]
]

if environment.env_type == EnvType.UNIT_TEST:
    make_unit_of_work = make_mock_unit_of_work  # type: ignore

else:
    make_unit_of_work = make_postgres_unit_of_work  # type: ignore
