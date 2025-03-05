import bcrypt


async def hash_text(plain_text: str) -> str:
    # TODO: run in executor so as to not block the event loop
    return bcrypt.hashpw(plain_text.encode(), bcrypt.gensalt()).decode()


async def verify_hash(plain_text: str, hashed_text: str) -> bool:
    # TODO: run in executor so as to not block the event loop
    return bcrypt.checkpw(plain_text.encode(), hashed_text.encode())
