from abc import ABC, abstractmethod

from bounded_contexts.auth.views import SensitiveAccountView, AccountView


class AccountViewFactory(ABC):

    @abstractmethod
    async def create_sensitive_view(self, username: str) -> SensitiveAccountView | None:
        pass

    @abstractmethod
    async def create_view(self, account_id: str) -> AccountView:
        pass
