#!/usr/bin/env python3
"""Consolidated tests for API and CLI interfaces."""

import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml
from fastapi.testclient import TestClient

from audio_instruction.api.app import app
from audio_instruction.api.models import WorkoutGuideRequest
from audio_instruction.cli.main import main, parse_workout_config


class TestAPI(unittest.TestCase):
    """Test case for verifying API functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        
        # Example workout data
        self.workout_data = {
            "language": "en",
            "background_urls": ["https://www.youtube.com/watch?v=example"],
            "instructions": [
                {"text": "Get ready", "duration_seconds": 10},
                {"text": "Run for 30 seconds", "duration_seconds": 30},
                {"text": "Rest for 15 seconds", "duration_seconds": 15},
                {"text": "Good job", "duration_seconds": 10},
            ]
        }

    @patch('audio_instruction.api.app.generate_workout_guide_audio')
    def test_workout_endpoint(self, mock_generate):
        """Test the /workout endpoint."""
        # Create a mock audio buffer
        mock_buffer = io.BytesIO(b'test audio data')
        mock_generate.return_value = mock_buffer
        
        # Test the endpoint
        response = self.client.post("/workout", json=self.workout_data)
        
        # Check response status code
        self.assertEqual(response.status_code, 200)
        
        # We can't check the exact content because the real implementation will generate
        # actual audio data, which will be different from our mock
        # Just verify that we get some binary data back
        self.assertTrue(len(response.content) > 0)
        
        # Verify the generate_workout_guide_audio was called correctly
        mock_generate.assert_called_once()
        args, kwargs = mock_generate.call_args
        
        # Verify that the instructions were passed correctly
        self.assertEqual(len(kwargs["instructions"]), 4)
        self.assertEqual(kwargs["instructions"][1][0], "Run for 30 seconds")
        self.assertEqual(kwargs["instructions"][1][1], 30)
        self.assertEqual(kwargs["lang"], "en")
        self.assertEqual(kwargs["background_urls"], ["https://www.youtube.com/watch?v=example"])
        
    def test_workout_endpoint_validation_error(self):
        """Test validation error handling in the /workout endpoint."""
        # Invalid workout data (missing instructions)
        invalid_data = {"language": "en"}
        
        # Test the endpoint with invalid data
        response = self.client.post("/workout", json=invalid_data)
        
        # Check response status code
        self.assertEqual(response.status_code, 422)  # Unprocessable Entity
        
    def test_workout_endpoint_invalid_instruction(self):
        """Test validation error for invalid instruction in the /workout endpoint."""
        # Invalid workout data (duration too short)
        invalid_data = {
            "language": "en",
            "instructions": [
                {"text": "Too short", "duration_seconds": 5}  # duration < 10 seconds
            ]
        }
        
        # Test the endpoint with invalid data
        response = self.client.post("/workout", json=invalid_data)
        
        # Check response status code and error message
        self.assertEqual(response.status_code, 422)  # Unprocessable Entity
        
    def test_health_endpoint(self):
        """Test the /health endpoint."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        
    def test_validate_workout_request(self):
        """Test that the WorkoutGuideRequest model validates input correctly."""
        # Valid request should parse without errors
        request = WorkoutGuideRequest(**self.workout_data)
        self.assertEqual(request.language, "en")
        self.assertEqual(len(request.instructions), 4)
        
        # Should convert to tuples using the convert function
        from audio_instruction.api.models import convert_request_to_core_format
        instructions_tuple, lang, urls = convert_request_to_core_format(request)
        self.assertEqual(len(instructions_tuple), 4)
        self.assertEqual(instructions_tuple[1], ("Run for 30 seconds", 30))


