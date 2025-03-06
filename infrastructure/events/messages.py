# Base class for messages
from typing import TypedDict


class Message(TypedDict):
    message_id: str
    message_type: str


# Commands can only have one handler
class Command(Message):
    pass


# Events can have n handlers
class Event(Message):
    pass
