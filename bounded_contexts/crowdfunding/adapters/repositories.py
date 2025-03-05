import json

from bounded_contexts.common.adapters.repository_adapters import MockRepository
from bounded_contexts.crowdfunding.aggregates import Campaign, Donation
from bounded_contexts.crowdfunding.ports.repositories import CampaignRepository
from infrastructure.event_bus import PostgresUnitOfWork, UnitOfWork, MockUnitOfWork


class PostgresCampaignRepository(CampaignRepository):

    def __init__(self, uow: PostgresUnitOfWork) -> None:
        super().__init__(uow)
        self.uow = uow

    async def _find_by_id(self, entity_id: str) -> Campaign | None:
        row = await self.uow.conn.fetchrow(
            """
            SELECT * FROM campaigns WHERE entity_id = $1
            """,
            entity_id,
        )

        if not row:
            return None

        donations = [Donation(**donation) for donation in json.loads(row["donations"])]

        return Campaign(
            entity_id=row["entity_id"],
            account_id=row["account_id"],
            title=row["title"],
            description=row["description"],
            goal=row["goal"],
            total_raised=row["total_raised"],
            donations=donations,
        )

    async def _add(self, campaign: Campaign) -> None:
        donations = json.dumps([donation.__dict__ for donation in campaign._donations])

        await self.uow.conn.execute(
            """
            INSERT INTO campaigns (
                entity_id, account_id, title, description, goal, total_raised, donations
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)

            """,
            campaign.entity_id,
            campaign.account_id,
            campaign.title,
            campaign.description,
            campaign.goal,
            campaign.total_raised,
            donations,
        )

    async def _update(self, campaign: Campaign) -> None:
        donations = json.dumps([donation.__dict__ for donation in campaign._donations])

        await self.uow.conn.execute(
            """
            UPDATE campaigns
            SET account_id = $2, goal = $3, total_raised = $4, donations = $5, title = $6, description = $7
            WHERE entity_id = $1
            """,
            campaign.entity_id,
            campaign.account_id,
            campaign.goal,
            campaign.total_raised,
            donations,
            campaign.title,
            campaign.description,
        )


class MockCampaignRepository(CampaignRepository, MockRepository[Campaign]):
    pass


def campaign_repository(uow: UnitOfWork) -> CampaignRepository:
    if isinstance(uow, PostgresUnitOfWork):
        return PostgresCampaignRepository(uow)

    elif isinstance(uow, MockUnitOfWork):
        return MockCampaignRepository(uow)

    raise Exception("Unsupported UnitOfWork type.")
