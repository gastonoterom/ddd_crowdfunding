from bounded_contexts.crowdfunding.ports.view_factories import CampaignViewFactory
from bounded_contexts.crowdfunding.views import CampaignView
from infrastructure.postgres import postgres_pool


class PostgresCampaignViewFactory(CampaignViewFactory):
    @staticmethod
    def __row_to_view(row: dict) -> CampaignView:
        return CampaignView(
            entity_id=row["entity_id"],
            title=row["title"],
            description=row["description"],
            goal=row["goal"],
            total_raised=row["total_raised"],
            creator_account_id=row["creator_account_id"],
            creator_username=row["creator_username"],
        )

    async def create_view(self, campaign_id: str) -> CampaignView:
        async with postgres_pool.get_pool().acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    c.entity_id, 
                    c.title, 
                    c.description, 
                    c.goal, 
                    c.total_raised, 
                    a.entity_id as creator_account_id, 
                    c.username as creator_username  
                FROM campaigns c
                JOIN auth_accounts a ON c.account_id = a.entity_id
                WHERE entity_id = $1
                """,
                campaign_id,
            )

        assert row is not None, f"campaign with id {campaign_id} not found"

        return self.__row_to_view(row)

    async def list(self) -> list[CampaignView]:
        async with postgres_pool.get_pool().acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    c.entity_id, 
                    c.title, 
                    c.description, 
                    c.goal, 
                    c.total_raised, 
                    a.entity_id as creator_account_id, 
                    c.username as creator_username  
                FROM campaigns c
                JOIN auth_accounts a ON c.account_id = a.entity_id
                """,
            )

        return [self.__row_to_view(row) for row in rows]


def campaign_view_factory() -> CampaignViewFactory:
    return PostgresCampaignViewFactory()
