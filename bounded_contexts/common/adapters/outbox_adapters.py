import asyncio

from bounded_contexts.common.ports.outbox import (
    TransactionalOutbox,
    TransactionalOutboxProcessor,
)
from infrastructure.events.bus import event_bus
from infrastructure.events.messages import Message
from infrastructure.events.unit_of_work import PostgresUnitOfWork, UnitOfWork
from infrastructure.postgres import postgres_pool


class PostgresTransactionalOutbox(TransactionalOutbox):
    def __init__(self, uow: PostgresUnitOfWork) -> None:
        super().__init__(uow)
        self.uow = uow

    async def store(self, messages: list[Message]) -> None:
        # TODO: batch insert
        for message in messages:
            await self.uow.conn.execute(
                """INSERT INTO outbox_messages (message_id, message_type, message_data) 
                VALUES ($1, $2, $3)""",
                # TODO: This
                message.id,  # type: ignore
                message.type,  # type: ignore
                message.data,  # type: ignore
            )


class PostgresTransactionalOutboxProcessor(TransactionalOutboxProcessor):
    async def process_messages(self) -> None:
        messages = await self._fetch_messages()

        await self._dispatch_messages(messages)

        await self._destroy_messages(messages)

    async def _fetch_messages(self) -> list[Message]:
        async with postgres_pool.get_pool().acquire() as conn:
            # TODO: This
            rows = await conn.fetch("")

        return [self.__row_to_message(row) for row in rows]

    async def _dispatch_messages(self, messages: list[Message]) -> None:
        await asyncio.gather(
            *[event_bus.handle(message) for message in messages],
            return_exceptions=True,
        )

        # TODO: Log exceptions

    async def _destroy_messages(self, messages: list[Message]) -> None:
        async with postgres_pool.get_pool().acquire() as conn:
            await conn.execute(
                """
                DELETE FROM outbox_messages WHERE message_id = ANY($1)
                """,
                [message.id for message in messages],  # type: ignore
            )

    def __row_to_message(self, row: dict) -> Message:
        raise NotImplementedError()


# TODO: Also do mock ones
def outbox(uow: UnitOfWork) -> TransactionalOutbox:
    assert isinstance(uow, PostgresUnitOfWork)
    return PostgresTransactionalOutbox(uow)


def outbox_processor() -> TransactionalOutboxProcessor:
    return PostgresTransactionalOutboxProcessor()
