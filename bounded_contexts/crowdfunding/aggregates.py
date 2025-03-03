from dataclasses import dataclass


@dataclass(frozen=True)
class Donation:
    idempotency_key: str
    amount: int
    account_id: str


class Campaign:
    def __init__(
        self,
        # TODO: Campaign description, campaign name, campaign picture
        campaign_id: str,
        account_id: str,
        goal: int,
        total_raised: int = 0,
        donations: list[Donation] | None = None,
        version: int = 1,
    ) -> None:
        self._campaign_id = campaign_id
        self._account_id = account_id
        self._goal = goal
        self._donations: list[Donation] = donations if donations else []
        self._total_raised = total_raised
        self._version = version

    @property
    def campaign_id(self) -> str:
        return self._campaign_id

    @property
    def account_id(self) -> str:
        return self._account_id

    @property
    def goal(self) -> int:
        return self._goal

    @property
    def total_raised(self) -> int:
        return self._total_raised

    def donate(self, donation: Donation) -> None:
        # We enforce consistency constraints in aggregate roots
        # If this doesn't scale in the future, we can use lazy loading
        for previous_donation in self._donations:
            if previous_donation.idempotency_key == donation.idempotency_key:
                return

        # Arbitrary rules, can be changed or replaced via inheritance
        if donation.account_id == self.account_id:
            raise ValueError("Can't donate to your own campaign")

        if self.goal_reached():
            raise ValueError("Campaign goal already reached")

        self._donations.append(donation)
        self._total_raised += donation.amount
        self._version += 1

    def goal_reached(self) -> bool:
        return self.total_raised >= self.goal
