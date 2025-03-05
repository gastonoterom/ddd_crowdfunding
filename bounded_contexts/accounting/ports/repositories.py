from abc import ABC

from bounded_contexts.accounting.aggregates import Account, Deposit, Withdrawal
from bounded_contexts.common.repositories import Repository
from infrastructure.event_bus import UnitOfWork, PostgresUnitOfWork, MockUnitOfWork


# Abstract repository
class AccountRepository(Repository[Account], ABC):
    pass
