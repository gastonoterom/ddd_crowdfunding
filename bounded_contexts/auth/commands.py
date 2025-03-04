from dataclasses import dataclass

from infrastructure.event_bus import Command


@dataclass(frozen=True)
class RegisterAccount(Command):
    account_id: str
    username: str
    hashed_password: str
