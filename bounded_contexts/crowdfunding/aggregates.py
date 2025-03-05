from dataclasses import dataclass

from bounded_contexts.common.aggregates import Aggregate


@dataclass(frozen=True)
class Donation:
    idempotency_key: str
    amount: int
    account_id: str


class Campaign(Aggregate):
    def __init__(
        self,
        entity_id: str,
        account_id: str,
        title: str,
        description: str,
        goal: int,
        total_raised: int = 0,
        donations: list[Donation] | None = None,
    ) -> None:
        super().__init__(entity_id)
        self._account_id = account_id
        self._title = title
        self._description = description
        self._goal = goal
        self._donations: list[Donation] = donations if donations else []
        self._total_raised = total_raised

    @property
    def account_id(self) -> str:
        return self._account_id

    @property
    def title(self) -> str:
        return self._title

    @property
    def description(self) -> str:
        return self._description

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

    def goal_reached(self) -> bool:
        return self.total_raised >= self.goal
