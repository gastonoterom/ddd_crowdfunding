from dataclasses import dataclass


@dataclass(frozen=True)
class Deposit:
    idempotency_key: str
    amount: int


@dataclass(frozen=True)
class Withdrawal:
    idempotency_key: str
    amount: int


class Account:
    def __init__(
        self,
        account_id: str,
        deposits: list[Deposit] | None = None,
        withdrawals: list[Withdrawal] | None = None,
        version: int = 1,
    ) -> None:
        self._account_id = account_id

        self._version = version

        self._deposits = deposits if deposits else []
        self._withdrawals = withdrawals if withdrawals else []

    @property
    def account_id(self) -> str:
        return self._account_id

    @property
    def version(self) -> int:
        return self._version

    def deposit(self, deposit: Deposit) -> None:
        # Ignore duplicate deposits
        for previous_deposit in self._deposits:
            if previous_deposit.idempotency_key == deposit.idempotency_key:
                return

        self._deposits.append(deposit)
        self._version += 1

    def withdraw(self, withdrawal: Withdrawal) -> None:
        # Ignore duplicate withdrawals
        for previous_withdrawal in self._withdrawals:
            if previous_withdrawal.idempotency_key == withdrawal.idempotency_key:
                return

        if withdrawal.amount > self.available_funds:
            raise ValueError(f"Insufficient funds to withdraw '{withdrawal.amount}'")

        self._withdrawals.append(withdrawal)
        self._version += 1

    @property
    def available_funds(self) -> int:
        if len(self._deposits) == 0:
            return 0

        deposits_total = sum([deposit.amount for deposit in self._deposits])

        withdrawals_total = sum([withdrawal.amount for withdrawal in self._withdrawals])

        assert deposits_total >= withdrawals_total, "Inconsistency error"

        return deposits_total - withdrawals_total


def account_transfer(
    idempotency_key: str,
    from_account: Account,
    to_account: Account,
    amount: int,
) -> None:
    from_account.withdraw(Withdrawal(idempotency_key, amount))
    to_account.deposit(Deposit(idempotency_key, amount))


def external_deposit(
    idempotency_key: str,
    wallet: Account,
    amount: int,
) -> None:
    wallet.deposit(Deposit(idempotency_key, amount))


def external_withdraw(
    idempotency_key: str,
    wallet: Account,
    amount: int,
) -> None:
    wallet.withdraw(Withdrawal(idempotency_key, amount))
