from contextlib import asynccontextmanager

from fastapi import FastAPI

from bounded_contexts.accounting.handlers import register_accounting_handlers
from bounded_contexts.auth.adapters.rest import auth_router
from bounded_contexts.auth.handlers import register_auth_handlers
from bounded_contexts.bitcoin.adapters.rest import bitcoin_router
from bounded_contexts.common.adapters.outbox_adapters import process_outbox
from bounded_contexts.crowdfunding.adapters.rest import crowdfunding_router
from bounded_contexts.crowdfunding.handlers import register_crowdfunding_handlers
from bounded_contexts.bitcoin.handlers import register_bitcoin_handlers
from infrastructure.postgres import postgres_pool, execute_ddl
from infrastructure.tools.background_utils import background_service


# Context manager for our fastapi application, we want to
# start the postgres connection pool and run the DDLs before the app
# and close the connection pool after it is shutdown


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await postgres_pool.start_pool()
    await execute_ddl()

    # Periodically process the transactional outbox
    background_service.run_fire_forget_coroutine(process_outbox())

    yield

    # Close the connection pool
    await postgres_pool.cleanup()


# Register message handlers
register_auth_handlers()
register_accounting_handlers()
register_crowdfunding_handlers()
register_bitcoin_handlers()

# Create FastApi application
app = FastAPI(lifespan=lifespan)


# Register fastapi routers
app.include_router(auth_router)
app.include_router(crowdfunding_router)
app.include_router(bitcoin_router)
