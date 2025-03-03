import json
from abc import ABC, abstractmethod

from bounded_contexts.accounting.aggregates import Account, Deposit, Withdrawal
from infrastructure.event_bus import UnitOfWork, PostgresUnitOfWork


# Abstract repository
class AccountRepository(ABC):

    @abstractmethod
    async def add(self, account: Account) -> None:
        pass

    @abstractmethod
    async def update(self, account: Account) -> None:
        pass

    @abstractmethod
    async def find_by_account_id(self, account_id: str) -> Account | None:
        pass


# Postgres implementation
class PostgresAccountRepository(AccountRepository):

    def __init__(self, uow: PostgresUnitOfWork) -> None:
        self.uow = uow

    # TODO: Handle migrations
    @staticmethod
    def repository_ddl() -> str:
        return """
        CREATE TABLE IF NOT EXISTS accounting_accounts (
            account_id VARCHAR PRIMARY KEY,
            deposits JSONB,
            withdrawals JSONB,
            version INT
        );
        """

    async def find_by_account_id(self, account_id: str) -> Account | None:
        row = await self.uow.conn.fetchrow(
            """
            SELECT * FROM accounting_accounts WHERE account_id = $1
            """,
            account_id,
        )

        if not row:
            return None

        deposits = [Deposit(**deposit) for deposit in json.loads(row["deposits"])]
        withdrawals = [
            Withdrawal(**withdrawal) for withdrawal in json.loads(row["withdrawals"])
        ]

        return Account(
            account_id=row["account_id"],
            deposits=deposits,
            withdrawals=withdrawals,
            version=row["version"],
        )

    async def add(self, account: Account) -> None:
        deposits = json.dumps([deposit.__dict__ for deposit in account._deposits])
        withdrawals = json.dumps(
            [withdrawal.__dict__ for withdrawal in account._withdrawals]
        )

        await self.uow.conn.execute(
            """
            INSERT INTO accounting_accounts (account_id, deposits, withdrawals, version)
            VALUES ($1, $2, $3, $4)
            """,
            account.account_id,
            deposits,
            withdrawals,
            account._version,
        )

    async def update(self, account: Account) -> None:
        deposits = json.dumps([deposit.__dict__ for deposit in account._deposits])
        withdrawals = json.dumps(
            [withdrawal.__dict__ for withdrawal in account._withdrawals]
        )

        await self.uow.conn.execute(
            """
            UPDATE accounting_accounts
            SET deposits = $2, withdrawals = $3, version = $4
            WHERE account_id = $1
            """,
            account.account_id,
            deposits,
            withdrawals,
            account._version,
        )


# Account repository factory, based on the type of UnitOfWork
def account_repository(uow: UnitOfWork) -> AccountRepository:
    if isinstance(uow, PostgresUnitOfWork):
        return PostgresAccountRepository(uow)

    raise Exception("Unsupported UnitOfWork type.")
