import httpx

async def call_ocr(file_bytes, filename):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://ocr:5000/ocr",  # à adapter si besoin
            files={"file": (filename, file_bytes)}
        )
        return response.json()