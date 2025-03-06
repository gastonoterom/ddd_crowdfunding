from bounded_contexts.common.aggregates import Aggregate
from bounded_contexts.common.ports.repositories import Repository


class MockRepository[T: Aggregate](Repository):
    _entities: dict[str, T] = {}

    async def _find_by_id(self, entity_id: str) -> T | None:
        return self._entities.get(entity_id)

    async def _add(self, entity: T) -> None:
        self._entities[entity.entity_id] = entity

    async def _update(self, entity: T) -> None:
        self._entities[entity.entity_id] = entity
