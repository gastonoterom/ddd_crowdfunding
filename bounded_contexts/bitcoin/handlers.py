from bounded_contexts.bitcoin.adapters.repositories import invoice_repository
from bounded_contexts.bitcoin.aggregates import BTCInvoice, InvoiceStatus, InvoiceType
from bounded_contexts.bitcoin.messages import (
    CreateInvoice,
    DepositInvoicePaidEvent,
    WithdrawalCreatedEvent,
)
from infrastructure.events.bus import event_bus
from infrastructure.events.unit_of_work import UnitOfWork


async def handle_create_invoice(uow: UnitOfWork, command: CreateInvoice) -> None:
    invoice = BTCInvoice(
        invoice_id=command.invoice_id,
        account_id=command.account_id,
        amount=command.amount,
        status=InvoiceStatus.PENDING,
        payment_hash=command.payment_hash,
        payment_request=command.payment_request,
        invoice_type=command.invoice_type,
    )

    await invoice_repository(uow).add(invoice)

    if command.invoice_type == InvoiceType.WITHDRAWAL:
        # TODO: handle consistency with a transactional outbox
        uow.emit(
            WithdrawalCreatedEvent(
                invoice_id=invoice.invoice_id,
                account_id=invoice.account_id,
                amount=invoice.amount,
                invoice_type=InvoiceType.WITHDRAWAL,
            )
        )


async def handle_invoice_paid_event(
    uow: UnitOfWork, event: DepositInvoicePaidEvent
) -> None:
    invoice = await invoice_repository(uow).find_by_id(event.invoice_id)

    assert invoice

    invoice.mark_as_paid()


def register_bitcoin_handlers() -> None:
    event_bus.register_command_handler(CreateInvoice, handle_create_invoice)
    event_bus.register_event_handler(DepositInvoicePaidEvent, handle_invoice_paid_event)
