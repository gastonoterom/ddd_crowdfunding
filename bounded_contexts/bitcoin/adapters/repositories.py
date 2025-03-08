from bounded_contexts.bitcoin.aggregates import BTCInvoice, InvoiceStatus, InvoiceType
from bounded_contexts.bitcoin.ports.repositories import InvoiceRepository
from infrastructure.events.unit_of_work import PostgresUnitOfWork, UnitOfWork


class PostgresInvoiceRepository(InvoiceRepository):

    def __init__(self, uow: PostgresUnitOfWork) -> None:
        super().__init__(uow)
        self.uow = uow

    async def find_by_payment_hash(self, payment_hash: str) -> BTCInvoice | None:
        row = await self.uow.conn.fetchrow(
            """
            SELECT * FROM btc_invoices WHERE payment_hash = $1
            """,
            payment_hash,
        )

        if not row:
            return None

        return BTCInvoice(
            account_id=row["account_id"],
            amount=int(row["amount"]),
            status=InvoiceStatus(row["status"]),
            payment_hash=row["payment_hash"],
            payment_request=row["payment_request"],
            invoice_type=InvoiceType(row["invoice_type"]),
        )

    async def _find_by_id(self, entity_id: str) -> BTCInvoice | None:
        row = await self.uow.conn.fetchrow(
            """
            SELECT * FROM btc_invoices WHERE payment_hash = $1
            """,
            entity_id,
        )

        if not row:
            return None

        return BTCInvoice(
            account_id=row["account_id"],
            amount=int(row["amount"]),
            status=InvoiceStatus(row["status"]),
            payment_hash=row["payment_hash"],
            payment_request=row["payment_request"],
            invoice_type=InvoiceType(row["invoice_type"]),
        )

    async def _add(self, entity: BTCInvoice) -> None:
        await self.uow.conn.execute(
            """
            INSERT INTO btc_invoices (
                account_id, amount, status, payment_hash, payment_request, invoice_type
            ) VALUES ($1, $2, $3, $4, $5, $6)

            """,
            entity._account_id,
            entity._amount,
            entity._status.value,
            entity._payment_hash,
            entity._payment_request,
            entity._invoice_type,
        )

    async def _update(self, entity: BTCInvoice) -> None:
        await self.uow.conn.execute(
            """
            UPDATE btc_invoices
            SET status = $1
            WHERE payment_hash = $2
            """,
            entity._status.value,
            entity.entity_id,
        )


def invoice_repository(uow: UnitOfWork) -> InvoiceRepository:
    if isinstance(uow, PostgresUnitOfWork):
        return PostgresInvoiceRepository(uow)

    raise Exception("Unsupported UnitOfWork type.")
