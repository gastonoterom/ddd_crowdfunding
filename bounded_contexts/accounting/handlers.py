from bounded_contexts.accounting.aggregates import (
    Account,
    account_transfer,
    Deposit,
    Withdrawal,
)
from bounded_contexts.accounting.repositories import account_repository
from bounded_contexts.auth.events import SignupEvent
from bounded_contexts.bitcoin.aggregates import InvoiceType
from bounded_contexts.bitcoin.messages import (
    DepositInvoicePaidEvent,
    WithdrawalCreatedEvent,
)
from bounded_contexts.crowdfunding.events import DonationCreatedEvent
from infrastructure.event_bus import UnitOfWork, event_bus


async def handle_account_created_event(uow: UnitOfWork, event: SignupEvent) -> None:
    account = Account(account_id=event.account_id)

    await account_repository(uow).add(account)


async def handle_donation_created_event(
    uow: UnitOfWork, event: DonationCreatedEvent
) -> None:
    donor = await account_repository(uow).find_by_account_id(event.donor_account_id)
    recipient = await account_repository(uow).find_by_account_id(
        event.recipient_account_id
    )

    assert donor and recipient

    account_transfer(
        idempotency_key=event.idempotency_key,
        from_account=donor,
        to_account=recipient,
        amount=event.amount,
    )

    await account_repository(uow).update(donor)
    await account_repository(uow).update(recipient)


async def handle_invoice_paid_event(
    uow: UnitOfWork,
    event: DepositInvoicePaidEvent,
) -> None:
    assert event.invoice_type == InvoiceType.DEPOSIT

    account = await account_repository(uow).find_by_account_id(event.account_id)

    assert account

    account.deposit(
        Deposit(
            idempotency_key=event.invoice_id,
            amount=event.amount,
        )
    )

    await account_repository(uow).update(account)


async def handle_withdrawal_crated_event(
    uow: UnitOfWork,
    event: WithdrawalCreatedEvent,
) -> None:
    assert event.invoice_type == InvoiceType.WITHDRAWAL

    account = await account_repository(uow).find_by_account_id(event.account_id)

    assert account

    account.withdraw(
        Withdrawal(
            idempotency_key=event.invoice_id,
            amount=event.amount,
        )
    )

    await account_repository(uow).update(account)


def register_accounting_handlers() -> None:
    event_bus.register_event_handler(SignupEvent, handle_account_created_event)
    event_bus.register_event_handler(
        DonationCreatedEvent,
        handle_donation_created_event,
    )
    event_bus.register_event_handler(DepositInvoicePaidEvent, handle_invoice_paid_event)
    event_bus.register_event_handler(
        WithdrawalCreatedEvent, handle_withdrawal_crated_event
    )
