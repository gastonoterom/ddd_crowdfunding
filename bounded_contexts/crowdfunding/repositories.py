import json
from abc import ABC, abstractmethod

from bounded_contexts.crowdfunding.aggregates import Campaign, Donation
from infrastructure.event_bus import UnitOfWork, PostgresUnitOfWork


# Abstract repository
class CampaignRepository(ABC):
    # TODO: Do this for other domains too (save to add/update)
    @abstractmethod
    async def add(self, campaign: Campaign) -> None:
        pass

    @abstractmethod
    async def update(self, campaign: Campaign) -> None:
        pass

    @abstractmethod
    async def find_by_campaign_id(self, campaign_id: str) -> Campaign | None:
        pass


# Postgres implementation
class PostgresCampaignRepository(CampaignRepository):

    def __init__(self, uow: PostgresUnitOfWork) -> None:
        self.uow = uow

    @staticmethod
    def repository_ddl() -> str:
        return """
        CREATE TABLE IF NOT EXISTS campaigns (
            campaign_id VARCHAR PRIMARY KEY,
            account_id VARCHAR,
            goal INT,
            total_raised INT,
            -- TODO: Could also be a different table
            donations JSONB,
            -- TODO: Reconsider version field
            version INT
        );
        """

    async def find_by_campaign_id(self, campaign_id: str) -> Campaign | None:
        row = await self.uow.conn.fetchrow(
            """
            SELECT * FROM campaigns WHERE campaign_id = $1
            """,
            campaign_id,
        )

        if not row:
            return None

        donations = [Donation(**donation) for donation in json.loads(row["donations"])]

        return Campaign(
            campaign_id=row["campaign_id"],
            account_id=row["account_id"],
            goal=row["goal"],
            total_raised=row["total_raised"],
            donations=donations,
            version=row["version"],
        )

    async def add(self, campaign: Campaign) -> None:
        donations = json.dumps([donation.__dict__ for donation in campaign._donations])

        await self.uow.conn.execute(
            """
            INSERT INTO campaigns (
                campaign_id, account_id, goal, total_raised, donations, version
            ) VALUES ($1, $2, $3, $4, $5, $6)
            
            """,
            campaign.campaign_id,
            campaign.account_id,
            campaign.goal,
            campaign.total_raised,
            donations,
            campaign._version,
        )

    async def update(self, campaign: Campaign) -> None:
        donations = json.dumps([donation.__dict__ for donation in campaign._donations])

        await self.uow.conn.execute(
            """
            UPDATE campaigns
            SET account_id = $2, goal = $3, total_raised = $4, donations = $5, version = $6
            WHERE campaign_id = $1
            """,
            campaign.campaign_id,
            campaign.account_id,
            campaign.goal,
            campaign.total_raised,
            donations,
            campaign._version,
        )


def campaign_repository(uow: UnitOfWork) -> CampaignRepository:
    if isinstance(uow, PostgresUnitOfWork):
        return PostgresCampaignRepository(uow)

    raise Exception("Unsupported UnitOfWork type.")
