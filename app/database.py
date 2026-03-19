import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# Sur Render, load_dotenv() n’est pas utile, on utilise les variables d’env directement
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "datalake_admin")

if not MONGODB_URI:
    raise Exception("❌ MONGODB_URI n'est pas défini dans les variables d'environnement !")

# Initialisation du client Mongo
client = AsyncIOMotorClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=5000  # Timeout rapide pour éviter de bloquer l'app
)

# Base et collections
db = client[DB_NAME]

users_collection = db["users"]
bronze_collection = db["bronze"]
silver_collection = db["silver"]
gold_collection   = db["gold"]

# Test de connexion
async def ping_db():
    await client.admin.command("ping")
    print("✅ Connecté à MongoDB Atlas !")