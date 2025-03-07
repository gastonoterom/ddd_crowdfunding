from bounded_contexts.auth.ports.view_factories import AccountViewFactory
from bounded_contexts.auth.views import SensitiveAccountView, AccountView
from infrastructure.postgres import postgres_pool


class PostgresAccountViewFactory(AccountViewFactory):

    async def create_view(self, account_id: str) -> AccountView:
        async with postgres_pool.get_pool().acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    a.account_id,
                    a.username
                FROM auth_accounts a
                WHERE account_id = $1
                """,
                account_id,
            )

        assert row

        return AccountView(
            account_id=row["account_id"],
            username=row["username"],
        )

    async def create_sensitive_view(self, username: str) -> SensitiveAccountView | None:
        async with postgres_pool.get_pool().acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    a.account_id,
                    a.username,
                    a.password
                FROM auth_accounts a
                WHERE username = $1
                """,
                username,
            )

        if row is None:
            return row

        return SensitiveAccountView(
            account_id=row["account_id"],
            username=row["username"],
            password_hash=row["password"],
        )


def account_view_factory() -> AccountViewFactory:
    return PostgresAccountViewFactory()
