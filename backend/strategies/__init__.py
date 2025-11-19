"""
Strategies Package

Contains strategy pattern implementations for extensible algorithms.
Strategies enable runtime algorithm selection and easy addition of new implementations.
"""

from .ImageComparisonStrategy import (
    IImageComparisonStrategy,
    PixelDifferenceStrategy,
    TemplateMatchingStrategy,
    StructuralSimilarityStrategy,
    ImageComparator,
)

__all__ = [
    "IImageComparisonStrategy",
    "PixelDifferenceStrategy",
    "TemplateMatchingStrategy",
    "StructuralSimilarityStrategy",
    "ImageComparator",
]
