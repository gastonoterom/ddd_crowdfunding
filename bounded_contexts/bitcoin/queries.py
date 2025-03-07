from bounded_contexts.bitcoin.aggregates import BTCInvoice
from bounded_contexts.bitcoin.views import InvoiceView


async def get_invoice_view(payment_hash: str) -> InvoiceView:
    invoice: BTCInvoice | None = None

    if invoice is None:
        raise Exception(f"Invoice not found")

    return InvoiceView(
        account_id=invoice.account_id,
        amount=invoice.amount,
        status=invoice.status,
        payment_hash=invoice.payment_hash,
        payment_request=invoice.payment_request,
        invoice_type=invoice.invoice_type,
    )
