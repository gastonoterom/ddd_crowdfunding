from dataclasses import dataclass

from bounded_contexts.bitcoin.aggregates import InvoiceType
from infrastructure.events.messages import Command, Event


@dataclass(frozen=True)
class CreateInvoice(Command):
    account_id: str
    payment_hash: str
    payment_request: str
    amount: int
    invoice_type: InvoiceType


@dataclass(frozen=True)
class DepositInvoicePaidEvent(Event):
    payment_hash: str
