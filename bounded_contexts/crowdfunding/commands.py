from dataclasses import dataclass

from infrastructure.event_bus import Command


@dataclass(frozen=True)
class CreateCampaign(Command):
    campaign_id: str
    account_id: str
    goal: int


@dataclass(frozen=True)
class DonateToCampaign(Command):
    idempotency_key: str
    campaign_id: str
    account_id: str
    amount: int
