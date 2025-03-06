import pytest

from bounded_contexts.crowdfunding.adapters.repositories import (
    campaign_repository,
)
from bounded_contexts.crowdfunding.aggregates import Campaign
from bounded_contexts.crowdfunding.handlers import (
    create_campaign_handler,
    donate_to_campaign_handler,
)
from bounded_contexts.crowdfunding.messages import (
    DonateToCampaign,
    DonationCreatedEvent,
    CreateCampaign,
)
from infrastructure.events.uow_factory import make_unit_of_work

entity_id = "entity_id"
account_id = "account_id"
title = "Test Title"
description = "Test Description"

goal = 1000


@pytest.mark.asyncio
async def test_create_campaign_handler() -> None:
    command = CreateCampaign(
        entity_id=entity_id,
        title=title,
        description=description,
        goal=goal,
        account_id=account_id,
    )

    async with make_unit_of_work() as uow:
        await create_campaign_handler(uow, command)

        campaign = await campaign_repository(uow).find_by_id(entity_id)

        assert campaign

        assert campaign.entity_id == entity_id
        assert campaign.account_id == account_id
        assert campaign.title == title
        assert campaign.description == description
        assert campaign.goal == goal
        assert campaign.total_raised == 0


@pytest.mark.asyncio
async def test_donate_to_campaign_handler() -> None:
    # Create a campaign (total raise should be 0)
    async with make_unit_of_work() as uow:
        campaign: Campaign | None = Campaign(
            entity_id=entity_id,
            account_id=account_id,
            title=title,
            description=description,
            goal=goal,
        )

        assert campaign

        await campaign_repository(uow).add(campaign)

        assert campaign.total_raised == 0

    # Donate to the campaign, total raised should be 100
    command = DonateToCampaign(
        campaign_id=entity_id,
        idempotency_key="idempotency_key",
        account_id="account_2_id",
        amount=100,
    )

    async with make_unit_of_work() as uow:
        await donate_to_campaign_handler(uow, command)

        campaign = await campaign_repository(uow).find_by_id(entity_id)

        assert campaign

        assert campaign.total_raised == 100

        messages = uow.collect_messages()
        assert len(messages) == 1

        # This command should raise a DonationCreatedEvent
        assert messages[0] == DonationCreatedEvent(
            idempotency_key="idempotency_key",
            donor_account_id="account_2_id",
            recipient_account_id=account_id,
            amount=100,
        )
