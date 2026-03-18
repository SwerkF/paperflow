from app.database import silver_collection
from datetime import datetime
from app.services.ocr_service import call_ocr

async def process_ocr(file_bytes, filename, bronze_id):
    try:
        ocr_result = await call_ocr(file_bytes, filename)

        await silver_collection.update_one(
            {"bronze_id": str(bronze_id)},
            {
                "$set": {
                    "ocr_text": ocr_result.get("text"),
                    "extracted_fields": ocr_result.get("fields", {}),
                    "status": "processed",
                    "processed_at": datetime.utcnow()
                }
            }
        )

    except Exception as e:
        print("❌ OCR ERROR:", e)