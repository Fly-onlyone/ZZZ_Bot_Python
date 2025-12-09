"""
Image Comparison Strategy Pattern

Provides extensible image comparison strategies following the Strategy Pattern.
Enables easy addition of new comparison algorithms without modifying existing code.
"""

import logging
from abc import ABC, abstractmethod
from typing import Union

import cv2
import numpy as np

from core.constants import IMAGE_MATCH_THRESHOLD, IMAGE_BINARY_THRESHOLD

logger = logging.getLogger(__name__)

# Type aliases
ImageType = Union[str, np.ndarray]


class IImageComparisonStrategy(ABC):
    """
    Strategy interface for image comparison algorithms.

    Implements the Strategy Pattern to enable swappable comparison methods.
    """

    @abstractmethod
    def compare(self, img1: ImageType, img2: ImageType) -> float:
        """
        Compare two images and return similarity/difference metric.

        Args:
            img1: First image (file path or numpy array)
            img2: Second image (file path or numpy array)

        Returns:
            float: Comparison result (interpretation depends on strategy)
        """
        pass

    @abstractmethod
    def is_match(
        self, img1: ImageType, img2: ImageType, threshold: float = IMAGE_MATCH_THRESHOLD
    ) -> bool:
        """
        Determine if two images match based on threshold.

        Args:
            img1: First image
            img2: Second image
            threshold: Matching threshold

        Returns:
            bool: True if images match
        """
        pass

    @staticmethod
    def load_image(image: ImageType) -> np.ndarray:
        """
        Load image from path or return array directly.

        Args:
            image: File path or numpy array

        Returns:
            numpy.ndarray: Loaded image

        Raises:
            ValueError: If image cannot be loaded
        """
        if isinstance(image, str):
            img = cv2.imread(image)
            if img is None:
                raise ValueError(f"Could not load image from path: {image}")
            return img
        elif isinstance(image, np.ndarray):
            return image
        else:
            raise ValueError(
                f"Image must be file path (str) or numpy.ndarray, got {type(image)}"
            )


class PixelDifferenceStrategy(IImageComparisonStrategy):
    """
    Pixel-by-pixel difference comparison strategy.

    Compares images by computing absolute difference and thresholding.
    Returns percentage of different pixels (0-100).

    Best for: Exact matching, UI state detection
    """

    def __init__(self, binary_threshold: int = IMAGE_BINARY_THRESHOLD):
        """
        Initialize strategy with binary threshold.

        Args:
            binary_threshold: Threshold for binary difference (0-255)
        """
        self.binary_threshold = binary_threshold

    def compare(self, img1: ImageType, img2: ImageType) -> float:
        """
        Calculate percentage of different pixels.

        Args:
            img1: First image
            img2: Second image

        Returns:
            float: Difference percentage (0-100)
        """
        # Load images
        image1 = self.load_image(img1)
        image2 = self.load_image(img2)

        # Resize to match dimensions
        if image1.shape != image2.shape:
            image2 = cv2.resize(image2, (image1.shape[1], image1.shape[0]))

        # Compute absolute difference
        difference = cv2.absdiff(image1, image2)

        # Convert to grayscale
        gray_diff = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)

        # Apply binary threshold
        _, threshold_diff = cv2.threshold(
            gray_diff, self.binary_threshold, 255, cv2.THRESH_BINARY
        )

        # Calculate difference percentage
        non_zero_count = np.count_nonzero(threshold_diff)
        total_pixels = threshold_diff.size
        difference_percentage = (non_zero_count / total_pixels) * 100

        logger.debug(f"Pixel difference: {difference_percentage:.2f}%")
        return difference_percentage

    def is_match(
        self, img1: ImageType, img2: ImageType, threshold: float = IMAGE_MATCH_THRESHOLD
    ) -> bool:
        """
        Check if images match based on difference threshold.

        Args:
            img1: First image
            img2: Second image
            threshold: Maximum allowed difference percentage

        Returns:
            bool: True if difference < threshold
        """
        diff = self.compare(img1, img2)
        is_match = diff < threshold
        logger.debug(
            f"Match result: {is_match} (diff: {diff:.2f}%, threshold: {threshold}%)"
        )
        return is_match


