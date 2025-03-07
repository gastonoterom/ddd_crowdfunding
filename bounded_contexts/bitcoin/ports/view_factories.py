from abc import ABC, abstractmethod

from bounded_contexts.bitcoin.views import InvoiceView


class InvoiceViewFactory(ABC):
    @abstractmethod
    async def create_invoice_view(self, payment_hash: str) -> InvoiceView:
        pass
