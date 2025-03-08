from bounded_contexts.bitcoin.adapters.view_factories import invoice_view_factory
from bounded_contexts.bitcoin.views import InvoiceView


async def get_invoice_view(payment_hash: str) -> InvoiceView:
    invoice: InvoiceView = await invoice_view_factory().create_invoice_view(
        payment_hash=payment_hash,
    )

    return InvoiceView(
        account_id=invoice.account_id,
        amount=invoice.amount,
        status=invoice.status,
        payment_hash=invoice.payment_hash,
        payment_request=invoice.payment_request,
        invoice_type=invoice.invoice_type,
    )
