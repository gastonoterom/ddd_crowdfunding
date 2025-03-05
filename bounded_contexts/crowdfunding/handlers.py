from bounded_contexts.crowdfunding.adapters.repositories import (
    campaign_repository,
)
from bounded_contexts.crowdfunding.aggregates import Campaign, Donation
from bounded_contexts.crowdfunding.messages import (
    CreateCampaign,
    DonateToCampaign,
    DonationCreatedEvent,
)
from infrastructure.event_bus import UnitOfWork, event_bus


async def create_campaign_handler(uow: UnitOfWork, command: CreateCampaign) -> None:
    campaign = Campaign(
        entity_id=command.entity_id,
        account_id=command.account_id,
        title=command.title,
        description=command.description,
        goal=command.goal,
    )

    await campaign_repository(uow).add(campaign)


async def donate_to_campaign_handler(
    uow: UnitOfWork,
    command: DonateToCampaign,
) -> None:
    campaign: Campaign | None = await campaign_repository(uow).find_by_id(
        command.campaign_id
    )

    if campaign is None:
        raise ValueError("Campaign not found")

    campaign.donate(
        Donation(
            idempotency_key=command.idempotency_key,
            amount=command.amount,
            account_id=command.account_id,
        )
    )

    uow.emit(
        DonationCreatedEvent(
            idempotency_key=command.idempotency_key,
            donor_account_id=command.account_id,
            recipient_account_id=campaign.account_id,
            amount=command.amount,
        )
    )


def register_crowdfunding_handlers():
    event_bus.register_command_handler(CreateCampaign, create_campaign_handler)
    event_bus.register_command_handler(DonateToCampaign, donate_to_campaign_handler)
