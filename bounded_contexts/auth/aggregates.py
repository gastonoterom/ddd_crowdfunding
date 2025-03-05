from bounded_contexts.common.aggregates import Aggregate


class Account(Aggregate):
    def __init__(self, account_id: str, username: str, password: str) -> None:
        super().__init__(account_id)
        self.username = username
        self.password = password

    @property
    def account_id(self) -> str:
        return self.entity_id
