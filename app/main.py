from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import ping_db
from app.routes import upload, storage
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    await ping_db()
    yield

app = FastAPI(
    title="Data Lake API",
    description="API de stockage documentaire — Bronze / Silver / Gold",
    version="1.0.0",
    lifespan=lifespan
)

# CORS pour que le front React puisse appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(storage.router)