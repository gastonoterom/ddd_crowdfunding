from abc import abstractmethod, ABC

from bounded_contexts.auth.aggregates import Account
from bounded_contexts.common.ports.repositories import Repository


# Abstract repository
class AccountRepository(Repository[Account], ABC):
    pass
