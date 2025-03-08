from typing import Annotated

import bolt11
from fastapi import Depends, APIRouter
from pydantic import BaseModel

from bounded_contexts.bitcoin.adapters.btc_processor import btc_processor
from bounded_contexts.bitcoin.messages import (
    CreateInvoice,
    VerifyInvoice,
    InvoiceType,
)
from bounded_contexts.bitcoin.queries import get_invoice_view
from bounded_contexts.bitcoin.views import InvoiceView
from infrastructure.events.bus import event_bus
from infrastructure.fastapi import get_account_id


bitcoin_router = APIRouter()


class CreateInvoiceRequest(BaseModel):
    amount: int


@bitcoin_router.post("/bitcoin/deposit")
async def post_deposit_request(
    body: CreateInvoiceRequest,
    account_id: Annotated[str, Depends(get_account_id)],
) -> InvoiceView:
    invoice = await btc_processor().create_invoice(
        satoshis=body.amount,
    )

    command = CreateInvoice(
        payment_hash=invoice.payment_hash,
        account_id=account_id,
        amount=body.amount,
        payment_request=invoice.payment_request,
        invoice_type=InvoiceType.DEPOSIT,
    )

    await event_bus.handle(command)

    return await get_invoice_view(payment_hash=invoice.payment_hash)


class VerifyInvoiceRequest(BaseModel):
    payment_hash: str


@bitcoin_router.post("/bitcoin/verify_deposit")
async def put_verify_deposit(
    body: VerifyInvoiceRequest,
) -> None:
    await event_bus.handle(
        VerifyInvoice(
            payment_hash=body.payment_hash,
        )
    )


class WithdrawRequest(BaseModel):
    encoded_invoice: str


@bitcoin_router.post("/bitcoin/withdraw")
async def post_withdraw(
    body: WithdrawRequest,
    account_id: Annotated[str, Depends(get_account_id)],
) -> None:
    invoice = bolt11.decode(body.encoded_invoice)

    msat = invoice.amount_msat or 0
    amount = int(msat / 1000)

    assert invoice.currency == "bc"
    assert invoice.has_payment_hash

    command = CreateInvoice(
        payment_hash=invoice.payment_hash,
        account_id=account_id,
        amount=amount,
        payment_request=body.encoded_invoice,
        invoice_type=InvoiceType.WITHDRAWAL,
    )

    await event_bus.handle(command)
