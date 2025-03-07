from bounded_contexts.accounting.messages import (
    RequestWithdrawCommand,
    WithdrawSucceededEvent,
    WithdrawRejectedEvent,
)
from bounded_contexts.bitcoin.adapters.btc_processor import btc_processor
from bounded_contexts.bitcoin.adapters.repositories import invoice_repository
from bounded_contexts.bitcoin.aggregates import BTCInvoice, InvoiceStatus, InvoiceType
from bounded_contexts.bitcoin.messages import (
    CreateInvoice,
    DepositInvoicePaidEvent,
)
from infrastructure.events.bus import event_bus
from infrastructure.events.uow_factory import make_unit_of_work


async def handle_create_invoice(command: CreateInvoice) -> None:
    async with make_unit_of_work() as uow:
        invoice = BTCInvoice(
            account_id=command.account_id,
            amount=command.amount,
            status=InvoiceStatus.PENDING,
            payment_hash=command.payment_hash,
            payment_request=command.payment_request,
            invoice_type=command.invoice_type,
        )

        await invoice_repository(uow).add(invoice)

        if command.invoice_type == InvoiceType.WITHDRAWAL:
            uow.emit(
                RequestWithdrawCommand(
                    idempotency_key=invoice.payment_hash,
                    account_id=invoice.account_id,
                    amount=invoice.amount,
                    metadata={
                        "payment_hash": invoice.payment_hash,
                        "payment_request": invoice.payment_request,
                    },
                )
            )


async def handle_deposit_invoice_paid_event(event: DepositInvoicePaidEvent) -> None:
    async with make_unit_of_work() as uow:
        invoice = await invoice_repository(uow).find_by_id(event.payment_hash)

        assert invoice

        invoice.mark_as_paid()


async def handle_withdraw_accepted_event(event: WithdrawSucceededEvent) -> None:
    payment_hash: str | None = event.metadata.get("payment_hash", None)
    payment_request: str | None = event.metadata.get("payment_request", None)

    if payment_hash is None or payment_request is None:
        return

    await btc_processor().pay_invoice(payment_request)

    async with make_unit_of_work() as uow:
        invoice = await invoice_repository(uow).find_by_id(payment_hash)
        assert invoice

        invoice.mark_as_paid()


async def handle_withdraw_rejected_event(event: WithdrawRejectedEvent) -> None:
    payment_hash: str | None = event.metadata.get("payment_hash", None)
    payment_request: str | None = event.metadata.get("payment_request", None)

    if payment_hash is None or payment_request is None:
        return

    async with make_unit_of_work() as uow:
        invoice = await invoice_repository(uow).find_by_id(payment_hash)
        assert invoice

        invoice.mark_as_rejected()


def register_bitcoin_handlers() -> None:
    event_bus.register_command_handler(CreateInvoice, handle_create_invoice)
    event_bus.register_event_handler(
        DepositInvoicePaidEvent, handle_deposit_invoice_paid_event
    )
