from dataclasses import dataclass

from bounded_contexts.auth.adapters.repositories import account_repository
from bounded_contexts.auth.aggregates import Account
from infrastructure.event_bus import make_unit_of_work
from infrastructure.tools import verify_hash, create_jwt_token


@dataclass(frozen=True)
class LoginTokenView:
    account_id: str
    token: str


async def create_login_token_view(username: str, password: str) -> LoginTokenView:
    # TODO: uow is overkill, use view factories
    async with make_unit_of_work() as uow:
        account: Account | None = await account_repository(uow).find_by_username(
            username=username,
        )

    if account is None:
        raise Exception(f"Invalid login.")

    valid_hash = await verify_hash(
        plain_text=password,
        hashed_text=account.password,
    )

    if not valid_hash:
        raise Exception(f"Invalid login.")

    return LoginTokenView(
        account_id=account.account_id,
        token=await create_jwt_token(payload={"account_id": account.account_id}),
    )
