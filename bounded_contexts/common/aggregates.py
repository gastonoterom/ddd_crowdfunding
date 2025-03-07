from abc import ABC


# Aggregate base class
class Aggregate(ABC):
    def __init__(self, entity_id: str) -> None:
        self.__entity_id = entity_id

    @property
    def entity_id(self) -> str:
        return self.__entity_id

    def __eq__(self, other) -> bool:
        if not isinstance(other, Aggregate):
            return False

        return self.entity_id == other.entity_id
