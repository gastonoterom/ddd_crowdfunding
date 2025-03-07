import asyncio
import logging
import pickle
from asyncio import sleep

from bounded_contexts.common.ports.outbox import (
    TransactionalOutbox,
    TransactionalOutboxProcessor,
)
from infrastructure.events.bus import event_bus
from infrastructure.events.messages import Message
from infrastructure.events.unit_of_work import PostgresUnitOfWork, UnitOfWork
from infrastructure.postgres import postgres_pool

logger = logging.getLogger(__name__)


class PostgresTransactionalOutbox(TransactionalOutbox):
    def __init__(self, uow: PostgresUnitOfWork) -> None:
        super().__init__(uow)
        self.uow = uow

    async def store(self, messages: list[Message]) -> None:
        if not messages:
            return

        # TODO: Don't use pickle...
        records = [(message.message_id, pickle.dumps(message)) for message in messages]

        # This uses a prepared statement under the hood, preventing SQL injection
        await self.uow.conn.executemany(
            """
            INSERT INTO outbox_messages (message_id, message_data) 
            VALUES ($1, $2)
            ON CONFLICT (message_id) DO NOTHING
            """,
            records,
        )


class PostgresTransactionalOutboxProcessor(TransactionalOutboxProcessor):
    async def process_messages(self) -> None:
        messages = await self._fetch_messages()

        await self._dispatch_messages(messages)

        await self._destroy_messages(messages)

    async def _fetch_messages(self) -> list[Message]:
        async with postgres_pool.get_pool().acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT message_id, message_data
                FROM outbox_messages
            """
            )

        return [self.__row_to_message(row) for row in rows]

    async def _dispatch_messages(self, messages: list[Message]) -> None:
        results = await asyncio.gather(
            *[event_bus.handle(message) for message in messages],
            return_exceptions=True,
        )

        exceptions = [result for result in results if isinstance(result, Exception)]
        if exceptions:
            for exc in exceptions:
                logger.error(f"Error processing message: {exc}")

    async def _destroy_messages(self, messages: list[Message]) -> None:
        async with postgres_pool.get_pool().acquire() as conn:
            await conn.execute(
                """
                DELETE FROM outbox_messages WHERE message_id = ANY($1)
                """,
                [message.id for message in messages],  # type: ignore
            )

    def __row_to_message(self, row: dict) -> Message:
        message_data = row["message_data"]
        return pickle.loads(message_data)


def outbox(uow: UnitOfWork) -> TransactionalOutbox:
    assert isinstance(uow, PostgresUnitOfWork)
    return PostgresTransactionalOutbox(uow)


def outbox_processor() -> TransactionalOutboxProcessor:
    return PostgresTransactionalOutboxProcessor()


async def process_outbox() -> None:
    processor = outbox_processor()
    while True:
        await processor.process_messages()
        await sleep(0.1)
