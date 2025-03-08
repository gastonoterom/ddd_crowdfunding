from bounded_contexts.accounting.messages import (
    RequestWithdrawCommand,
    WithdrawSucceededEvent,
    WithdrawRejectedEvent,
    DepositCommand,
)
from bounded_contexts.bitcoin.adapters.btc_processor import btc_processor
from bounded_contexts.bitcoin.adapters.repositories import invoice_repository
from bounded_contexts.bitcoin.aggregates import BTCInvoice, InvoiceStatus, InvoiceType
from bounded_contexts.bitcoin.messages import (
    CreateInvoice,
    VerifyInvoice,
)
from infrastructure.events.bus import event_bus
from infrastructure.events.uow_factory import make_unit_of_work


async def handle_create_invoice(command: CreateInvoice) -> None:
    async with make_unit_of_work() as uow:
        repository = invoice_repository(uow)

        invoice: BTCInvoice | None = await repository.find_by_id(command.payment_hash)

        # For idempotency purposes
        if invoice is None:
            invoice = BTCInvoice(
                account_id=command.account_id,
                amount=command.amount,
                status=InvoiceStatus.PENDING,
                payment_hash=command.payment_hash,
                payment_request=command.payment_request,
                invoice_type=command.invoice_type,
            )

            await invoice_repository(uow).add(invoice)

        assert invoice

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


async def handle_verify_invoice(command: VerifyInvoice) -> None:
    is_paid = await btc_processor().is_invoice_paid(
        payment_hash=command.payment_hash,
    )

    if not is_paid:
        raise Exception("Invoice not paid")

    async with make_unit_of_work() as uow:
        invoice = await invoice_repository(uow).find_by_id(command.payment_hash)

        assert invoice

        invoice.mark_as_paid()

        uow.emit(
            DepositCommand(
                account_id=invoice.account_id,
                idempotency_key=invoice.payment_hash,
                amount=invoice.amount,
                metadata={
                    "payment_hash": invoice.payment_hash,
                    "payment_request": invoice.payment_request,
                },
            )
        )


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
    event_bus.register_command_handler(
        VerifyInvoice,
        handle_verify_invoice,
    )
    event_bus.register_event_handler(
        WithdrawSucceededEvent,
        handle_withdraw_accepted_event,
    )
    event_bus.register_event_handler(
        WithdrawRejectedEvent,
        handle_withdraw_rejected_event,
    )
