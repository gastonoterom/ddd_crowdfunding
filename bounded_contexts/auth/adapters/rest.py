from typing import Annotated
from uuid import uuid4

from fastapi import Depends, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from bounded_contexts.auth.messages import RegisterAccount
from bounded_contexts.auth.views import create_login_token_view
from infrastructure.event_bus import event_bus
from infrastructure.tools import hash_text


auth_router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    password: str


class RegisterResponse(BaseModel):
    account_id: str


@auth_router.post("/auth/register")
async def register(body: RegisterRequest) -> RegisterResponse:
    account_id = uuid4().hex

    hashed_password = await hash_text(body.password)

    command = RegisterAccount(
        account_id=account_id,
        username=body.username,
        hashed_password=hashed_password,
    )

    await event_bus.handle(command)

    return RegisterResponse(account_id=account_id)


# Fast API specific implementation
class Token(BaseModel):
    access_token: str
    token_type: str


@auth_router.post("/token")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    token_view = await create_login_token_view(
        username=form_data.username,
        password=form_data.password,
    )

    return Token(access_token=token_view.token, token_type="bearer")