class TemplateMatchingStrategy(IImageComparisonStrategy):
    """
    Template matching comparison strategy.

    Uses OpenCV template matching to find img2 within img1.
    Returns confidence score (0-1).

    Best for: Finding small images within larger images, pattern detection
    """

    def __init__(self, method: int = cv2.TM_CCOEFF_NORMED):
        """
        Initialize strategy with matching method.

        Args:
            method: OpenCV template matching method
                    (TM_SQDIFF, TM_SQDIFF_NORMED, TM_CCORR, TM_CCORR_NORMED,
                     TM_CCOEFF, TM_CCOEFF_NORMED)
        """
        self.method = method

    def compare(self, img1: ImageType, img2: ImageType) -> float:
        """
        Perform template matching and return confidence score.

        Args:
            img1: Source image (larger image)
            img2: Template image (smaller image to find)

        Returns:
            float: Confidence score (0-1, higher is better)
        """
        # Load images
        source = self.load_image(img1)
        template = self.load_image(img2)

        # Convert to grayscale for matching
        source_gray = cv2.cvtColor(source, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

        # Perform template matching
        result = cv2.matchTemplate(source_gray, template_gray, self.method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # For TM_SQDIFF methods, lower is better; for others, higher is better
        if self.method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
            confidence = 1 - min_val
        else:
            confidence = max_val

        logger.debug(f"Template matching confidence: {confidence:.4f}")
        return confidence

    def is_match(
        self, img1: ImageType, img2: ImageType, threshold: float = 0.8
    ) -> bool:
        """
        Check if template matches based on confidence threshold.

        Args:
            img1: Source image
            img2: Template image
            threshold: Minimum confidence score (0-1)

        Returns:
            bool: True if confidence >= threshold
        """
        confidence = self.compare(img1, img2)
        is_match = confidence >= threshold
        logger.debug(
            f"Template match: {is_match} (confidence: {confidence:.4f}, threshold: {threshold})"
        )
        return is_match


class StructuralSimilarityStrategy(IImageComparisonStrategy):
    """
    Structural Similarity Index (SSIM) comparison strategy.

    Compares images based on structural information.
    Returns SSIM score (0-1, higher is more similar).

    Best for: Perceptual similarity, allowing slight variations
    Requires: scikit-image library
    """

    def __init__(self):
        """Initialize SSIM strategy."""
        try:
            from skimage.metrics import structural_similarity

            self.ssim = structural_similarity
        except ImportError:
            raise ImportError(
                "SSIM strategy requires scikit-image. Install with: pip install scikit-image"
            )

    def compare(self, img1: ImageType, img2: ImageType) -> float:
        """
        Calculate SSIM score.

        Args:
            img1: First image
            img2: Second image

        Returns:
            float: SSIM score (0-1, higher is more similar)
        """
        # Load images
        image1 = self.load_image(img1)
        image2 = self.load_image(img2)

        # Resize to match dimensions
        if image1.shape != image2.shape:
            image2 = cv2.resize(image2, (image1.shape[1], image1.shape[0]))

        # Convert to grayscale
        gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

        # Compute SSIM
        score = self.ssim(gray1, gray2)

        logger.debug(f"SSIM score: {score:.4f}")
        return score

    def is_match(
        self, img1: ImageType, img2: ImageType, threshold: float = 0.95
    ) -> bool:
        """
        Check if images match based on SSIM threshold.

        Args:
            img1: First image
            img2: Second image
            threshold: Minimum SSIM score (0-1)

        Returns:
            bool: True if SSIM >= threshold
        """
        score = self.compare(img1, img2)
        is_match = score >= threshold
        logger.debug(
            f"SSIM match: {is_match} (score: {score:.4f}, threshold: {threshold})"
        )
        return is_match


class ImageComparator:
    """
    Context class for image comparison using Strategy Pattern.

    Allows runtime selection of comparison strategy.
    """

    def __init__(self, strategy: IImageComparisonStrategy = None):
        """
        Initialize comparator with strategy.

        Args:
            strategy: Comparison strategy (defaults to PixelDifferenceStrategy)
        """
        self.strategy = strategy or PixelDifferenceStrategy()

    def set_strategy(self, strategy: IImageComparisonStrategy) -> None:
        """
        Change comparison strategy at runtime.

        Args:
            strategy: New strategy to use
        """
        self.strategy = strategy
        logger.info(f"Switched to strategy: {strategy.__class__.__name__}")

    def compare(self, img1: ImageType, img2: ImageType) -> float:
        """
        Compare images using current strategy.

        Args:
            img1: First image
            img2: Second image

        Returns:
            float: Comparison result
        """
        return self.strategy.compare(img1, img2)

    def is_match(
        self, img1: ImageType, img2: ImageType, threshold: float = None
    ) -> bool:
        """
        Check if images match using current strategy.

        Args:
            img1: First image
            img2: Second image
            threshold: Optional threshold (uses strategy default if None)

        Returns:
            bool: True if images match
        """
        if threshold is None:
            return self.strategy.is_match(img1, img2)
        else:
            return self.strategy.is_match(img1, img2, threshold)
