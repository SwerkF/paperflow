from datetime import datetime
from app.database import bronze_collection, silver_collection, gold_collection
from app.services.ocr_service import call_ocr


async def process_ocr(file_bytes, filename, bronze_id, dossierId=None, entrepriseId=None):
    try:
        # 1. Bronze passe en processing
        await bronze_collection.update_one(
            {"_id": bronze_id},
            {
                "$set": {
                    "status": "processing"
                }
            }
        )

        # 2. Appel OCR
        ocr_result = await call_ocr(file_bytes, filename)

        ocr_text = ocr_result.get("text")
        extracted_fields = ocr_result.get("fields", {})
        ocr_confidence = ocr_result.get("confidence")

        # 3. Mise à jour Silver
        await silver_collection.update_one(
            {"bronze_id": str(bronze_id)},
            {
                "$set": {
                    "ocr_text": ocr_text,
                    "extracted_fields": extracted_fields,
                    "ocr_confidence": ocr_confidence,
                    "status": "processed",
                    "processed_at": datetime.utcnow(),
                    "dossierId": dossierId,
                    "entrepriseId": entrepriseId
                }
            }
        )

        # 4. Récupérer Silver pour créer Gold
        silver_doc = await silver_collection.find_one({"bronze_id": str(bronze_id)})

        if silver_doc:
            await gold_collection.insert_one({
                "silver_id": str(silver_doc["_id"]),
                "bronze_id": str(bronze_id),
                "filename": filename,
                "document_type": extracted_fields.get("document_type", "unknown"),
                "validated_fields": extracted_fields,
                "coherence_score": 1.0,
                "incoherences": [],
                "is_fraudulent": False,
                "curated_at": datetime.utcnow(),
                "status": "valid",
                "dossierId": dossierId,
                "entrepriseId": entrepriseId
            })

        # 5. Bronze passe en done
        await bronze_collection.update_one(
            {"_id": bronze_id},
            {
                "$set": {
                    "status": "done"
                }
            }
        )

        print(f"✅ OCR terminé pour {filename}")

    except Exception as e:
        print("❌ OCR ERROR:", e)

        # 6. Bronze en erreur
        await bronze_collection.update_one(
            {"_id": bronze_id},
            {
                "$set": {
                    "status": "error"
                }
            }
        )

        # 7. Silver en erreur
        await silver_collection.update_one(
            {"bronze_id": str(bronze_id)},
            {
                "$set": {
                    "status": "error",
                    "processed_at": datetime.utcnow()
                }
            }
        )