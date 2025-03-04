from bounded_contexts.auth.aggregates import Account
from bounded_contexts.auth.commands import RegisterAccount
from bounded_contexts.auth.events import SignupEvent
from bounded_contexts.auth.repositories import account_repository
from infrastructure.event_bus import UnitOfWork, event_bus


async def handle_register(
    uow: UnitOfWork,
    command: RegisterAccount,
) -> None:
    existing_account: Account | None = await account_repository(uow).find_by_username(
        command.username
    )

    if existing_account:
        raise ValueError("Account with this username already exists")

    account = Account(
        account_id=command.account_id,
        username=command.username.lower(),
        password=command.hashed_password,
    )

    await account_repository(uow).save(account)

    uow.emit(SignupEvent(account_id=account.account_id))


def register_auth_handlers() -> None:
    event_bus.register_command_handler(RegisterAccount, handle_register)
