"""Tests for the validation module."""
import pytest

from audio_instruction.core.validation import (
    ValidationError,
    validate_instruction_duration,
    validate_instruction_text_length,
    validate_total_duration,
    validate_workout_instructions,
)


def test_validate_instruction_text_length_valid():
    """Test that valid instruction text lengths pass validation."""
    # Valid text (under 256 chars)
    validate_instruction_text_length("Run for 30 seconds")
    validate_instruction_text_length("A" * 256)  # Exactly at limit


def test_validate_instruction_text_length_invalid():
    """Test that invalid instruction text lengths fail validation."""
    # Text too long (over 256 chars)
    with pytest.raises(ValidationError):
        validate_instruction_text_length("A" * 257)


def test_validate_instruction_duration_valid():
    """Test that valid instruction durations pass validation."""
    # Valid durations
    validate_instruction_duration("Run", 10)  # Exactly at limit
    validate_instruction_duration("Walk", 60)  # Well above limit


def test_validate_instruction_duration_invalid():
    """Test that invalid instruction durations fail validation."""
    # Duration too short
    with pytest.raises(ValidationError):
        validate_instruction_duration("Run", 9)  # Just below limit
    
    with pytest.raises(ValidationError):
        validate_instruction_duration("Jump", 5)  # Well below limit


def test_validate_total_duration_valid():
    """Test that valid total durations pass validation."""
    # Valid total durations
    validate_total_duration([("Run", 60), ("Walk", 60)])  # 2 minutes
    
    # Just at limit (4 hours)
    instructions = [("Exercise", 3600) for _ in range(4)]  # 4 hours total
    validate_total_duration(instructions)


def test_validate_total_duration_invalid():
    """Test that invalid total durations fail validation."""
    # Just over limit (4 hours + 1 second)
    instructions = [("Exercise", 3600) for _ in range(4)]  # 4 hours
    instructions.append(("Extra", 1))  # Add 1 second over limit
    
    with pytest.raises(ValidationError):
        validate_total_duration(instructions)


def test_validate_workout_instructions_valid():
    """Test that valid workout instructions pass validation."""
    # Valid instructions
    instructions = [
        ("Warm up", 60),
        ("Exercise 1", 30),
        ("Rest", 15),
        ("Exercise 2", 30),
        ("Cool down", 60)
    ]
    
    validate_workout_instructions(instructions)


def test_validate_workout_instructions_invalid_empty():
    """Test that empty workout instructions fail validation."""
    with pytest.raises(ValidationError):
        validate_workout_instructions([])


def test_validate_workout_instructions_invalid_text():
    """Test that workout instructions with invalid text fail validation."""
    # One instruction has too long text
    instructions = [
        ("Warm up", 60),
        ("A" * 257, 30),  # Too long text
        ("Cool down", 60)
    ]
    
    with pytest.raises(ValidationError):
        validate_workout_instructions(instructions)


def test_validate_workout_instructions_invalid_duration():
    """Test that workout instructions with invalid duration fail validation."""
    # One instruction has too short duration
    instructions = [
        ("Warm up", 60),
        ("Exercise", 5),  # Too short duration
        ("Cool down", 60)
    ]
    
    with pytest.raises(ValidationError):
        validate_workout_instructions(instructions)


def test_validate_workout_instructions_invalid_total_duration():
    """Test that workout instructions with invalid total duration fail validation."""
    # Total duration exceeds limit
    instructions = [("Long exercise", 3600) for _ in range(5)]  # 5 hours total
    
    with pytest.raises(ValidationError):
        validate_workout_instructions(instructions) 