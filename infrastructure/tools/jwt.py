import jwt


SECRET_KEY = "unsafe_key"  # TODO: env variables


async def create_jwt_token(payload: dict) -> str:
    # TODO: Run in executor
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


async def decode_jwt_token(token: str) -> dict:
    # TODO: Run in executor
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
