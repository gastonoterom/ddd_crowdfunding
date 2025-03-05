import json

from bounded_contexts.accounting.aggregates import Account, Deposit, Withdrawal
from bounded_contexts.accounting.ports.repositories import AccountRepository
from bounded_contexts.common.adapters.repository_adapters import MockRepository
from infrastructure.event_bus import UnitOfWork, PostgresUnitOfWork, MockUnitOfWork


# Postgres implementation
class PostgresAccountRepository(AccountRepository):

    def __init__(self, uow: PostgresUnitOfWork) -> None:
        super().__init__(uow)
        self.uow = uow

    async def _find_by_id(self, entity_id: str) -> Account | None:
        row = await self.uow.conn.fetchrow(
            """
            SELECT * FROM accounting_accounts WHERE account_id = $1
            """,
            entity_id,
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

    async def _add(self, entity: Account) -> None:
        deposits = json.dumps([deposit.__dict__ for deposit in entity._deposits])
        withdrawals = json.dumps(
            [withdrawal.__dict__ for withdrawal in entity._withdrawals]
        )

        await self.uow.conn.execute(
            """
            INSERT INTO accounting_accounts (account_id, deposits, withdrawals, version)
            VALUES ($1, $2, $3, $4)
            """,
            entity.account_id,
            deposits,
            withdrawals,
            entity._version,
        )

    async def _update(self, entity: Account) -> None:
        deposits = json.dumps([deposit.__dict__ for deposit in entity._deposits])
        withdrawals = json.dumps(
            [withdrawal.__dict__ for withdrawal in entity._withdrawals]
        )

        await self.uow.conn.execute(
            """
            UPDATE accounting_accounts
            SET deposits = $2, withdrawals = $3, version = $4
            WHERE account_id = $1
            """,
            entity.account_id,
            deposits,
            withdrawals,
            entity._version,
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
