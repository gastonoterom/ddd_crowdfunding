from bounded_contexts.auth.adapters.repositories import account_repository
from bounded_contexts.auth.aggregates import Account
from bounded_contexts.auth.messages import RegisterAccount, SignupEvent
from infrastructure.events.bus import event_bus
from infrastructure.events.unit_of_work import UnitOfWork


async def handle_register(
    uow: UnitOfWork,
    command: RegisterAccount,
) -> None:
    existing_account: Account | None = await account_repository(uow).find_by_username(
        command["username"]
    )

    assert (
        existing_account is None
    ), f"Account with username {command['username']} already exists"

    account = Account(
        account_id=command["account_id"],
        username=command["username"].lower(),
        password=command["hashed_password"],
    )

    await account_repository(uow).add(account)

    uow.emit(SignupEvent(account_id=account.account_id))


def register_auth_handlers() -> None:
    event_bus.register_command_handler(RegisterAccount, handle_register)
