import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Image preprocessing for OCR optimization"""
    
    @staticmethod
    def preprocess(image_path: str, output_path: str = None) -> str:
        """
        Preprocess image for better OCR accuracy
        
        Args:
            image_path: Input image path
            output_path: Output path (optional)
            
        Returns:
            Path to processed image
        """
        try:
            logger.info(f"Starting image preprocessing: {image_path}")
            
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image: {image_path}")
            
            logger.info(f"Image dimensions: {img.shape}")
            
            # Apply preprocessing steps
            img = ImageProcessor._denoise(img)
            logger.info("✓ Denoising applied")
            
            img = ImageProcessor._enhance_contrast(img)
            logger.info("✓ Contrast enhancement applied")
            
            img = ImageProcessor._resize_for_ocr(img)
            logger.info("✓ Image resized for OCR")
            
            # Save processed image
            if output_path is None:
                from pathlib import Path
                path = Path(image_path)
                output_path = path.parent / f"{path.stem}_processed{path.suffix}"

                cv2.imwrite(str(output_path), img)
                logger.info(f"✓ Image preprocessing completed: {output_path}")

            return str(output_path)
        
        except Exception as e:
            logger.error(f"✗ Image preprocessing failed: {e}")
            raise

    @staticmethod
    def _denoise(img):
        """Remove noise from image"""
        try:
            return cv2.fastNlMeansDenoisingColored(
                img,
                None,
                10,
                10,
                7,
                21
            )
        except Exception as e:
            logger.warning(f"Denoising failed, continuing with original: {e}")
            return img

    @staticmethod
    def _enhance_contrast(img):
        """Increase image contrast using CLAHE"""
        try:
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            enhanced = cv2.merge([l, a, b])
            return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        except Exception as e:
            logger.warning(f"Contrast enhancement failed, continuing with original: {e}")
            return img

    @staticmethod
    def _resize_for_ocr(img, min_height=600):
        """Resize image for optimal OCR"""
        try:
            h, w = img.shape[:2]
            if h < min_height:
                scale = min_height / h
                new_w = int(w * scale)
                img = cv2.resize(img, (new_w, min_height), interpolation=cv2.INTER_CUBIC)
                logger.info(f"Image resized from {h}x{w} to {min_height}x{new_w}")
            return img
        except Exception as e:
            logger.warning(f"Resizing failed, continuing with original: {e}")
            return img