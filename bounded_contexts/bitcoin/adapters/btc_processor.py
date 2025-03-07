import httpx

from bounded_contexts.bitcoin.ports.btc_processor import (
    BitcoinLightningProcessor,
    InvoiceData,
)
from config.env import lnbits_environment


class LNBitsProcessor(BitcoinLightningProcessor):

    async def create_invoice(self, satoshis: int) -> InvoiceData:
        headers = {
            "X-Api-Key": lnbits_environment.invoice_key,
            "Content-Type": "application/json",
        }

        data = {"out": False, "amount": satoshis}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                lnbits_environment.api_url, json=data, headers=headers
            )

        if response.status_code == 201:
            invoice_data = response.json()

            return InvoiceData(
                payment_hash=invoice_data["payment_hash"],
                payment_request=invoice_data["payment_request"],
            )
        else:
            raise Exception(f"Error creating invoice: {response}")

    async def is_invoice_paid(self, payment_hash: str) -> bool:
        headers = {
            "X-Api-Key": lnbits_environment.invoice_key,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                lnbits_environment.api_url + "/" + payment_hash, headers=headers
            )

        return bool(response.json()["paid"])

    async def pay_invoice(self, payment_request: str) -> None:
        headers = {
            "X-Api-Key": lnbits_environment.admin_key,
            "Content-Type": "application/json",
        }
        data = {"out": True, "bolt11": payment_request}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                lnbits_environment.api_url, json=data, headers=headers
            )
            assert response.status_code == 201, f"Error paying invoice: {response}"


def btc_processor() -> BitcoinLightningProcessor:
    return LNBitsProcessor()
