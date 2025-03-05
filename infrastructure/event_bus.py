import contextlib
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator, Callable

import asyncpg
from asyncpg import Connection
from asyncpg.transaction import Transaction
from retry import retry

from infrastructure.postgres import postgres_pool


# Base class for messages
@dataclass(frozen=True)
class Message(ABC):
    pass


# Commands can only have one handler
@dataclass(frozen=True)
class Command(Message):
    pass


# Events can have n handlers
@dataclass(frozen=True)
class Event(Message):
    pass


# This represents an atomic database transaction
class UnitOfWork(ABC):
    def __init__(self) -> None:
        self._messages: list[Message] = []
        # Dirty objects are objects that have been modified and need to be persisted,
        # along with a callback that will do the actual persistence
        self._dirty_objects: list[tuple[object, Callable]] = []

    def emit(self, message: Message) -> None:
        self._messages.append(message)

    def collect_messages(self) -> list[Message]:
        messages = self._messages
        self._messages = []
        return messages

    def add_dirty_object(self, obj: object, callback: Callable) -> None:
        self._dirty_objects.append((obj, callback))

    @abstractmethod
    async def commit(self) -> None:
        for obj, persistence_callback in self._dirty_objects:
            await persistence_callback(obj)

    @abstractmethod
    async def rollback(self) -> None:
        self._messages.clear()


# Postgres specific implementation
class PostgresUnitOfWork(UnitOfWork):
    def __init__(self, conn: asyncpg.Connection, transaction: Transaction) -> None:
        super().__init__()
        self.__conn = conn
        self.__transaction = transaction

    @property
    def conn(self) -> Connection:
        return self.__conn

    async def commit(self) -> None:
        await super().commit()
        await self.__transaction.commit()

    async def rollback(self) -> None:
        await super().rollback()
        await self.__transaction.rollback()


# Mock UOW for unit tests
class MockUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        super().__init__()

    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass


# Unit Of Work context manager:
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


# The event bus: handles a message, dispatches it to the right handler,
# then collects the messages emitted by the handler
# and dispatches them as well until the queue is empty
class EventBus:
    def __init__(
        self,
    ) -> None:
        # Commands can have 1 and only 1 handler
        self._command_handlers: dict[type[Command], Callable] = {}

        # Events can have N handlers
        self._event_handlers: dict[type[Event], list[Callable]] = {}

    def register_command_handler(
        self, command: type[Command], handler: Callable
    ) -> None:
        self._command_handlers[command] = handler

    def register_event_handler(self, event: type[Event], handler: Callable) -> None:
        if event not in self._event_handlers:
            self._event_handlers[event] = []

        self._event_handlers[event].append(handler)

    @retry(
        tries=3,
        delay=0.1,
        jitter=0.1,
    )
    async def handle(self, message: Message) -> None:
        async with make_unit_of_work() as uow:
            messages: list[Message] = [message]

            while messages:
                message = messages.pop(0)

                if isinstance(message, Command):
                    await self._handle_command(uow, message, messages)

                elif isinstance(message, Event):
                    await self._handle_event(uow, message, messages)

    async def _handle_command(
        self, uow: UnitOfWork, command: Command, messages: list[Message]
    ) -> None:
        handler = self._command_handlers[type(command)]

        await handler(uow, command)

        messages.extend(uow.collect_messages())

    async def _handle_event(
        self, uow: UnitOfWork, event: Event, messages: list[Message]
    ) -> None:
        handlers = self._event_handlers.get(type(event), [])

        for handler in handlers:
            await handler(uow, event)

            messages.extend(uow.collect_messages())


event_bus = EventBus()
