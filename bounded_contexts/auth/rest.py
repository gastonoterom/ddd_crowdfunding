from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel

from bounded_contexts.auth.commands import RegisterAccount
from bounded_contexts.auth.views import create_login_token_view
from infrastructure.event_bus import event_bus


def register_auth_routes(app: FastAPI) -> None:
    class RegisterRequest(BaseModel):
        username: str
        password: str

    class RegisterResponse(BaseModel):
        account_id: str

    @app.post("/auth/register")
    async def register(body: RegisterRequest) -> RegisterResponse:
        account_id = uuid4().hex

        command = RegisterAccount(
            account_id=account_id,
            username=body.username,
            password=body.password,
        )

        await event_bus.handle(command)

        return RegisterResponse(account_id=account_id)

    class LoginRequest(BaseModel):
        username: str
        password: str

    class LoginResponse(BaseModel):
        token: str

    @app.post("/auth/login")
    async def login(body: LoginRequest) -> LoginResponse:

        token_view = await create_login_token_view(
            username=body.username,
            password=body.password,
        )

        return LoginResponse(token=token_view.token)
