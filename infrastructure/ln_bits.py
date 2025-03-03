from dataclasses import dataclass

import httpx

LNBITS_API_URL = "https://demo.lnbits.com/api/v1/payments"
ADMIN_KEY = "5847740bd3f14c40b57c198440050d4c"
INVOICE_KEY = "8bf12cd6363d48be8ccb52d01f0678bb"


@dataclass
class LNBitsInvoice:
    payment_hash: str
    payment_request: str


async def create_invoice(invoice_id: str, satoshis: int) -> LNBitsInvoice:
    headers = {"X-Api-Key": INVOICE_KEY, "Content-Type": "application/json"}
    data = {"out": False, "amount": satoshis, "memo": invoice_id}

    async with httpx.AsyncClient() as client:
        response = await client.post(LNBITS_API_URL, json=data, headers=headers)

    if response.status_code == 201:
        invoice_data = response.json()

        return LNBitsInvoice(
            payment_hash=invoice_data["payment_hash"],
            payment_request=invoice_data["payment_request"],
        )
    else:
        raise Exception(f"Error creating invoice: {response}")


async def is_invoice_paid(payment_hash: str) -> bool:
    headers = {"X-Api-Key": INVOICE_KEY, "Content-Type": "application/json"}

    async with httpx.AsyncClient() as client:
        response = await client.get(
            LNBITS_API_URL + "/" + payment_hash, headers=headers
        )

    return bool(response.json()["paid"])


async def pay_invoice(payment_request: str) -> None:
    headers = {"X-Api-Key": ADMIN_KEY, "Content-Type": "application/json"}
    data = {"out": True, "bolt11": payment_request}

    async with httpx.AsyncClient() as client:
        response = await client.post(LNBITS_API_URL, json=data, headers=headers)
        assert response.status_code == 201, f"Error paying invoice: {response}"
