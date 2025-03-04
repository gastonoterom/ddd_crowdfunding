import jwt


SECRET_KEY = "unsafe_key"  # TODO: env variables


class JWTUtils:
    @staticmethod
    async def create_token(payload: dict) -> str:
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    @staticmethod
    async def decode_token(token: str) -> dict:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
