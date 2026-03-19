from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import ping_db
from app.routes import upload, storage
from app.routes import users
from app.routes import entreprises
from app.routes import dossiers
from app.routes import webhook
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await ping_db()
        print("✅ MongoDB connecté")
    except Exception as e:
        print("❌ MongoDB non connecté :", e)
    yield


class LimitUploadSize(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.method == "POST":
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > 50 * 1024 * 1024:
                return Response("Fichier trop volumineux. Maximum 50MB", status_code=413)
        return await call_next(request)


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

# ── Limite taille body à 50MB ──
app.add_middleware(LimitUploadSize)

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