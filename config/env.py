import os
from dataclasses import dataclass
from enum import StrEnum

from dotenv import load_dotenv


class EnvType(StrEnum):
    UNIT_TEST = "UNIT_TEST"
    E2E_TEST = "E2E_TEST"
    APP = "APP"


@dataclass
class LNBitsEnvironment:
    api_url: str
    admin_key: str
    invoice_key: str


@dataclass(frozen=True)
class AppEnvironment:
    env_type: EnvType
    postgres_connection_url: str
    jwt_secret_key: str


load_dotenv()

env_type_var: str | None = os.getenv("ENV_TYPE")
assert env_type_var, "ENV_TYPE environment variable must be set"

environment = AppEnvironment(
    env_type=EnvType(env_type_var),
    postgres_connection_url=os.getenv("POSTGRES_CONNECTION_URL") or "",
    jwt_secret_key=os.getenv("JWT_SECRET_KEY") or "",
)


lnbits_environment = LNBitsEnvironment(
    api_url=os.getenv("LNBITS_API_URL") or "",
    admin_key=os.getenv("LNBITS_ADMIN_KEY") or "",
    invoice_key=os.getenv("LNBITS_INVOICE_KEY") or "",
)
