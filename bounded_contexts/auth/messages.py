from infrastructure.events.messages import Command, Event


class RegisterAccount(Command):
    account_id: str
    username: str
    hashed_password: str
    message_type: str = "register-account"


class SignupEvent(Event):
    account_id: str
