from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.api.routes import router as api_router
from backend.api.excel_routes import router as excel_router
from backend.services.ocr_service import ocr_service
from backend.database.init_db import init_db
from backend.utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database & load PaddleOCR model once into memory
    init_db()
    ocr_service.initialize()
    logger.server_started(host="localhost", port=8000)
    yield
    # Shutdown
    logger.log_step("Server Shutting Down...")

app = FastAPI(
    title="PaddleOCR AI Dashboard Backend API",
    description="High-performance FastAPI service integrating PaddleOCR for live webcam, images, PDFs, and document analysis.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local React/Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(excel_router)

if __name__ == "__main__":
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
