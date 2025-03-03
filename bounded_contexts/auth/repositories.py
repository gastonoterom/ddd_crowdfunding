from abc import ABC, abstractmethod

from bounded_contexts.auth.aggregates import Account
from infrastructure.event_bus import UnitOfWork, PostgresUnitOfWork


# Abstract repository
class AccountRepository(ABC):

    @abstractmethod
    async def find_by_username(self, username: str) -> Account | None:
        pass

    @abstractmethod
    async def save(self, account: Account) -> None:
        pass


# Postgres implementation
class PostgresAccountRepository(AccountRepository):

    def __init__(self, uow: PostgresUnitOfWork) -> None:
        self.uow = uow

    @staticmethod
    def repository_ddl() -> str:
        return """
        CREATE TABLE IF NOT EXISTS auth_accounts (
            account_id VARCHAR PRIMARY KEY,
            username VARCHAR NOT NULL UNIQUE,
            password VARCHAR NOT NULL
        );
        """

    async def find_by_username(self, username: str) -> Account | None:

        row = await self.uow.conn.fetchrow(
            "SELECT account_id, username, password FROM auth_accounts WHERE username = $1",
            username,
        )

        if row is None:
            return None

        return Account(
            account_id=row["account_id"],
            username=row["username"],
            password=row["password"],
        )

    async def save(self, account: Account) -> None:
        await self.uow.conn.execute(
            """
            INSERT INTO auth_accounts (account_id, username, password)
            VALUES ($1, $2, $3)
            """,
            account.account_id,
            account.username,
            account.password,
        )


# Account repository factory, based on the type of UnitOfWork
def account_repository(uow: UnitOfWork) -> AccountRepository:
    if isinstance(uow, PostgresUnitOfWork):
        return PostgresAccountRepository(uow)

    raise Exception("Unsupported UnitOfWork type.")
