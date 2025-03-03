from dataclasses import dataclass

from infrastructure.event_bus import Event


@dataclass(frozen=True)
class DonationCreatedEvent(Event):
    idempotency_key: str
    donor_account_id: str
    recipient_account_id: str
    amount: int
