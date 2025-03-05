from bounded_contexts.auth.aggregates import Account
from bounded_contexts.auth.ports.repositories import AccountRepository
from infrastructure.event_bus import UnitOfWork, PostgresUnitOfWork


# Postgres implementation
class PostgresAccountRepository(AccountRepository):

    def __init__(self, uow: PostgresUnitOfWork) -> None:
        super().__init__(uow)
        self.uow = uow

    async def _find_by_id(self, entity_id: str) -> Account | None:

        row = await self.uow.conn.fetchrow(
            "SELECT account_id, username, password FROM auth_accounts WHERE account_id = $1",
            entity_id,
        )

        if row is None:
            return None

        return Account(
            account_id=row["account_id"],
            username=row["username"],
            password=row["password"],
        )

    async def _add(self, entity: Account) -> None:
        await self.uow.conn.execute(
            """
            INSERT INTO auth_accounts (account_id, username, password)
            VALUES ($1, $2, $3)
            """,
            entity.account_id,
            entity.username,
            entity.password,
        )

    # TODO: This method
    async def _update(self, entity: Account) -> None:
        raise NotImplementedError()

    # TODO: This doesn't belong here
    async def find_by_username(self, username: str) -> Account | None:
        raise NotImplementedError()


# Account repository factory, based on the type of UnitOfWork
def account_repository(uow: UnitOfWork) -> AccountRepository:
    if isinstance(uow, PostgresUnitOfWork):
        return PostgresAccountRepository(uow)

    raise Exception("Unsupported UnitOfWork type.")
