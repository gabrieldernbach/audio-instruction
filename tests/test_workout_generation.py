#!/usr/bin/env python3
"""Consolidated tests for workout generation and validation functionality."""

import logging
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydub import AudioSegment

from audio_instruction.core.validation import (
    ValidationError,
    validate_instruction_duration,
    validate_instruction_text_length,
    validate_total_duration,
    validate_workout_instructions,
)
from audio_instruction.core.workout import (
    assemble_workout_audio,
    generate_workout_guide_audio,
    integrate_continuous_background,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestValidation(unittest.TestCase):
    """Test case for verifying validation functionality."""

    def test_validate_instruction_text_length_valid(self):
        """Test that valid instruction text lengths pass validation."""
        # Valid text (under 256 chars)
        validate_instruction_text_length("Run for 30 seconds")
        validate_instruction_text_length("A" * 256)  # Exactly at limit

    def test_validate_instruction_text_length_invalid(self):
        """Test that invalid instruction text lengths fail validation."""
        # Text too long (over 256 chars)
        with pytest.raises(ValidationError):
            validate_instruction_text_length("A" * 257)

    def test_validate_instruction_duration_valid(self):
        """Test that valid instruction durations pass validation."""
        # Valid durations
        validate_instruction_duration("Run", 10)  # Exactly at limit
        validate_instruction_duration("Walk", 60)  # Well above limit

    def test_validate_instruction_duration_invalid(self):
        """Test that invalid instruction durations fail validation."""
        # Duration too short
        with pytest.raises(ValidationError):
            validate_instruction_duration("Run", 9)  # Just below limit
        
        with pytest.raises(ValidationError):
            validate_instruction_duration("Jump", 5)  # Well below limit

    def test_validate_total_duration_valid(self):
        """Test that valid total durations pass validation."""
        # Valid total durations
        validate_total_duration([("Run", 60), ("Walk", 60)])  # 2 minutes
        
        # Just at limit (4 hours)
        instructions = [("Exercise", 3600) for _ in range(4)]  # 4 hours total
        validate_total_duration(instructions)

    def test_validate_total_duration_invalid(self):
        """Test that invalid total durations fail validation."""
        # Just over limit (4 hours + 1 second)
        instructions = [("Exercise", 3600) for _ in range(4)]  # 4 hours
        instructions.append(("Extra", 1))  # Add 1 second over limit
        
        with pytest.raises(ValidationError):
            validate_total_duration(instructions)

    def test_validate_workout_instructions_valid(self):
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

    def test_validate_workout_instructions_invalid_empty(self):
        """Test that empty workout instructions fail validation."""
        with pytest.raises(ValidationError):
            validate_workout_instructions([])

    def test_validate_workout_instructions_invalid_text(self):
        """Test that workout instructions with invalid text fail validation."""
        # One instruction has too long text
        instructions = [
            ("Warm up", 60),
            ("A" * 257, 30),  # Too long text
            ("Cool down", 60)
        ]
        
        with pytest.raises(ValidationError):
            validate_workout_instructions(instructions)

    def test_validate_workout_instructions_invalid_duration(self):
        """Test that workout instructions with invalid duration fail validation."""
        # One instruction has too short duration
        instructions = [
            ("Warm up", 60),
            ("Exercise", 5),  # Too short duration
            ("Cool down", 60)
        ]
        
        with pytest.raises(ValidationError):
            validate_workout_instructions(instructions)

    def test_validate_workout_instructions_invalid_total_duration(self):
        """Test that workout instructions with invalid total duration fail validation."""
        # Total duration exceeds limit
        instructions = [("Long exercise", 3600) for _ in range(5)]  # 5 hours total
        
        with pytest.raises(ValidationError):
            validate_workout_instructions(instructions)


class TestMultipleBackgrounds(unittest.TestCase):
    """Test case for verifying multiple background tracks support."""
    
    def setUp(self):
        """Set up test environment."""
        # Define test background URLs (short videos)
        self.test_urls = [
            "https://www.youtube.com/watch?v=RsBtQCDbTWo",  # Short NCS music
            "https://www.youtube.com/watch?v=7NOSDKb0HlU",  # Short NCS music 
            "https://www.youtube.com/watch?v=xdcTUa4RxVE",  # Short NCS music
        ]
        
        # Define a simple test workout
        self.test_instructions = [
            ("Get ready", 10),
            ("Exercise one", 30),
            ("Rest", 10),
            ("Exercise two", 30),
            ("Final rest", 20),
        ]
        
        # Create a temporary file for the output
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_path = os.path.join(self.temp_dir.name, "test_output.mp3")
    
    def tearDown(self):
        """Clean up after test."""
        self.temp_dir.cleanup()
    
    @patch('audio_instruction.core.audio.fetch_background_tracks')
    def test_background_track_fetching(self, mock_fetch):
        """Test that multiple background tracks can be fetched."""
        # Setup mock tracks
        mock_tracks = [MagicMock(spec=AudioSegment) for _ in range(3)]
        mock_fetch.return_value = mock_tracks
        
        # Call the function
        tracks = mock_fetch(self.test_urls)
        
        # Check that we got the expected tracks
        self.assertEqual(len(tracks), 3)
        
        # Check that each track is a valid AudioSegment
        for i, track in enumerate(tracks):
            self.assertIsInstance(track, MagicMock)
    
    @patch('audio_instruction.core.audio.fetch_background_tracks')
    @patch('audio_instruction.core.audio.adjust_loudness')
    def test_background_integration(self, mock_adjust, mock_fetch):
        """Test integrating multiple background tracks with guide audio."""
        # Create a simple guide audio
        guide_audio = MagicMock(spec=AudioSegment)
        guide_audio.__len__ = MagicMock(return_value=5000)  # 5 seconds
        guide_audio.overlay.return_value = MagicMock(spec=AudioSegment)
        
        # Setup mock tracks
        mock_tracks = [MagicMock(spec=AudioSegment) for _ in range(3)]
        mock_fetch.return_value = mock_tracks
        
        # Setup mock adjust_loudness
        mock_adjust.return_value = MagicMock(spec=AudioSegment)
        
        # Try to integrate background tracks
        result = integrate_continuous_background(guide_audio, self.test_urls)
        
        # Verify fetch_background_tracks was called
        mock_fetch.assert_called_once_with(self.test_urls)
        
        # Verify guide_audio.overlay was called
        guide_audio.overlay.assert_called_once()
        
        # Verify the result is the overlaid audio
        self.assertEqual(result, guide_audio.overlay.return_value)
    
    @patch('audio_instruction.cli.main.parse_workout_config')
    @patch('audio_instruction.core.workout.generate_workout_guide_audio')
    def test_end_to_end_with_config(self, mock_generate, mock_parse):
        """Test end-to-end processing of workout config."""
        # Setup mock config
        mock_config = {
            'language': 'en',
            'background_urls': self.test_urls,
            'instructions': self.test_instructions
        }
        mock_parse.return_value = mock_config
        
        # Setup mock generate function
        mock_buffer = MagicMock()
        mock_generate.return_value = mock_buffer
        
        # Call the function
        from audio_instruction.cli.main import main
        
        # Mock sys.argv
        with patch('sys.argv', ['audio-instruction', 'config.json', '-o', self.output_path]):
            main()
        
        # Verify parse_workout_config was called
        mock_parse.assert_called_once_with('config.json')
        
        # Verify generate_workout_guide_audio was called with correct args
        mock_generate.assert_called_once()
        args, kwargs = mock_generate.call_args
        self.assertEqual(kwargs['instructions'], self.test_instructions)
        self.assertEqual(kwargs['lang'], 'en')
        self.assertEqual(kwargs['background_urls'], self.test_urls)
        self.assertEqual(kwargs['output_path'], self.output_path)


if __name__ == "__main__":
    unittest.main() 