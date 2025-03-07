import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppEnvironment:
    postgres_connection_url: str
    jwt_secret_key: str


load_dotenv()

environment = AppEnvironment(
    postgres_connection_url=os.getenv("POSTGRES_CONNECTION_URL"),
    jwt_secret_key=os.getenv("JWT_SECRET_KEY"),
)
