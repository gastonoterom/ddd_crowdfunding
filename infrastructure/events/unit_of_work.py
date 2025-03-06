from abc import ABC, abstractmethod
from typing import Callable

import asyncpg
from asyncpg.transaction import Transaction


from infrastructure.events.messages import Message


class UnitOfWork(ABC):
    def __init__(self) -> None:
        self._messages: list[Message] = []

        # Tracked objects are objects that have been retrieved or created and need to be persisted,
        # (along with a callback that will do the actual persistence)
        self._tracked_objects: list[tuple[object, Callable]] = []

    def emit(self, message: Message) -> None:
        self._messages.append(message)

    def collect_messages(self) -> list[Message]:
        messages = self._messages
        self._messages = []
        return messages

    def track_object(self, obj: object, callback: Callable) -> None:
        self._tracked_objects.append((obj, callback))

    async def commit(self) -> None:
        # First, persist (update) tracked objects
        for obj, persistence_callback in self._tracked_objects:
            await persistence_callback()

        # Then, save all stored messages to the outbox
        # TODO: get rid of this circular import
        from bounded_contexts.common.adapters.outbox_adapters import outbox

        messages = self.collect_messages()
        await outbox(self).store(messages)

        await self._commit()

    async def rollback(self) -> None:
        self._messages.clear()
        await self._rollback()

    @abstractmethod
    async def _commit(self) -> None:
        pass

    @abstractmethod
    async def _rollback(self) -> None:
        pass


# Postgres specific implementation
class PostgresUnitOfWork(UnitOfWork):
    def __init__(self, conn: asyncpg.Connection, transaction: Transaction) -> None:
        super().__init__()
        self.__conn = conn
        self.__transaction = transaction

    @property
    def conn(self) -> asyncpg.Connection:
        return self.__conn

    async def _commit(self) -> None:
        await self.__transaction.commit()

    async def _rollback(self) -> None:
        await self.__transaction.rollback()


# Mock UOW for unit tests
class MockUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        super().__init__()

    async def _commit(self) -> None:
        pass

    async def _rollback(self) -> None:
        pass
