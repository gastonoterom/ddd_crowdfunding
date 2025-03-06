from dataclasses import dataclass

from infrastructure.events.messages import Command, Event


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


@dataclass(frozen=True)
class DonationCreatedEvent(Event):
    idempotency_key: str
    donor_account_id: str
    recipient_account_id: str
    amount: int
