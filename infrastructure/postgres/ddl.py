from bounded_contexts.accounting.adapters.aggregate_ddl import ACCOUNTING_AGGREGATE_DDL
from bounded_contexts.auth.adapters.aggregate_ddl import AUTH_ACCOUNT_DDL
from bounded_contexts.bitcoin.adapters.aggregate_ddl import BTC_INVOICES_AGGREGATE_DDL
from bounded_contexts.common.adapters.outbox_ddl import OUTBOX_DDL
from bounded_contexts.crowdfunding.adapters.aggregate_ddl import CAMPAIGN_AGGREGATE_DDL
from infrastructure.postgres.pool import postgres_pool


DDL_LIST = [
    OUTBOX_DDL,
    CAMPAIGN_AGGREGATE_DDL,
    BTC_INVOICES_AGGREGATE_DDL,
    ACCOUNTING_AGGREGATE_DDL,
    AUTH_ACCOUNT_DDL,
]


async def execute_ddl() -> None:
    async with postgres_pool.get_pool().acquire() as conn:
        for ddl in DDL_LIST:
            await conn.execute(ddl)
