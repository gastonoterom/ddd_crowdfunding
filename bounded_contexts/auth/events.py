from dataclasses import dataclass

from infrastructure.event_bus import Event


@dataclass(frozen=True)
class SignupEvent(Event):
    account_id: str
