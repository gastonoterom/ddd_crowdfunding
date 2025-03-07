from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class InvoiceData:
    payment_hash: str
    payment_request: str


class BitcoinLightningProcessor(ABC):
    @abstractmethod
    async def create_invoice(self, satoshis: int) -> InvoiceData:
        pass

    @abstractmethod
    async def is_invoice_paid(self, payment_hash: str) -> bool:
        pass

    @abstractmethod
    async def pay_invoice(self, payment_request: str) -> None:
        pass
