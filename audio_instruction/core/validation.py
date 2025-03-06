"""Validation utilities for workout instruction generation."""
from typing import Any, Dict, List, Tuple


class ValidationError(Exception):
    """Exception raised for validation errors in the workout instructions."""
    pass


def validate_instruction_duration(instruction_text: str, duration_seconds: int, 
                                 min_duration: int = 10) -> None:
    """Validate that an instruction has sufficient duration.
    
    Args:
        instruction_text: The instruction text
        duration_seconds: The duration in seconds
        min_duration: Minimum acceptable duration in seconds (default: 10)
        
    Raises:
        ValidationError: If the duration is too short
    """
    if duration_seconds < min_duration:
        raise ValidationError(
            f"Exercise duration too short: '{instruction_text}' is {duration_seconds} seconds. "
            f"Minimum duration is {min_duration} seconds."
        )


def validate_instruction_text_length(instruction_text: str, max_chars: int = 256) -> None:
    """Validate that an instruction text is not too long.
    
    Args:
        instruction_text: The instruction text
        max_chars: Maximum acceptable length in characters (default: 256)
        
    Raises:
        ValidationError: If the text is too long
    """
    if len(instruction_text) > max_chars:
        raise ValidationError(
            f"Instruction text too long: '{instruction_text[:50]}...' is {len(instruction_text)} characters. "
            f"Maximum length is {max_chars} characters."
        )


def validate_total_duration(instructions: List[Tuple[str, int]], max_duration_hours: float = 4.0) -> None:
    """Validate that the total workout duration is within acceptable limits.
    
    Args:
        instructions: List of (instruction_text, duration_in_seconds) tuples
        max_duration_hours: Maximum acceptable total duration in hours (default: 4.0)
        
    Raises:
        ValidationError: If the total duration exceeds the maximum
    """
    total_seconds = sum(duration for _, duration in instructions)
    max_seconds = max_duration_hours * 3600
    
    if total_seconds > max_seconds:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        raise ValidationError(
            f"Total workout duration of {hours}h {minutes}m {seconds}s exceeds maximum of "
            f"{max_duration_hours} hours."
        )


def validate_workout_instructions(instructions: List[Tuple[str, int]], 
                                 max_text_length: int = 256,
                                 min_duration: int = 10,
                                 max_duration_hours: float = 4.0) -> None:
    """Validate all workout instructions.
    
    Args:
        instructions: List of (instruction_text, duration_in_seconds) tuples
        max_text_length: Maximum acceptable instruction text length in characters
        min_duration: Minimum acceptable instruction duration in seconds
        max_duration_hours: Maximum acceptable total workout duration in hours
        
    Raises:
        ValidationError: If any validation check fails
    """
    if not instructions:
        raise ValidationError("No workout instructions provided.")
    
    # Validate total duration
    validate_total_duration(instructions, max_duration_hours)
    
    # Validate each instruction
    for idx, (text, duration) in enumerate(instructions, 1):
        # Validate text
        validate_instruction_text_length(text, max_text_length)
        
        # Validate duration
        validate_instruction_duration(text, duration, min_duration)
    
    # All validations passed
    return 