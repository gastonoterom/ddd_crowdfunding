from dataclasses import dataclass

from infrastructure.events.messages import Event, Command


@dataclass(frozen=True)
class DepositCommand(Command):
    account_id: str
    idempotency_key: str
    amount: int


@dataclass(frozen=True)
class RequestWithdrawCommand(Command):
    account_id: str
    idempotency_key: str
    amount: int


@dataclass(frozen=True)
class Transfer(Command):
    idempotency_key: str
    from_account_id: str
    to_account_id: str
    amount: int


@dataclass(frozen=True)
class TransactionSucceeded(Event):
    idempotency_key: str


@dataclass(frozen=True)
class TransactionRejected(Event):
    idempotency_key: str
