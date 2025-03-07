import json

from bounded_contexts.accounting.aggregates import Account, Transaction
from bounded_contexts.accounting.ports.repositories import AccountRepository
from bounded_contexts.common.adapters.repository_adapters import MockRepository
from infrastructure.events.unit_of_work import (
    UnitOfWork,
    PostgresUnitOfWork,
    MockUnitOfWork,
)


# Postgres implementation
class PostgresAccountRepository(AccountRepository):

    def __init__(self, uow: PostgresUnitOfWork) -> None:
        super().__init__(uow)
        self.uow = uow

    async def _find_by_id(self, entity_id: str) -> Account | None:
        row = await self.uow.conn.fetchrow(
            """
            SELECT 
                a.account_id, a.transactions, a.balance 
            FROM accounting_accounts a WHERE account_id = $1
            """,
            entity_id,
        )

        if not row:
            return None

        transactions = [
            Transaction(**transaction)
            for transaction in json.loads(row["transactions"])
        ]

        return Account(
            account_id=row["account_id"],
            transactions=transactions,
            balance=int(row["balance"]),
        )

    async def _add(self, entity: Account) -> None:
        transactions = json.dumps(
            [transaction.__dict__ for transaction in entity._transactions]
        )

        await self.uow.conn.execute(
            """
            INSERT INTO accounting_accounts (account_id, transactions, balance)
            VALUES ($1, $2, $3)
            """,
            entity.account_id,
            transactions,
            entity.balance,
        )

    async def _update(self, entity: Account) -> None:
        transactions = json.dumps(
            [transaction.__dict__ for transaction in entity._transactions]
        )

        await self.uow.conn.execute(
            """
            UPDATE accounting_accounts
            SET transactions = $2, balance = $3
            WHERE account_id = $1
            """,
            entity.account_id,
            transactions,
            entity.balance,
        )


# Mock repository for tests
class MockAccountRepository(AccountRepository, MockRepository[Account]):
    pass


def account_repository(uow: UnitOfWork) -> AccountRepository:
    if isinstance(uow, PostgresUnitOfWork):
        return PostgresAccountRepository(uow)

    if isinstance(uow, MockUnitOfWork):
        return MockAccountRepository(uow)

    raise Exception("Unsupported UnitOfWork type.")
