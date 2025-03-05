from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from starlette import status

from infrastructure.tools import decode_jwt_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_account_id(token: Annotated[str, Depends(oauth2_scheme)]) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = await decode_jwt_token(token)

        account_id = payload.get("account_id")

        if account_id is None:
            raise credentials_exception

    except InvalidTokenError:
        raise credentials_exception

    return account_id
