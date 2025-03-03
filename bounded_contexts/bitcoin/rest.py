from uuid import uuid4

import bolt11
from fastapi import FastAPI
from pydantic import BaseModel

from bounded_contexts.bitcoin.aggregates import InvoiceStatus
from bounded_contexts.bitcoin.messages import (
    CreateInvoice,
    InvoicePaidEvent,
    InvoiceType,
)
from bounded_contexts.bitcoin.views import get_invoice_view
from infrastructure.event_bus import event_bus
from infrastructure.ln_bits import create_invoice, is_invoice_paid, pay_invoice


def register_bitcoin_routes(app: FastAPI) -> None:
    class CreateInvoiceRequest(BaseModel):
        # TODO: Real security
        account_id: str
        amount: int

    class CreateInvoiceResponse(BaseModel):
        invoice_id: str
        payment_hash: str
        payment_request: str

    @app.post("/bitcoin/deposit")
    async def post_deposit(body: CreateInvoiceRequest) -> CreateInvoiceResponse:
        invoice_id = uuid4().hex

        ln_bits = await create_invoice(
            invoice_id=invoice_id,
            satoshis=body.amount,
        )

        command = CreateInvoice(
            invoice_id=invoice_id,
            account_id=body.account_id,
            amount=body.amount,
            payment_request=ln_bits.payment_request,
            payment_hash=ln_bits.payment_hash,
            invoice_type=InvoiceType.DEPOSIT,
        )

        await event_bus.handle(command)

        return CreateInvoiceResponse(
            invoice_id=invoice_id,
            payment_hash=ln_bits.payment_hash,
            payment_request=ln_bits.payment_request,
        )

    # TODO: Security
    class VerifyInvoiceRequest(BaseModel):
        payment_hash: str

    # TODO: There should be a periodic event for this
    @app.post("/bitcoin/verify_deposit")
    async def put_Verify_deposit(body: VerifyInvoiceRequest) -> None:
        is_paid = await is_invoice_paid(
            payment_hash=body.payment_hash,
        )

        if not is_paid:
            raise Exception("Invoice not paid")

        invoice_view = await get_invoice_view(payment_hash=body.payment_hash)

        # If the invoice is already paid, we don't need to do anything else
        if invoice_view.status == InvoiceStatus.PAID:
            return

        await event_bus.handle(
            InvoicePaidEvent(
                invoice_id=invoice_view.invoice_id,
                account_id=invoice_view.account_id,
                amount=invoice_view.amount,
            )
        )

    # TODO: Security
    class WithdrawRequest(BaseModel):
        account_id: str
        encoded_invoice: str

    @app.post("/bitcoin/withdraw")
    async def post_withdraw(body: WithdrawRequest) -> None:
        invoice_id = uuid4().hex
        invoice = bolt11.decode(body.encoded_invoice)
        amount = int(invoice.amount_msat / 1000)

        assert invoice.currency == "bc"
        assert invoice.has_payment_hash

        command = CreateInvoice(
            invoice_id=invoice_id,
            account_id=body.account_id,
            amount=amount,
            payment_request=body.encoded_invoice,
            payment_hash=invoice.payment_hash,
            invoice_type=InvoiceType.WITHDRAWAL,
        )

        await event_bus.handle(command)

        await pay_invoice(body.encoded_invoice)
