"""
Image processing utilities for converting images to sketches.
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance
import io
from typing import Tuple, Optional, Dict, Any
import logging

from app.core.exceptions import ImageProcessingError
from app.schemas.sketch import SketchStyle, SketchProcessingOptions

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Handle image processing operations for sketch generation."""
    
    @staticmethod
    def validate_image(image_bytes: bytes) -> Tuple[bool, str]:
        """Validate if the image is processable."""
        try:
            # Try to open with PIL
            image = Image.open(io.BytesIO(image_bytes))
            
            # Check format
            if image.format not in ['JPEG', 'PNG', 'WEBP']:
                return False, "Unsupported image format. Use JPEG, PNG, or WEBP."
            
            # Check size (max 4K resolution)
            if image.width > 4096 or image.height > 4096:
                return False, "Image too large. Maximum resolution is 4096x4096."
            
            # Check minimum size
            if image.width < 100 or image.height < 100:
                return False, "Image too small. Minimum resolution is 100x100."
            
            return True, "Valid image"
            
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"
    
    @staticmethod
    def get_image_info(image_bytes: bytes) -> Dict[str, Any]:
        """Get image information."""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            return {
                'width': image.width,
                'height': image.height,
                'format': image.format,
                'mode': image.mode,
                'size_bytes': len(image_bytes)
            }
        except Exception as e:
            raise ImageProcessingError(f"Failed to get image info: {str(e)}")
    
    @staticmethod
    def resize_image(
        image_bytes: bytes,
        max_width: int = 1920,
        max_height: int = 1920,
        quality: int = 85
    ) -> bytes:
        """Resize image while maintaining aspect ratio."""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Calculate new size
            ratio = min(max_width / image.width, max_height / image.height)
            if ratio < 1:
                new_width = int(image.width * ratio)
                new_height = int(image.height * ratio)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                image = background
            
            # Save to bytes
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            raise ImageProcessingError(f"Failed to resize image: {str(e)}")
    
    @staticmethod
    def create_thumbnail(image_bytes: bytes, size: Tuple[int, int] = (200, 200)) -> bytes:
        """Create thumbnail of the image."""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                image = background
            
            # Create thumbnail
            image.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save to bytes
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=80, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            raise ImageProcessingError(f"Failed to create thumbnail: {str(e)}")
    
    @classmethod
    def generate_sketch(
        cls,
        image_bytes: bytes,
        style: SketchStyle = SketchStyle.PENCIL,
        options: Optional[SketchProcessingOptions] = None
    ) -> bytes:
        """Generate sketch from image."""
        try:
            if options is None:
                options = SketchProcessingOptions()
            
            # Convert PIL image to OpenCV format
            pil_image = Image.open(io.BytesIO(image_bytes))
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Convert to numpy array
            image_array = np.array(pil_image)
            image_cv = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            # Apply style-specific processing
            if style == SketchStyle.PENCIL:
                sketch = cls._generate_pencil_sketch(image_cv, options)
            elif style == SketchStyle.CHARCOAL:
                sketch = cls._generate_charcoal_sketch(image_cv, options)
            elif style == SketchStyle.INK:
                sketch = cls._generate_ink_sketch(image_cv, options)
            elif style == SketchStyle.WATERCOLOR:
                sketch = cls._generate_watercolor_sketch(image_cv, options)
            else:
                sketch = cls._generate_pencil_sketch(image_cv, options)
            
            # Convert back to PIL and save
            sketch_rgb = cv2.cvtColor(sketch, cv2.COLOR_BGR2RGB)
            pil_sketch = Image.fromarray(sketch_rgb)
            
            # Apply post-processing
            pil_sketch = cls._apply_post_processing(pil_sketch, options)
            
            # Save to bytes
            output = io.BytesIO()
            pil_sketch.save(output, format='JPEG', quality=90, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Sketch generation failed: {str(e)}")
            raise ImageProcessingError(f"Failed to generate sketch: {str(e)}")
    
    @staticmethod
    def _generate_pencil_sketch(image: np.ndarray, options: SketchProcessingOptions) -> np.ndarray:
        """Generate pencil-style sketch."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blur = cv2.GaussianBlur(gray, (options.blur_kernel, options.blur_kernel), 0)
        
        # Create edges using Canny
        edges = cv2.Canny(blur, options.edge_threshold1, options.edge_threshold2)
        
        # Invert edges for pencil effect
        edges_inv = cv2.bitwise_not(edges)
        
        # Combine with original image
        pencil = cv2.multiply(gray, edges_inv, scale=1/255.0)
        
        # Apply intensity adjustment
        pencil = cv2.multiply(pencil, options.intensity)
        pencil = np.clip(pencil, 0, 255).astype(np.uint8)
        
        # Convert back to BGR for consistency
        return cv2.cvtColor(pencil, cv2.COLOR_GRAY2BGR)
    
    @staticmethod
    def _generate_charcoal_sketch(image: np.ndarray, options: SketchProcessingOptions) -> np.ndarray:
        """Generate charcoal-style sketch."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply heavier blur for charcoal effect
        blur = cv2.GaussianBlur(gray, (options.blur_kernel * 2 + 1, options.blur_kernel * 2 + 1), 0)
        
        # Create edges
        edges = cv2.Canny(blur, options.edge_threshold1 // 2, options.edge_threshold2 // 2)
        
        # Invert and apply charcoal effect
        edges_inv = cv2.bitwise_not(edges)
        charcoal = cv2.multiply(gray, edges_inv, scale=1/255.0)
        
        # Enhance contrast for charcoal look
        charcoal = cv2.multiply(charcoal, options.contrast * 1.5)
        charcoal = np.clip(charcoal, 0, 255).astype(np.uint8)
        
        # Apply non-linear transformation for darker areas
        charcoal = np.power(charcoal / 255.0, 1.2) * 255
        charcoal = charcoal.astype(np.uint8)
        
        return cv2.cvtColor(charcoal, cv2.COLOR_GRAY2BGR)
    
    @staticmethod
    def _generate_ink_sketch(image: np.ndarray, options: SketchProcessingOptions) -> np.ndarray:
        """Generate ink-style sketch."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Light blur
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Strong edge detection for ink effect
        edges = cv2.Canny(blur, options.edge_threshold1 * 2, options.edge_threshold2 * 2)
        
        # Apply morphological operations for ink-like strokes
        kernel = np.ones((2, 2), np.uint8)
        ink = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        # Invert for white background
        ink = cv2.bitwise_not(ink)
        
        return cv2.cvtColor(ink, cv2.COLOR_GRAY2BGR)
    
    @staticmethod
    def _generate_watercolor_sketch(image: np.ndarray, options: SketchProcessingOptions) -> np.ndarray:
        """Generate watercolor-style sketch."""
        # Reduce colors using K-means clustering
        data = image.reshape((-1, 3))
        data = np.float32(data)
        
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 15, 1.0)
        k = 8  # Number of colors
        _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # Convert back to uint8 and reshape
        centers = np.uint8(centers)
        quantized = centers[labels.flatten()]
        quantized = quantized.reshape(image.shape)
        
        # Apply bilateral filter for watercolor effect
        watercolor = cv2.bilateralFilter(quantized, 15, 50, 50)
        
        # Apply intensity adjustment
        watercolor = cv2.multiply(watercolor, options.intensity)
        watercolor = np.clip(watercolor, 0, 255).astype(np.uint8)
        
        return watercolor
    
    @staticmethod
    def _apply_post_processing(image: Image.Image, options: SketchProcessingOptions) -> Image.Image:
        """Apply post-processing effects."""
        # Adjust contrast
        if options.contrast != 1.0:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(options.contrast)
        
        # Add slight noise for texture (optional)
        if hasattr(options, 'add_texture') and options.add_texture:
            # Add very subtle noise
            image_array = np.array(image)
            noise = np.random.randint(-5, 5, image_array.shape, dtype=np.int16)
            noisy = np.clip(image_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            image = Image.fromarray(noisy)
        
        return image
