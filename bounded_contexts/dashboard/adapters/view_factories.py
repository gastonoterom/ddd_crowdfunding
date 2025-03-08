from bounded_contexts.dashboard.ports.view_factories import DashboardViewFactory
from bounded_contexts.dashboard.views import DashboardView
from infrastructure.postgres import postgres_pool


class PostgresDashboardViewFactory(DashboardViewFactory):

    async def create_dashboard_view(self, account_id: str) -> DashboardView:
        async with postgres_pool.get_pool().acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    a.account_id,
                    aa.balance,
                    COUNT(c.entity_id) as campaigns_amount
                FROM auth_accounts a
                JOIN accounting_accounts aa ON a.account_id = aa.account_id
                LEFT JOIN campaigns c on a.account_id = c.entity_id 
                WHERE a.account_id = $1
                GROUP BY a.account_id, aa.balance
                """,
                account_id,
            )

        assert row

        return DashboardView(
            account_id=row["account_id"],
            balance=int(row["balance"]),
            campaigns_amount=int(row["campaigns_amount"]),
        )


def dashboard_view_factory() -> DashboardViewFactory:
    return PostgresDashboardViewFactory()
