from bounded_contexts.accounting.messages import (
    TransferSucceededEvent,
    RequestTransferCommand,
)
from bounded_contexts.crowdfunding.adapters.repositories import (
    campaign_repository,
)
from bounded_contexts.crowdfunding.aggregates import Campaign, Donation
from bounded_contexts.crowdfunding.messages import (
    CreateCampaign,
    DonateToCampaign,
)
from infrastructure.events.bus import event_bus
from infrastructure.events.unit_of_work import UnitOfWork
from infrastructure.events.uow_factory import make_unit_of_work


async def create_campaign_handler(command: CreateCampaign) -> None:
    campaign = Campaign(
        entity_id=command.entity_id,
        account_id=command.account_id,
        title=command.title,
        description=command.description,
        goal=command.goal,
    )

    async with make_unit_of_work() as uow:
        await campaign_repository(uow).add(campaign)


async def donate_to_campaign_handler(command: DonateToCampaign) -> None:
    async with make_unit_of_work() as uow:
        campaign = await campaign_repository(uow).find_by_id(command.campaign_id)

        assert campaign

        uow.emit(
            RequestTransferCommand(
                idempotency_key=command.idempotency_key,
                from_account_id=command.account_id,
                to_account_id=campaign.account_id,
                amount=command.amount,
                metadata={"campaign_id": campaign.entity_id},
            )
        )


async def register_campaign_donation(
    command: TransferSucceededEvent,
) -> None:
    async with make_unit_of_work() as uow:
        campaign_id: str | None = command.metadata.get("campaign_id", None)

        if campaign_id is None:
            return

        campaign: Campaign | None = await campaign_repository(uow).find_by_id(
            campaign_id
        )

        assert campaign

        campaign.donate(
            Donation(
                idempotency_key=command.idempotency_key,
                amount=command.amount,
                account_id=command.from_account_id,
            )
        )


def register_crowdfunding_handlers():
    event_bus.register_command_handler(CreateCampaign, create_campaign_handler)
    event_bus.register_command_handler(DonateToCampaign, donate_to_campaign_handler)

    event_bus.register_event_handler(
        TransferSucceededEvent,
        register_campaign_donation,
    )
