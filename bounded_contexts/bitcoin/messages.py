# TODO: create 'messages' package in all other domains
from dataclasses import dataclass

from bounded_contexts.bitcoin.aggregates import InvoiceType
from infrastructure.event_bus import Command, Event


@dataclass(frozen=True)
class CreateInvoice(Command):
    invoice_id: str
    account_id: str
    payment_hash: str
    payment_request: str
    # TODO: Handle 'amount' currency (satoshis, etc..)
    amount: int
    invoice_type: InvoiceType


@dataclass(frozen=True)
class DepositInvoicePaidEvent(Event):
    invoice_id: str  # TODO: Use payment hash
    account_id: str
    amount: int
    invoice_type: InvoiceType


@dataclass(frozen=True)
class WithdrawalCreatedEvent(Event):
    invoice_id: str  # TODO: Use payment hash
    account_id: str
    amount: int
    invoice_type: InvoiceType
