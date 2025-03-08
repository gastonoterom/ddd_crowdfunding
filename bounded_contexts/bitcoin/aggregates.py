from enum import StrEnum

from bounded_contexts.common.aggregates import Aggregate


class InvoiceStatus(StrEnum):
    PENDING = "PENDING"
    PAID = "PAID"
    REJECTED = "REJECTED"


class InvoiceType(StrEnum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"


class BTCInvoice(Aggregate):
    def __init__(
        self,
        account_id: str,
        amount: int,
        payment_hash: str,
        payment_request: str,
        status: InvoiceStatus,
        invoice_type: InvoiceType,
    ) -> None:
        super().__init__(payment_hash)
        self._account_id = account_id
        self._amount = amount
        self._status = status
        self._payment_hash = payment_hash
        self._payment_request = payment_request
        self._invoice_type = invoice_type

    def mark_as_paid(self) -> None:
        if self._status == InvoiceStatus.PAID:
            return

        assert self._status == InvoiceStatus.PENDING
        self._status = InvoiceStatus.PAID

    def mark_as_rejected(self) -> None:
        if self._status == InvoiceStatus.REJECTED:
            return

        assert self._status == InvoiceStatus.PENDING
        self._status = InvoiceStatus.REJECTED

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

    @property
    def invoice_type(self) -> InvoiceType:
        return self._invoice_type
