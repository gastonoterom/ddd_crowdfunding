from dataclasses import dataclass


@dataclass(frozen=True)
class DashboardView:
    account_id: str
    balance: int
    campaigns_amount: int
