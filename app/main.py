from fastapi import FastAPI
from contextlib import asynccontextmanager
from .routers import users, tasks
from .mongo import connect_to_mongo, disconnect_from_mongo, ensure_indexes


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup")
    await connect_to_mongo()
    await ensure_indexes()
    yield
    await disconnect_from_mongo()
    print("Application shutdown")

app = FastAPI(lifespan=lifespan)

app.include_router(users.router)
app.include_router(tasks.router)
