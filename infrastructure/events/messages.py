# Base class for messages

from abc import ABC
from dataclasses import dataclass, asdict, field
from uuid import uuid4


@dataclass(frozen=True)
class Message(ABC):
    message_id: str = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, "message_id", uuid4().hex)

    def to_dict(self) -> dict:
        return asdict(self)


# Commands can only have one handler
@dataclass(frozen=True)
class Command(Message):
    pass


# Events can have n handlers
@dataclass(frozen=True)
class Event(Message):
    pass
