from enum import StrEnum


class InvoiceStatus(StrEnum):
    PENDING = "PENDING"
    PAID = "PAID"


class InvoiceType(StrEnum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"


class BTCInvoice:
    def __init__(
        self,
        invoice_id: str,
        account_id: str,
        amount: int,
        payment_hash: str,
        payment_request: str,
        status: InvoiceStatus,
        invoice_type: InvoiceType,
    ) -> None:
        self._invoice_id = invoice_id
        self._account_id = account_id
        self._amount = amount
        self._status = status
        self._payment_hash = payment_hash
        self._payment_request = payment_request
        self._invoice_type = invoice_type

    def mark_as_paid(self) -> None:
        self._status = InvoiceStatus.PAID

    @property
    def invoice_id(self) -> str:
        return self._invoice_id

    @property
    def account_id(self) -> str:
        return self._account_id

    @property
    def amount(self) -> int:
        return self._amount

    @property
    def status(self) -> InvoiceStatus:
        return self._status

    @property
    def payment_hash(self) -> str:
        return self._payment_hash

    @property
    def payment_request(self) -> str:
        return self._payment_request
