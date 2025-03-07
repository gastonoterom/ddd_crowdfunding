from dataclasses import dataclass

from infrastructure.events.messages import Event, Command


@dataclass(frozen=True)
class DepositCommand(Command):
    account_id: str
    idempotency_key: str
    amount: int
    metadata: dict


@dataclass(frozen=True)
class RequestWithdrawCommand(Command):
    account_id: str
    idempotency_key: str
    amount: int
    metadata: dict


@dataclass(frozen=True)
class RequestTransferCommand(Command):
    idempotency_key: str
    from_account_id: str
    to_account_id: str
    amount: int
    metadata: dict


@dataclass(frozen=True)
class TransferSucceededEvent(Event):
    idempotency_key: str
    from_account_id: str
    to_account_id: str
    amount: int
    metadata: dict


@dataclass(frozen=True)
class WithdrawSucceededEvent(Event):
    account_id: str
    idempotency_key: str
    amount: int
    metadata: dict


@dataclass(frozen=True)
class WithdrawRejectedEvent(Event):
    account_id: str
    idempotency_key: str
    amount: int
    metadata: dict
