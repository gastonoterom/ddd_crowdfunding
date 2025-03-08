from bounded_contexts.dashboard.adapters.view_factories import dashboard_view_factory
from bounded_contexts.dashboard.views import DashboardView


async def view_dashboard(account_id: str) -> DashboardView:
    return await dashboard_view_factory().create_dashboard_view(account_id=account_id)
