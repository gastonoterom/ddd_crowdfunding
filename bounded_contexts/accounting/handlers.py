from bounded_contexts.accounting.adapters.repositories import account_repository
from bounded_contexts.accounting.aggregates import (
    Account,
    account_transfer,
)
from bounded_contexts.accounting.messages import (
    RequestTransferCommand,
    DepositCommand,
    WithdrawSucceededEvent,
    RequestWithdrawCommand,
    WithdrawRejectedEvent,
    TransferSucceededEvent,
)
from bounded_contexts.auth.messages import SignupEvent
from infrastructure.events.bus import event_bus
from infrastructure.events.uow_factory import make_unit_of_work


async def handle_account_created_event(event: SignupEvent) -> None:
    account = Account(account_id=event.account_id)

    async with make_unit_of_work() as uow:
        await account_repository(uow).add(account)


async def handle_transfer(
    command: RequestTransferCommand,
) -> None:
    async with make_unit_of_work() as uow:
        initiator = await account_repository(uow).find_by_id(command.from_account_id)
        recipient = await account_repository(uow).find_by_id(command.to_account_id)

        assert initiator and recipient

        account_transfer(
            idempotency_key=command.idempotency_key,
            from_account=initiator,
            to_account=recipient,
            amount=command.amount,
            metadata=command.metadata,
        )

        uow.emit(
            TransferSucceededEvent(
                idempotency_key=command.idempotency_key,
                from_account_id=command.from_account_id,
                to_account_id=command.to_account_id,
                amount=command.amount,
                metadata=command.metadata,
            )
        )


async def handle_deposit(
    command: DepositCommand,
) -> None:
    async with make_unit_of_work() as uow:
        account = await account_repository(uow).find_by_id(command.account_id)

        assert account

        account.deposit(
            idempotency_key=command.idempotency_key,
            amount=command.amount,
            metadata={},
        )


async def handle_withdraw_request(
    event: RequestWithdrawCommand,
) -> None:
    async with make_unit_of_work() as uow:
        account = await account_repository(uow).find_by_id(event.account_id)

        assert account

        try:
            account.withdraw(
                idempotency_key=event.idempotency_key,
                amount=event.amount,
                metadata=event.metadata,
            )

            uow.emit(
                WithdrawSucceededEvent(
                    idempotency_key=event.idempotency_key,
                    account_id=event.account_id,
                    amount=event.amount,
                    metadata=event.metadata,
                )
            )

        except ValueError:
            uow.emit(
                WithdrawRejectedEvent(
                    idempotency_key=event.idempotency_key,
                    account_id=event.account_id,
                    amount=event.amount,
                    metadata=event.metadata,
                )
            )


def register_accounting_handlers() -> None:
    event_bus.register_event_handler(SignupEvent, handle_account_created_event)

    event_bus.register_command_handler(
        RequestTransferCommand,
        handle_transfer,
    )

    event_bus.register_command_handler(
        DepositCommand,
        handle_deposit,
    )

    event_bus.register_command_handler(RequestWithdrawCommand, handle_withdraw_request)
