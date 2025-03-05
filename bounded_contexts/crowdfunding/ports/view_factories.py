from abc import ABC, abstractmethod

from bounded_contexts.crowdfunding.views import CampaignView


class CampaignViewFactory(ABC):

    @abstractmethod
    async def create_view(self, campaign_id: str) -> CampaignView:
        pass

    @abstractmethod
    async def list(self) -> list[CampaignView]:
        pass
