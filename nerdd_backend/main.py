import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .actions import SaveJobToDb, SaveModuleToDb, UpdateJobSize
from .lifespan import ActionLifespan, CreateModuleLifespan, InitializeAppLifespan
from .routers import (
    jobs_router,
    modules_router,
    results_router,
    sources_router,
    websockets_router,
)

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


lifespans = [
    InitializeAppLifespan(),
    ActionLifespan(lambda app: SaveJobToDb(app.state.channel, app.state.repository)),
    ActionLifespan(lambda app: UpdateJobSize(app.state.channel, app.state.repository)),
    ActionLifespan(lambda app: SaveModuleToDb(app.state.channel, app.state.repository)),
    CreateModuleLifespan(),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting tasks")
    start_tasks = asyncio.gather(
        *[asyncio.create_task(lifespan.start(app)) for lifespan in lifespans]
    )

    await start_tasks

    logger.info("Running tasks")
    run_tasks = asyncio.gather(
        *[asyncio.create_task(lifespan.run()) for lifespan in lifespans]
    )

    yield

    logger.info("Attempting to cancel all tasks")
    run_tasks.cancel()

    try:
        await run_tasks
    except asyncio.CancelledError:
        logger.info("Tasks successfully cancelled")


app = FastAPI(lifespan=lifespan)


origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router)
app.include_router(sources_router)
app.include_router(results_router)
app.include_router(modules_router)
app.include_router(websockets_router)