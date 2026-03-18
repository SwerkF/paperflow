import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "datalake_admin")

client = AsyncIOMotorClient(MONGODB_URI)
db = client[DB_NAME]

bronze_collection = db["bronze"]
silver_collection = db["silver"]
gold_collection   = db["gold"]

async def ping_db():
    await client.admin.command("ping")
    print("✅ Connecté à MongoDB Atlas !")