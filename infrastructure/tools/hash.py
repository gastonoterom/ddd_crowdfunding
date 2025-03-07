import bcrypt

from infrastructure.tools.background_utils import background_service


async def hash_text(plain_text: str) -> str:
    return await background_service.run_async(
        lambda: bcrypt.hashpw(plain_text.encode(), bcrypt.gensalt()).decode()
    )


async def verify_hash(plain_text: str, hashed_text: str) -> bool:
    return await background_service.run_async(
        lambda: bcrypt.checkpw(plain_text.encode(), hashed_text.encode())
    )
