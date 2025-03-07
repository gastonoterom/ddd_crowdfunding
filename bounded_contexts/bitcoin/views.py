from dataclasses import dataclass

from bounded_contexts.bitcoin.aggregates import InvoiceType


@dataclass(frozen=True)
class InvoiceView:
    account_id: str
    amount: int
    status: str
    payment_hash: str
    payment_request: str
    invoice_type: InvoiceType
