from dataclasses import dataclass

from infrastructure.event_bus import Command, Event


@dataclass(frozen=True)
class RegisterAccount(Command):
    account_id: str
    username: str
    hashed_password: str


@dataclass(frozen=True)
class SignupEvent(Event):
    account_id: str
