from bounded_contexts.crowdfunding.aggregates import Campaign, Donation
from bounded_contexts.crowdfunding.commands import CreateCampaign, DonateToCampaign
from bounded_contexts.crowdfunding.events import DonationCreatedEvent
from bounded_contexts.crowdfunding.repositories import campaign_repository
from infrastructure.event_bus import UnitOfWork, event_bus


async def create_campaign_handler(uow: UnitOfWork, command: CreateCampaign) -> None:
    campaign = Campaign(
        campaign_id=command.campaign_id,
        account_id=command.account_id,
        goal=command.goal,
    )

    await campaign_repository(uow).add(campaign)


async def donate_to_campaign_handler(
    uow: UnitOfWork,
    command: DonateToCampaign,
) -> None:
    campaign: Campaign | None = await campaign_repository(uow).find_by_campaign_id(
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

    await campaign_repository(uow).update(campaign)

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
