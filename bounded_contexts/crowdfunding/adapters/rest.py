from typing import Annotated
from uuid import uuid4

from fastapi import Depends, APIRouter
from pydantic import BaseModel

from bounded_contexts.crowdfunding.adapters.view_factories import campaign_view_factory
from bounded_contexts.crowdfunding.messages import CreateCampaign, DonateToCampaign
from bounded_contexts.crowdfunding.views import CampaignView
from infrastructure.event_bus import event_bus
from infrastructure.fastapi import get_account_id


crowdfunding_router = APIRouter()


class CreateCampaignRequest(BaseModel):
    goal: int
    title: str
    description: str


@crowdfunding_router.post("/crowdfunding/campaign")
async def post_campaign(
    body: CreateCampaignRequest,
    account_id: Annotated[str, Depends(get_account_id)],
) -> CampaignView:
    entity_id = uuid4().hex

    command = CreateCampaign(
        entity_id=entity_id,
        account_id=account_id,
        title=body.title,
        description=body.description,
        goal=body.goal,
    )

    await event_bus.handle(command)

    return await campaign_view_factory().create_view(entity_id)


class DonateToCampaignRequest(BaseModel):
    idempotency_key: str
    campaign_id: str
    amount: int


@crowdfunding_router.post("/crowdfunding/donate")
async def post_donate(
    body: DonateToCampaignRequest,
    account_id: Annotated[str, Depends(get_account_id)],
) -> CampaignView:
    command = DonateToCampaign(
        campaign_id=body.campaign_id,
        account_id=account_id,
        amount=body.amount,
        idempotency_key=body.idempotency_key,
    )

    await event_bus.handle(command)

    return await campaign_view_factory().create_view(command.campaign_id)


@crowdfunding_router.get("/crowdfunding/campaign")
async def get_campaign(campaign_id: str) -> CampaignView:
    return await campaign_view_factory().create_view(campaign_id)


@crowdfunding_router.get("/crowdfunding/campaigns")
async def get_campaigns() -> list[CampaignView]:
    return await campaign_view_factory().list()
