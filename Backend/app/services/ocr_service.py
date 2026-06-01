import logging
from typing import Tuple
from PIL import Image
from app.config import settings
import time
import sys
import os
import pytesseract

# Platform-aware Tesseract path
if sys.platform.startswith("win"):
    os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR"
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
else:
    # Linux/Railway — use system tesseract
    tesseract_cmd = os.environ.get("TESSERACT_CMD", "tesseract")
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

class OCRService:
    """Handle OCR text extraction from images"""
    
    @staticmethod
    def extract_text(image_path: str) -> Tuple[str, float, float]:
        """
        Extract text from image using configured OCR engine
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (text, confidence, processing_time)
        """
        try:
            start_time = time.time()
            
            if settings.OCR_ENGINE == "tesseract":
                text, confidence = OCRService._extract_tesseract(image_path)
            elif settings.OCR_ENGINE == "easyocr":
                text, confidence = OCRService._extract_easyocr(image_path)
            elif settings.OCR_ENGINE == "paddleocr":
                text, confidence = OCRService._extract_paddleocr(image_path)
            else:
                raise ValueError(f"Unknown OCR engine: {settings.OCR_ENGINE}")
            
            processing_time = time.time() - start_time
            logger.info(f"✓ OCR extraction completed in {processing_time:.2f}s")
            
            return text, confidence, processing_time
        
        except Exception as e:
            logger.error(f"✗ OCR extraction failed: {str(e)}")
            raise

    @staticmethod
    def _extract_tesseract(image_path: str) -> Tuple[str, float]:
        """Extract text using Tesseract OCR (clean + safe version)"""
        try:
            import os
            from PIL import Image
            import pytesseract

            if not os.path.exists(image_path):
                raise FileNotFoundError(f"OCR image not found: {image_path}")

            img = Image.open(image_path)

            text = pytesseract.image_to_string(
                img,
                lang=settings.OCR_LANGUAGE
            )

            data = pytesseract.image_to_data(
                img,
                output_type=pytesseract.Output.DICT
            )

            confidences = []
            for conf in data.get("confidence", []):
                try:
                    c = float(conf)
                    if c > 0:
                        confidences.append(c)
                except:
                    continue

            avg_confidence = (
                sum(confidences) / len(confidences)
                if confidences else 0.0
            )

            return text, avg_confidence / 100.0

        except Exception as e:
            logger.error(f"Tesseract extraction error: {e}")
            raise

    @staticmethod
    def _extract_easyocr(image_path: str) -> Tuple[str, float]:
        """Extract using EasyOCR"""
        try:
            import easyocr
            logger.info("Initializing EasyOCR reader...")
            reader = easyocr.Reader([settings.OCR_LANGUAGE])

            results = reader.readtext(image_path)
            
            text = "\n".join([text for (bbox, text, confidence) in results])
            avg_confidence = sum([conf for (_, _, conf) in results]) / len(results) if results else 0
            
            logger.info(f"EasyOCR extracted {len(text)} characters from {len(results)} text blocks")
            return text, avg_confidence
        except Exception as e:
            logger.error(f"EasyOCR extraction error: {e}")
            raise

    @staticmethod
    def _extract_paddleocr(image_path: str) -> Tuple[str, float]:
        """Extract using PaddleOCR"""
        try:
            from paddleocr import PaddleOCR
            logger.info("Initializing PaddleOCR reader...")
            ocr = PaddleOCR(use_angle_cls=True, lang='en')
            results = ocr.ocr(image_path, cls=True)
            
            text = "\n".join([line[0][1] for line in results])
            avg_confidence = sum([line[0][2] for line in results]) / len(results) if results else 0
            
            logger.info(f"PaddleOCR extracted {len(text)} characters")
            return text, avg_confidence
        except Exception as e:
            logger.error(f"PaddleOCR extraction error: {e}")
            raise