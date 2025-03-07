from bounded_contexts.accounting.adapters.repositories import account_repository
from bounded_contexts.accounting.aggregates import (
    Account,
    account_transfer,
)
from bounded_contexts.accounting.messages import (
    Transfer,
    DepositCommand,
    TransactionSucceeded,
    RequestWithdrawCommand,
    TransactionRejected,
)
from bounded_contexts.auth.messages import SignupEvent
from bounded_contexts.bitcoin.adapters.rest import WithdrawRequest
from infrastructure.events.bus import event_bus
from infrastructure.events.unit_of_work import UnitOfWork


async def handle_account_created_event(uow: UnitOfWork, event: SignupEvent) -> None:
    account = Account(account_id=event.account_id)

    await account_repository(uow).add(account)


async def handle_transfer(
    uow: UnitOfWork,
    command: Transfer,
) -> None:
    initiator = await account_repository(uow).find_by_id(command.from_account_id)
    recipient = await account_repository(uow).find_by_id(command.to_account_id)

    assert initiator and recipient

    try:
        account_transfer(
            idempotency_key=command.idempotency_key,
            from_account=initiator,
            to_account=recipient,
            amount=command.amount,
        )

        uow.emit(
            TransactionSucceeded(
                idempotency_key=command.idempotency_key,
            )
        )

    except ValueError:
        uow.emit(
            TransactionRejected(
                idempotency_key=command.idempotency_key,
            )
        )


async def handle_deposit(
    uow: UnitOfWork,
    command: DepositCommand,
) -> None:
    account = await account_repository(uow).find_by_id(command.account_id)

    assert account

    account.deposit(
        idempotency_key=command.idempotency_key,
        amount=command.amount,
    )


async def handle_withdraw_request(
    uow: UnitOfWork,
    event: RequestWithdrawCommand,
) -> None:
    account = await account_repository(uow).find_by_id(event.account_id)

    assert account

    try:
        account.withdraw(
            idempotency_key=event.idempotency_key,
            amount=event.amount,
        )

        uow.emit(
            TransactionSucceeded(
                idempotency_key=event.idempotency_key,
            )
        )

    except ValueError:
        uow.emit(
            TransactionRejected(
                idempotency_key=event.idempotency_key,
            )
        )


def register_accounting_handlers() -> None:
    event_bus.register_event_handler(SignupEvent, handle_account_created_event)

    event_bus.register_event_handler(
        Transfer,
        handle_transfer,
    )

    event_bus.register_event_handler(
        DepositCommand,
        handle_deposit,
    )

    event_bus.register_event_handler(WithdrawRequest, handle_withdraw_request)
