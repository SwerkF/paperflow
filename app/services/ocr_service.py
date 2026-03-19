import os
import httpx


OCR_SERVICE_URL = os.getenv("OCR_SERVICE_URL", "http://ocr:5000/ocr")


async def call_ocr(file_bytes: bytes, filename: str) -> dict:
    timeout = httpx.Timeout(60.0, connect=10.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            OCR_SERVICE_URL,
            files={"file": (filename, file_bytes)},
        )
        response.raise_for_status()
        return response.json()