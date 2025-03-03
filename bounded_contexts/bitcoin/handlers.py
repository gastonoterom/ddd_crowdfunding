from bounded_contexts.bitcoin.aggregates import BTCInvoice, InvoiceStatus, InvoiceType
from bounded_contexts.bitcoin.messages import (
    CreateInvoice,
    InvoicePaidEvent,
    WithdrawalCreatedEvent,
)
from bounded_contexts.bitcoin.repositories import invoice_repository
from infrastructure.event_bus import UnitOfWork, event_bus


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
            )
        )


async def handle_invoice_paid_event(uow: UnitOfWork, event: InvoicePaidEvent) -> None:
    invoice = await invoice_repository(uow).find_by_invoice_id(event.invoice_id)

    assert invoice

    invoice.mark_as_paid()

    await invoice_repository(uow).update(invoice)


def register_bitcoin_handlers() -> None:
    event_bus.register_command_handler(CreateInvoice, handle_create_invoice)
    event_bus.register_event_handler(InvoicePaidEvent, handle_invoice_paid_event)
