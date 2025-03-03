from bounded_contexts.crowdfunding.aggregates import Campaign, Donation

campaign_id = "campaign_id"
account_id = "account_id"
donor_id = "donor_id"
goal = 1000


def test_create_campaign() -> None:
    campaign = Campaign(campaign_id=campaign_id, account_id=account_id, goal=goal)

    # Assert properties
    assert campaign.campaign_id == campaign_id
    assert campaign.account_id == account_id
    assert campaign.goal == goal
    assert campaign.total_raised == 0
    assert not campaign.goal_reached()


def test_donate_to_campaign() -> None:
    campaign = Campaign(campaign_id=campaign_id, account_id=account_id, goal=goal)
    donation = Donation(idempotency_key="key1", amount=100, account_id=donor_id)

    campaign.donate(donation)

    assert campaign.total_raised == 100
    assert not campaign.goal_reached()


def test_donate_to_own_campaign() -> None:
    campaign = Campaign(campaign_id=campaign_id, account_id=account_id, goal=goal)
    donation = Donation(idempotency_key="key1", amount=100, account_id=account_id)

    try:
        campaign.donate(donation)
        assert False, "Should have raised an exception"
    except ValueError as e:
        assert str(e) == "Can't donate to your own campaign"


def test_donate_duplicate_idempotency_key() -> None:
    campaign = Campaign(campaign_id=campaign_id, account_id=account_id, goal=goal)
    donation = Donation(idempotency_key="key1", amount=100, account_id=donor_id)

    campaign.donate(donation)
    campaign.donate(donation)

    assert campaign.total_raised == 100


def test_goal_reached() -> None:
    campaign = Campaign(campaign_id=campaign_id, account_id=account_id, goal=goal)
    donation = Donation(idempotency_key="key1", amount=1000, account_id=donor_id)

    campaign.donate(donation)

    assert campaign.total_raised == 1000
    assert campaign.goal_reached()


def test_donate_after_goal_reached() -> None:
    campaign = Campaign(campaign_id=campaign_id, account_id=account_id, goal=goal)
    donation1 = Donation(idempotency_key="key1", amount=1000, account_id=donor_id)
    donation2 = Donation(idempotency_key="key2", amount=100, account_id=donor_id)

    campaign.donate(donation1)

    try:
        campaign.donate(donation2)
        assert False, "Should have raised an exception"
    except ValueError as e:
        assert str(e) == "Campaign goal already reached"
