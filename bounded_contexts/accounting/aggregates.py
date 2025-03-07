from dataclasses import dataclass

from bounded_contexts.common.aggregates import Aggregate


@dataclass(frozen=True)
class Transaction:
    idempotency_key: str
    amount: int
    metadata: dict


class Account(Aggregate):
    def __init__(
        self,
        account_id: str,
        balance: int = 0,
        transactions: list[Transaction] | None = None,
    ) -> None:
        super().__init__(entity_id=account_id)

        self._balance = balance

        self._transactions = transactions if transactions else []

    @property
    def account_id(self) -> str:
        return self.entity_id

    @property
    def balance(self) -> int:
        return self._balance

    def deposit(self, idempotency_key: str, amount: int, metadata: dict) -> None:
        # Ignore duplicate deposits
        for previous_deposit in self._transactions:
            if previous_deposit.idempotency_key == idempotency_key:
                return

        self._transactions.append(Transaction(idempotency_key, amount, metadata))
        self._balance += amount

    def withdraw(self, idempotency_key: str, amount: int, metadata: dict) -> None:
        # Ignore duplicate withdrawals
        for previous_withdrawal in self._transactions:
            if previous_withdrawal.idempotency_key == idempotency_key:
                return

        if amount > self.balance:
            raise ValueError(f"Insufficient funds to withdraw '{amount}'")

        self._transactions.append(Transaction(idempotency_key, -amount, metadata))
        self._balance -= amount


def account_transfer(
    idempotency_key: str,
    from_account: Account,
    to_account: Account,
    amount: int,
    metadata: dict,
) -> None:
    assert from_account != to_account

    from_account.withdraw(idempotency_key, amount, metadata)
    to_account.deposit(idempotency_key, amount, metadata)
