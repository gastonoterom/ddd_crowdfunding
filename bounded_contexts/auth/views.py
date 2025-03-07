from dataclasses import dataclass

from bounded_contexts.auth.adapters.repositories import account_repository
from bounded_contexts.auth.aggregates import Account
from infrastructure.events.uow_factory import make_unit_of_work
from infrastructure.tools import verify_hash, create_jwt_token


@dataclass(frozen=True)
class LoginTokenView:
    account_id: str
    token: str


@dataclass(frozen=True)
class AccountView:
    account_id: str
    username: str


@dataclass(frozen=True)
class SensitiveAccountView:
    account_id: str
    username: str
    password_hash: str
