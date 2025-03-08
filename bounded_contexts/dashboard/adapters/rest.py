from typing import Annotated

from fastapi import APIRouter, Depends

from bounded_contexts.dashboard.queries import view_dashboard
from bounded_contexts.dashboard.views import DashboardView
from infrastructure.fastapi import get_account_id

dashboard_router = APIRouter()


@dashboard_router.get("/dashboard")
async def get_dashboard(
    account_id: Annotated[str, Depends(get_account_id)],
) -> DashboardView:
    return await view_dashboard(account_id)
