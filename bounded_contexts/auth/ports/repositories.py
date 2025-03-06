from abc import abstractmethod

from bounded_contexts.auth.aggregates import Account
from bounded_contexts.common.ports.repositories import Repository


# Abstract repository
class AccountRepository(Repository[Account]):

    # TODO: Delete this method
    @abstractmethod
    async def find_by_username(self, username: str) -> Account | None:
        pass
