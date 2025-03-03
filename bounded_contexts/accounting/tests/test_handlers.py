import pytest

from bounded_contexts.accounting.aggregates import Account, Deposit
from bounded_contexts.accounting.handlers import (
    handle_account_created_event,
    handle_donation_created_event,
    handle_invoice_paid_event,
    handle_withdrawal_crated_event,
)
from bounded_contexts.accounting.repositories import account_repository
from bounded_contexts.auth.events import SignupEvent
from bounded_contexts.bitcoin.aggregates import InvoiceType
from bounded_contexts.bitcoin.messages import (
    DepositInvoicePaidEvent,
    WithdrawalCreatedEvent,
)
from bounded_contexts.crowdfunding.events import DonationCreatedEvent
from infrastructure.event_bus import make_unit_of_work


account_id = "account_id"
account_2_id = "account_2_id"

idempotency_key = "idempotency_key"


@pytest.mark.asyncio
async def test_handle_account_created_event() -> None:
    event = SignupEvent(account_id=account_id)

    async with make_unit_of_work() as uow:
        await handle_account_created_event(uow, event)

        account = await account_repository(uow).find_by_account_id(
            account_id=account_id,
        )

        assert account.account_id == account_id
        assert account.available_funds == 0


@pytest.mark.asyncio
async def test_handle_donation_created_event() -> None:
    async with make_unit_of_work() as uow:
        account_1 = Account(account_id=account_id)
        account_2 = Account(account_id=account_2_id)

        account_1.deposit(Deposit(idempotency_key=idempotency_key, amount=150))

        await account_repository(uow).add(account_1)
        await account_repository(uow).add(account_2)

    event = DonationCreatedEvent(
        idempotency_key=idempotency_key,
        donor_account_id=account_id,
        recipient_account_id=account_2_id,
        amount=100,
    )

    async with make_unit_of_work() as uow:
        await handle_donation_created_event(uow, event)

        account_1 = await account_repository(uow).find_by_account_id(
            account_id=account_id,
        )

        assert account_1.account_id == account_id
        assert account_1.available_funds == 50

        account_2 = await account_repository(uow).find_by_account_id(
            account_id=account_2_id,
        )

        assert account_2.account_id == account_2_id
        assert account_2.available_funds == 100


@pytest.mark.asyncio
async def test_handle_invoice_paid_event() -> None:
    async with make_unit_of_work() as uow:
        account_1 = Account(account_id=account_id)
        await account_repository(uow).add(account_1)

    event = DepositInvoicePaidEvent(
        invoice_id=idempotency_key,
        account_id=account_id,
        amount=50,
        invoice_type=InvoiceType.DEPOSIT,
    )

    async with make_unit_of_work() as uow:
        await handle_invoice_paid_event(uow, event)

        account_1 = await account_repository(uow).find_by_account_id(
            account_id=account_id,
        )

        assert account_1.account_id == account_id
        assert account_1.available_funds == 50


@pytest.mark.asyncio
async def test_handle_withdrawal_crated_event() -> None:
    async with make_unit_of_work() as uow:
        account_1 = Account(account_id=account_id)
        account_1.deposit(Deposit(idempotency_key, 100))
        await account_repository(uow).add(account_1)

    event = WithdrawalCreatedEvent(
        invoice_id=idempotency_key,
        account_id=account_id,
        amount=70,
        invoice_type=InvoiceType.WITHDRAWAL,
    )

    async with make_unit_of_work() as uow:
        await handle_withdrawal_crated_event(uow, event)

        account_1 = await account_repository(uow).find_by_account_id(
            account_id=account_id,
        )

        assert account_1.account_id == account_id
        assert account_1.available_funds == 30
