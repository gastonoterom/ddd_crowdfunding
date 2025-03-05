from abc import ABC

from bounded_contexts.common.repositories import Repository
from bounded_contexts.crowdfunding.aggregates import Campaign


class CampaignRepository(Repository[Campaign], ABC):
    pass
