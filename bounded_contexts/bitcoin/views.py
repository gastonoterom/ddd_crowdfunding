from dataclasses import dataclass

from bounded_contexts.bitcoin.adapters.repositories import invoice_repository
from bounded_contexts.bitcoin.aggregates import BTCInvoice, InvoiceType
from infrastructure.event_bus import make_unit_of_work


@dataclass(frozen=True)
class InvoiceView:
    invoice_id: str
    account_id: str
    amount: int
    status: str
    payment_hash: str
    payment_request: str
    invoice_type: InvoiceType


async def get_invoice_view(payment_hash: str) -> InvoiceView:
    async with make_unit_of_work() as uow:
        # TODO: don't use uow here, use view factories
        invoice: BTCInvoice | None = await invoice_repository(uow).find_by_payment_hash(
            payment_hash=payment_hash,
        )

    if invoice is None:
        raise Exception(f"Invoice not found")

    return InvoiceView(
        account_id=invoice.account_id,
        invoice_id=invoice.invoice_id,
        amount=invoice.amount,
        status=invoice.status,
        payment_hash=invoice.payment_hash,
        payment_request=invoice.payment_request,
        invoice_type=invoice.invoice_type,
    )
