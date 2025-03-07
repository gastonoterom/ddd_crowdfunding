from dataclasses import dataclass

from infrastructure.events.messages import Command


@dataclass(frozen=True)
class CreateCampaign(Command):
    entity_id: str
    account_id: str
    title: str
    description: str
    goal: int


@dataclass(frozen=True)
class DonateToCampaign(Command):
    idempotency_key: str
    campaign_id: str
    account_id: str
    amount: int
