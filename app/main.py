from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import ping_db
from app.routes import upload, storage
from app.routes import users
from app.routes import entreprises
from app.routes import dossiers
from app.routes import webhook
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await ping_db()
        print("✅ MongoDB connecté")
    except Exception as e:
        print("❌ MongoDB non connecté :", e)
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

# Routes
app.include_router(upload.router)
app.include_router(storage.router)
app.include_router(users.router)
app.include_router(webhook.router)
app.include_router(entreprises.router)
app.include_router(dossiers.router)

# Route test pour vérifier que l'API fonctionne
@app.get("/")
def root():
    return {"message": "API OK"}