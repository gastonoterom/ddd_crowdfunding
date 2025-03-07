from bounded_contexts.auth.adapters.view_factories import account_view_factory
from bounded_contexts.auth.views import LoginTokenView
from infrastructure.tools import verify_hash, create_jwt_token


async def create_login_token_view(username: str, password: str) -> LoginTokenView:
    account = await account_view_factory().create_sensitive_view(username=username)

    assert account, "Invalid login."

    valid_hash = await verify_hash(
        plain_text=password,
        hashed_text=account.password_hash,
    )

    assert valid_hash, "Invalid login."

    return LoginTokenView(
        account_id=account.account_id,
        token=await create_jwt_token(payload={"account_id": account.account_id}),
    )
