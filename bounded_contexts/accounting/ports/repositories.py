from abc import ABC

from bounded_contexts.accounting.aggregates import Account, Deposit, Withdrawal
from bounded_contexts.common.ports.repositories import Repository
from infrastructure.events.unit_of_work import (
    UnitOfWork,
    PostgresUnitOfWork,
    MockUnitOfWork,
)


# Abstract repository
class AccountRepository(Repository[Account], ABC):
    pass
