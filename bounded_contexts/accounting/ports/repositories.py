from abc import ABC

from bounded_contexts.accounting.aggregates import Account
from bounded_contexts.common.ports.repositories import Repository


# Abstract repository
class AccountRepository(Repository[Account], ABC):
    pass
