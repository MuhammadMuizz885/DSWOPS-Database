from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Application
    APP_NAME: str = "DocFlow SaaS"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "mysql+pymysql://root:Muizz1203#@localhost/document_scanner"
    )
    
    # File Upload
    UPLOAD_FOLDER: str = "./app/static/uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: list = ["pdf", "tiff", "tif", "jpg", "jpeg", "png"]
    
    # OCR Settings
    OCR_ENGINE: str = os.getenv("OCR_ENGINE", "tesseract")  # tesseract | easyocr | paddleocr
    OCR_LANGUAGE: str = os.getenv("OCR_LANGUAGE", "eng")
    OCR_CONFIDENCE_THRESHOLD: float = 0.5
    
    # Scanner
    SCANNER_ENABLED: bool = os.getenv("SCANNER_ENABLED", "false").lower() == "true"
    SCANNER_NAME: str = os.getenv("SCANNER_NAME", "Default Scanner")

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()