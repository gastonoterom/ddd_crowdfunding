from abc import abstractmethod

from bounded_contexts.bitcoin.aggregates import BTCInvoice
from bounded_contexts.common.ports.repositories import Repository


# Abstract repository
class InvoiceRepository(Repository[BTCInvoice]):
    # TODO: Use this as entity id directly
    @abstractmethod
    async def find_by_payment_hash(self, payment_hash: str) -> BTCInvoice | None:
        pass
