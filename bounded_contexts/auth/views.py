from dataclasses import dataclass

from bounded_contexts.auth.aggregates import Account
from bounded_contexts.auth.repositories import account_repository
from infrastructure.event_bus import make_unit_of_work
from utils.hash_utils import HashUtils
from utils.jwt import JWTUtils


@dataclass(frozen=True)
class LoginTokenView:
    account_id: str
    token: str


async def create_login_token_view(username: str, password: str) -> LoginTokenView:
    async with make_unit_of_work() as uow:
        account: Account | None = await account_repository(uow).find_by_username(
            username=username,
        )

    if account is None:
        raise Exception(f"Invalid login.")

    valid_hash = await HashUtils.verify(
        plain_text=password,
        hashed_text=account.password,
    )

    if not valid_hash:
        raise Exception(f"Invalid login.")

    return LoginTokenView(
        account_id=account.account_id,
        token=await JWTUtils.create_token(
            payload={"account_id": account.account_id}
        ),
    )
