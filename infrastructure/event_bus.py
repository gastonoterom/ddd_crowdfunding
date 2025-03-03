import contextlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator

import asyncpg
from asyncpg import Connection
from asyncpg.transaction import Transaction

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

    def emit(self, message: Message) -> None:
        self._messages.append(message)

    def collect_messages(self) -> list[Message]:
        messages = self._messages
        self._messages = []
        return messages

    @abstractmethod
    async def commit(self) -> None:
        pass

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
        await self.__transaction.commit()

    async def rollback(self) -> None:
        await self.__transaction.rollback()
        await super().rollback()


# Unit Of Work context manager:
@contextlib.asynccontextmanager
async def make_unit_of_work() -> AsyncGenerator[UnitOfWork, None]:
    pool = postgres_pool.pool

    if pool is None:
        pool = await postgres_pool.start_pool()

    async with pool.acquire() as conn:
        # TODO: Set isolation level to repeatable read
        transaction = conn.transaction()
        await transaction.start()

        uow = PostgresUnitOfWork(conn, transaction)

        try:
            yield uow

            await uow.commit()
        except BaseException:
            await uow.rollback()
            raise


# The event bus: handles a message, dispatches it to the right handler,
# then collects the messages emitted by the handler
# and dispatches them as well until the queue is empty
class EventBus:
    def __init__(
        self,
    ):
        # TODO: Better typing
        self._command_handlers: dict[type[Command], callable] = {}
        self._event_handlers: dict[type[Event], list[callable]] = {}

    def register_command_handler(
        self, command: type[Command], handler: callable
    ) -> None:
        self._command_handlers[command] = handler

    def register_event_handler(self, event: type[Event], handler: callable) -> None:
        if event not in self._event_handlers:
            self._event_handlers[event] = []

        self._event_handlers[event].append(handler)

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
