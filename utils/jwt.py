# TODO: Real JWT
class JWTUtils:
    @staticmethod
    async def create_token(payload: dict) -> str:
        return payload["account_id"]
