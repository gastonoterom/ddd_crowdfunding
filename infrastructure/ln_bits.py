# TODO: This is an adapter, move elsewhere
from dataclasses import dataclass

import httpx

from config.env import lnbits_environment


@dataclass
class LNBitsInvoice:
    payment_hash: str
    payment_request: str


async def create_invoice(invoice_id: str, satoshis: int) -> LNBitsInvoice:
    headers = {
        "X-Api-Key": lnbits_environment.invoice_key,
        "Content-Type": "application/json",
    }
    data = {"out": False, "amount": satoshis, "memo": invoice_id}

    async with httpx.AsyncClient() as client:
        response = await client.post(
            lnbits_environment.api_url, json=data, headers=headers
        )

    if response.status_code == 201:
        invoice_data = response.json()

        return LNBitsInvoice(
            payment_hash=invoice_data["payment_hash"],
            payment_request=invoice_data["payment_request"],
        )
    else:
        raise Exception(f"Error creating invoice: {response}")


async def is_invoice_paid(payment_hash: str) -> bool:
    headers = {
        "X-Api-Key": lnbits_environment.invoice_key,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            lnbits_environment.api_url + "/" + payment_hash, headers=headers
        )

    return bool(response.json()["paid"])


async def pay_invoice(payment_request: str) -> None:
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
