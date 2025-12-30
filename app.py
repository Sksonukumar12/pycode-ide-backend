from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import shutil
import uuid
import os

from enhance import enhance_image

app = FastAPI(title="AI Photo Enhancer")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/enhance")
async def enhance_photo(file: UploadFile = File(...)):
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result_path = enhance_image(file_path)

    return FileResponse(
        result_path,
        media_type="image/jpeg",
        filename="enhanced.jpg"
    )
