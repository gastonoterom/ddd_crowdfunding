# TODO: Real hashing
class HashUtils:

    @staticmethod
    async def hash(plain_text: str) -> str:
        return plain_text

    @staticmethod
    async def verify(plain_text: str, hashed_text: str) -> bool:
        return plain_text == hashed_text
