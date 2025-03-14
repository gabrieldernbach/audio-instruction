#!/usr/bin/env python3
"""Test script to verify support for multiple background tracks."""

import logging
import os
import tempfile
import unittest
from pathlib import Path

from pydub import AudioSegment

from audio_instruction.cli.main import parse_workout_config
from audio_instruction.core.audio import fetch_background_tracks
from audio_instruction.core.workout import (
    generate_workout_guide_audio,
    integrate_continuous_background,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    
    def test_background_track_fetching(self):
        """Test that multiple background tracks can be fetched."""
        logger.info(f"Testing fetching of {len(self.test_urls)} background tracks")
        
        # Fetch the tracks
        tracks = fetch_background_tracks(self.test_urls)
        
        # Check that we got some tracks (might not get all due to YouTube restrictions)
        self.assertGreater(len(tracks), 0, "Failed to fetch any background tracks")
        logger.info(f"Successfully fetched {len(tracks)} tracks")
        
        # Check that each track is a valid AudioSegment with a length
        for i, track in enumerate(tracks):
            self.assertIsInstance(track, AudioSegment, f"Track {i} is not an AudioSegment")
            self.assertGreater(len(track), 0, f"Track {i} has zero length")
            logger.info(f"Track {i} length: {len(track)/1000:.2f} seconds")
    
    def test_background_integration(self):
        """Test integrating multiple background tracks with guide audio."""
        # Create a simple guide audio
        guide_audio = AudioSegment.silent(duration=5000)  # 5 seconds
        
        # Try to integrate background tracks
        try:
            result = integrate_continuous_background(guide_audio, self.test_urls)
            
            # Check that the result has the same length as the guide
            self.assertEqual(len(result), len(guide_audio), 
                             "Integrated audio length doesn't match guide audio length")
            
            # The integrated audio should be different from the original silent audio
            # (this is a simple check that some background audio was added)
            self.assertNotEqual(result.rms, guide_audio.rms, 
                                "Integrated audio RMS is the same as silent guide audio")
            
            logger.info(f"Successfully integrated background tracks into guide audio")
        except Exception as e:
            self.fail(f"Integration of background tracks failed: {e}")
    
    def test_end_to_end_with_hiit_txt(self):
        """Test end-to-end processing of HIIT.txt with multiple backgrounds."""
        # Path to hiit.txt
        hiit_path = Path(__file__).parent.parent / "examples" / "sample_workouts" / "hiit.txt"
        
        # Make sure the file exists
        self.assertTrue(hiit_path.exists(), f"Cannot find HIIT.txt at {hiit_path}")
        
        # Parse the configuration
        try:
            config = parse_workout_config(str(hiit_path))
            
            # Check for multiple background URLs
            self.assertIn('background_urls', config, "No background_urls field in config")
            self.assertGreater(len(config['background_urls']), 1, 
                              f"Expected multiple background URLs, got {len(config['background_urls'])}")
            logger.info(f"Found {len(config['background_urls'])} background URLs in HIIT.txt")
            
            # Generate workout audio
            output_buffer = generate_workout_guide_audio(
                instructions=config['instructions'],
                lang=config['language'],
                background_urls=config['background_urls'],
                output_path=self.output_path
            )
            
            # Check that the output file was created
            self.assertTrue(os.path.exists(self.output_path), f"Output file not created at {self.output_path}")
            
            # Check that the file has content
            self.assertGreater(os.path.getsize(self.output_path), 0, "Output file is empty")
            logger.info(f"Generated workout audio with size {os.path.getsize(self.output_path)/1024/1024:.2f} MB")
            
            # Try to load the file to ensure it's valid
            audio = AudioSegment.from_file(self.output_path, format="mp3")
            logger.info(f"Generated audio duration: {len(audio)/1000:.2f} seconds")
            
        except Exception as e:
            self.fail(f"End-to-end test failed: {e}")


if __name__ == "__main__":
    unittest.main() 