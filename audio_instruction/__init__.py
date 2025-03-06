"""Audio Instruction - A tool for generating workout audio guides.

This package provides tools for creating audio workout guides with text-to-speech instructions
and optional background music from YouTube.
"""

__version__ = "0.1.0"

from audio_instruction.core.validation import (
    ValidationError,
    validate_workout_instructions,
)
from audio_instruction.core.workout import generate_workout_guide_audio

__all__ = ["generate_workout_guide_audio", "validate_workout_instructions", "ValidationError"] 