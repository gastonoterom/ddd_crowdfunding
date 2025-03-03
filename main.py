from fastapi import FastAPI

from bounded_contexts.accounting.handlers import register_accounting_handlers
from bounded_contexts.auth.handlers import register_auth_handlers
from bounded_contexts.auth.repositories import (
    PostgresAccountRepository as PostgresAuthAccountRepository,
)
from bounded_contexts.accounting.repositories import (
    PostgresAccountRepository as PostgresAccountingAccountRepository,
)
from bounded_contexts.auth.rest import register_auth_routes
from bounded_contexts.bitcoin.repositories import PostgresInvoiceRepository
from bounded_contexts.bitcoin.rest import register_bitcoin_routes
from bounded_contexts.crowdfunding.handlers import register_crowdfunding_handlers
from bounded_contexts.crowdfunding.repositories import PostgresCampaignRepository
from bounded_contexts.crowdfunding.rest import register_crowdfunding_routes
from bounded_contexts.bitcoin.handlers import register_bitcoin_handlers
from infrastructure.event_bus import make_unit_of_work

# TODO: Error handling
app = FastAPI()


# TODO: Better coverage


# TODO: Reconsider this, and hide behind some kind of configuration (also, on_event is deprecated)
# Run DDL
@app.on_event("startup")
async def startup():
    async with make_unit_of_work() as uow:
        for ddl in [
            PostgresAuthAccountRepository.repository_ddl(),
            PostgresAccountingAccountRepository.repository_ddl(),
            PostgresCampaignRepository.repository_ddl(),
            PostgresInvoiceRepository.repository_ddl(),
        ]:
            await uow.conn.execute(ddl)


# Register command handlers
register_auth_handlers()
register_accounting_handlers()
register_crowdfunding_handlers()
register_bitcoin_handlers()

# Register API routes
register_auth_routes(app)
register_crowdfunding_routes(app)
register_bitcoin_routes(app)
