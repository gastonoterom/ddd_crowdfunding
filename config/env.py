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

environment = AppEnvironment(
    env_type=EnvType(os.getenv("ENV_TYPE")),
    postgres_connection_url=os.getenv("POSTGRES_CONNECTION_URL"),
    jwt_secret_key=os.getenv("JWT_SECRET_KEY"),
)


lnbits_environment = LNBitsEnvironment(
    api_url=os.getenv("LNBITS_API_URL"),
    admin_key=os.getenv("LNBITS_ADMIN_KEY"),
    invoice_key=os.getenv("LNBITS_INVOICE_KEY"),
)
