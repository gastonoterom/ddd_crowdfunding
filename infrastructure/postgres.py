from asyncpg import Pool, create_pool


class PostgresPool:
    def __init__(
        self,
        connection_url: str,
    ) -> None:
        self.connection_url: str = connection_url
        self.pool: Pool | None = None

    async def start_pool(self) -> Pool:
        self.pool = await create_pool(dsn=self.connection_url)

        return self.pool


# TODO: this is hardcoded
postgres_pool = PostgresPool("postgresql://postgres:postgres@localhost:5432/postgres")
