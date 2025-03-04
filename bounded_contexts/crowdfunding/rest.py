from typing import Annotated
from uuid import uuid4

from fastapi import FastAPI, Depends
from pydantic import BaseModel

from bounded_contexts.crowdfunding.commands import CreateCampaign, DonateToCampaign
from infrastructure.event_bus import event_bus
from utils.fastapi import get_account_id


def register_crowdfunding_routes(app: FastAPI) -> None:
    class CreateCampaignRequest(BaseModel):
        goal: int

    class CreateCampaignResponse(BaseModel):
        campaign_id: str

    @app.post("/crowdfunding/campaign")
    async def post_campaign(
        body: CreateCampaignRequest,
        account_id: Annotated[str, Depends(get_account_id)],
    ) -> CreateCampaignResponse:
        campaign_id = uuid4().hex

        command = CreateCampaign(
            campaign_id=campaign_id,
            account_id=account_id,
            goal=body.goal,
        )

        await event_bus.handle(command)

        return CreateCampaignResponse(campaign_id=campaign_id)

    class DonateToCampaignRequest(BaseModel):
        idempotency_key: str
        campaign_id: str
        amount: int

    # TODO: Response view model
    @app.post("/crowdfunding/donate")
    async def post_donate(
        body: DonateToCampaignRequest,
        account_id: Annotated[str, Depends(get_account_id)],
    ) -> None:
        command = DonateToCampaign(
            campaign_id=body.campaign_id,
            account_id=account_id,
            amount=body.amount,
            idempotency_key=body.idempotency_key,
        )

        await event_bus.handle(command)
