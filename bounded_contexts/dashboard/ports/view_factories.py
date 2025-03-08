from abc import abstractmethod, ABC

from bounded_contexts.dashboard.views import DashboardView


class DashboardViewFactory(ABC):
    @abstractmethod
    async def create_dashboard_view(self, account_id: str) -> DashboardView:
        pass
