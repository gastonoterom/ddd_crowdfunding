import jwt

from config.env import environment
from infrastructure.tools.background_utils import background_service


async def create_jwt_token(payload: dict) -> str:
    return await background_service.run_async(
        lambda: jwt.encode(payload, environment.jwt_secret_key, algorithm="HS256")
    )


async def decode_jwt_token(token: str) -> dict:
    return await background_service.run_async(
        lambda: jwt.decode(token, environment.jwt_secret_key, algorithms=["HS256"])
    )
