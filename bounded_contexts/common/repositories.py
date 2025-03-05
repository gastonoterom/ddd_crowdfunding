from abc import ABC, abstractmethod

from bounded_contexts.common.aggregates import Aggregate
from infrastructure.event_bus import UnitOfWork


# Generic abstract repository class
class Repository[T: Aggregate](ABC):

    def __init__(self, uow: UnitOfWork) -> None:
        self.__uow = uow

    def __track_object(self, obj: T) -> None:
        self.__uow.track_object(obj, lambda: self._update(obj))

    async def find_by_id(self, entity_id: str) -> T | None:
        obj = await self._find_by_id(entity_id)

        if obj is not None:
            self.__track_object(obj)

        return obj

    async def add(self, entity: T) -> None:
        await self._add(entity)
        self.__track_object(entity)

    @abstractmethod
    async def _find_by_id(self, entity_id: str) -> T | None:
        pass

    @abstractmethod
    async def _add(self, entity: T) -> None:
        pass

    @abstractmethod
    async def _update(self, entity: T) -> None:
        pass
