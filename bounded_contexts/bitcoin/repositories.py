from abc import ABC, abstractmethod

from bounded_contexts.bitcoin.aggregates import BTCInvoice, InvoiceStatus, InvoiceType
from infrastructure.event_bus import UnitOfWork, PostgresUnitOfWork


# Abstract repository
class InvoiceRepository(ABC):

    @abstractmethod
    async def add(self, invoice: BTCInvoice) -> None:
        pass

    # TODO: We can add reference to dirty objects and
    #  update them automatically
    @abstractmethod
    async def update(self, invoice: BTCInvoice) -> None:
        pass

    @abstractmethod
    async def find_by_payment_hash(self, payment_hash: str) -> BTCInvoice | None:
        pass

    @abstractmethod
    async def find_by_invoice_id(self, invoice_id: str) -> BTCInvoice | None:
        pass


# Postgres implementation
class PostgresInvoiceRepository(InvoiceRepository):

    def __init__(self, uow: PostgresUnitOfWork) -> None:
        self.uow = uow

    @staticmethod
    def repository_ddl() -> str:
        return """
        CREATE TABLE IF NOT EXISTS btc_invoices (
            invoice_id VARCHAR PRIMARY KEY,
            account_id VARCHAR,
            payment_hash VARCHAR,
            payment_request VARCHAR,
            invoice_type VARCHAR,
            amount INT,
            status VARCHAR
        );
        """

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
            invoice_id=row["invoice_id"],
            account_id=row["account_id"],
            amount=int(row["amount"]),
            status=InvoiceStatus(row["status"]),
            payment_hash=row["payment_hash"],
            payment_request=row["payment_request"],
            invoice_type=InvoiceType(row["invoice_type"]),
        )

    async def find_by_invoice_id(self, invoice_id: str) -> BTCInvoice | None:
        row = await self.uow.conn.fetchrow(
            """
            SELECT * FROM btc_invoices WHERE invoice_id = $1
            """,
            invoice_id,
        )

        if not row:
            return None

        return BTCInvoice(
            invoice_id=row["invoice_id"],
            account_id=row["account_id"],
            amount=int(row["amount"]),
            status=InvoiceStatus(row["status"]),
            payment_hash=row["payment_hash"],
            payment_request=row["payment_request"],
            invoice_type=InvoiceType(row["invoice_type"]),
        )

    async def add(self, invoice: BTCInvoice) -> None:
        await self.uow.conn.execute(
            """
            INSERT INTO btc_invoices (
                invoice_id, account_id, amount, status, payment_hash, payment_request, invoice_type
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)

            """,
            invoice._invoice_id,
            invoice._account_id,
            invoice._amount,
            invoice._status.value,
            invoice._payment_hash,
            invoice._payment_request,
            invoice._invoice_type,
        )

    async def update(self, invoice: BTCInvoice) -> None:
        await self.uow.conn.execute(
            """
            UPDATE btc_invoices
            SET status = $1
            WHERE invoice_id = $2
            """,
            invoice._status.value,
            invoice._invoice_id,
        )


def invoice_repository(uow: UnitOfWork) -> InvoiceRepository:
    if isinstance(uow, PostgresUnitOfWork):
        return PostgresInvoiceRepository(uow)

    raise Exception("Unsupported UnitOfWork type.")
