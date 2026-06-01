from pydantic_settings import BaseSettings
from functools import lru_cache
from urllib.parse import quote_plus
import os

class Settings(BaseSettings):
    APP_NAME: str = "DocFlow SaaS"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True

    # Database (individual vars — safer than full URL)
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "Muizz1203#")
    DB_NAME: str = os.getenv("DB_NAME", "document_scanner")

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{quote_plus(self.DB_PASSWORD)}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # File Upload
    UPLOAD_FOLDER: str = "./app/static/uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS: list = ["pdf", "tiff", "tif", "jpg", "jpeg", "png"]

    # OCR
    OCR_ENGINE: str = os.getenv("OCR_ENGINE", "tesseract")
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