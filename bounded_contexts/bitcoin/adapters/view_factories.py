from bounded_contexts.bitcoin.aggregates import InvoiceStatus
from bounded_contexts.bitcoin.ports.view_factories import InvoiceViewFactory
from bounded_contexts.bitcoin.views import InvoiceView
from infrastructure.postgres import postgres_pool


class PostgresInvoiceViewFactory(InvoiceViewFactory):
    async def create_invoice_view(self, payment_hash: str) -> InvoiceView:
        async with postgres_pool.get_pool().acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    *
                FROM btc_invoices a
                WHERE payment_hash = $1
                """,
                payment_hash,
            )

        assert row

        return InvoiceView(
            payment_hash=row.payment_hash,
            account_id=row.account_id,
            amount=int(row.amount),
            status=InvoiceStatus(row.status),
            payment_request=row.payment_request,
            invoice_type=row.invoice_type,
        )
