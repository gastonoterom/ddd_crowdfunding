from abc import ABC, abstractmethod

from infrastructure.events.messages import Message
from infrastructure.events.unit_of_work import UnitOfWork


class TransactionalOutbox(ABC):
    def __init__(self, uow: UnitOfWork) -> None:
        self.__uow = uow

    @abstractmethod
    async def store(self, messages: list[Message]) -> None:
        pass


class TransactionalOutboxProcessor(ABC):
    async def process_messages(self) -> None:
        messages = await self._fetch_messages()

        await self._dispatch_messages(messages)

        await self._destroy_messages(messages)

    @abstractmethod
    async def _fetch_messages(self) -> list[Message]:
        pass

    @abstractmethod
    async def _dispatch_messages(self, messages: list[Message]) -> None:
        pass

    @abstractmethod
    async def _destroy_messages(self, messages: list[Message]) -> None:
        pass