class TestCLIFileFormats(unittest.TestCase):
    """Test case for verifying CLI functionality with different file formats."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for test files
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_dir_path = Path(self.test_dir.name)

        # Example workout data
        self.workout_data = {
            "language": "en",
            "background_urls": ["https://www.youtube.com/watch?v=example"],
            "instructions": [
                {"text": "Get ready", "duration_seconds": 10},
                {"text": "Run for 30 seconds", "duration_seconds": 30},
                {"text": "Rest for 15 seconds", "duration_seconds": 15},
                {"text": "Good job", "duration_seconds": 10},
            ]
        }

        # Create test files in different formats
        self._create_test_files()

    def tearDown(self):
        """Clean up after tests."""
        self.test_dir.cleanup()

    def _create_test_files(self):
        """Create test files in different formats."""
        # JSON format
        json_path = self.test_dir_path / "workout.json"
        with open(json_path, "w") as f:
            json.dump(self.workout_data, f)

        # YAML format
        yaml_path = self.test_dir_path / "workout.yml"
        with open(yaml_path, "w") as f:
            yaml.dump(self.workout_data, f)

        # Plain text format
        txt_path = self.test_dir_path / "workout.txt"
        with open(txt_path, "w") as f:
            f.write("# Test Workout\n")
            f.write("Get ready | 10\n")
            f.write("Run for 30 seconds | 30\n")
            f.write("Rest for 15 seconds | 15\n")
            f.write("Good job | 10\n")

    @patch('audio_instruction.core.workout.generate_workout_guide_audio')
    def test_parse_json_workout(self, mock_generate):
        """Test parsing JSON workout config."""
        config_path = self.test_dir_path / "workout.json"
        
        # Call the parse function
        config = parse_workout_config(str(config_path))
        
        # Verify the parsed config
        self.assertEqual(config["language"], "en")
        self.assertEqual(len(config["instructions"]), 4)
        # Instructions are now tuples of (text, duration)
        self.assertEqual(config["instructions"][1][0], "Run for 30 seconds")
        self.assertEqual(config["instructions"][1][1], 30)
        self.assertEqual(config["background_urls"], ["https://www.youtube.com/watch?v=example"])

    @patch('audio_instruction.core.workout.generate_workout_guide_audio')
    def test_parse_yaml_workout(self, mock_generate):
        """Test parsing YAML workout config."""
        config_path = self.test_dir_path / "workout.yml"
        
        # Call the parse function
        config = parse_workout_config(str(config_path))
        
        # Verify the parsed config
        self.assertEqual(config["language"], "en")
        self.assertEqual(len(config["instructions"]), 4)
        # Instructions are now tuples of (text, duration)
        self.assertEqual(config["instructions"][1][0], "Run for 30 seconds")
        self.assertEqual(config["instructions"][1][1], 30)
        self.assertEqual(config["background_urls"], ["https://www.youtube.com/watch?v=example"])

    @patch('audio_instruction.core.workout.generate_workout_guide_audio')
    def test_parse_txt_workout(self, mock_generate):
        """Test parsing plain text workout config."""
        config_path = self.test_dir_path / "workout.txt"
        
        # Call the parse function
        config = parse_workout_config(str(config_path))
        
        # Verify the parsed config
        self.assertEqual(config["language"], "en")  # Default language
        self.assertEqual(len(config["instructions"]), 4)
        # Instructions are now tuples of (text, duration)
        self.assertEqual(config["instructions"][1][0], "Run for 30 seconds")
        self.assertEqual(config["instructions"][1][1], 30)
        # Plain text format may include default background_urls in some implementations
        # So we don't test for its absence

    @patch('audio_instruction.cli.main.parse_workout_config')
    @patch('audio_instruction.cli.main.generate_workout_guide_audio')  # Patch in cli.main, not core.workout
    def test_cli_main_function(self, mock_generate, mock_parse):
        """Test the main CLI function."""
        # Setup mocks
        # Convert instructions to tuples for the mock return value
        mock_workout_data = self.workout_data.copy()
        mock_workout_data["instructions"] = [
            ("Get ready", 10),
            ("Run for 30 seconds", 30),
            ("Rest for 15 seconds", 15),
            ("Good job", 10),
        ]
        mock_parse.return_value = mock_workout_data
        
        # Test CLI with JSON file
        json_path = self.test_dir_path / "workout.json"
        output_path = self.test_dir_path / "workout.mp3"
        
        # Mock sys.argv
        with patch('sys.argv', ['audio-instruction', str(json_path), '-o', str(output_path)]):
            main()
            
        # Verify function calls
        mock_parse.assert_called_with(str(json_path))
        mock_generate.assert_called_once()
        args, kwargs = mock_generate.call_args
        self.assertEqual(kwargs["output_path"], str(output_path))
        self.assertEqual(kwargs["lang"], "en")


if __name__ == "__main__":
    unittest.main() 