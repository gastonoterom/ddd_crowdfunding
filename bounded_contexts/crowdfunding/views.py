from dataclasses import dataclass


@dataclass(frozen=True)
class CampaignView:
    entity_id: str
    title: str
    description: str
    goal: int
    total_raised: int
    creator_account_id: str
    creator_username: str
