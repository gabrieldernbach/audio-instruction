#!/usr/bin/env python3
"""Consolidated tests for audio processing functionality."""

import io
import unittest
from unittest.mock import MagicMock, Mock, patch

import numpy as np
from pydub import AudioSegment

from audio_instruction.core.audio import adjust_loudness
from audio_instruction.core.tts import build_instruction_audio, create_countdown_audio
from audio_instruction.core.workout import (
    assemble_workout_audio,
    integrate_continuous_background,
)


class TestAudioNormalization(unittest.TestCase):
    """Test case for verifying audio normalization functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock AudioSegment
        self.mock_audio = MagicMock(spec=AudioSegment)
        self.mock_audio.sample_width = 2  # 16-bit audio
        self.mock_audio.frame_rate = 44100
        self.mock_audio.channels = 2
        
    @patch('numpy.array')
    @patch('pyloudnorm.Meter')
    def test_adjust_loudness_stereo(self, mock_meter, mock_array):
        """Test loudness normalization for stereo audio."""
        # Setup mocks
        mock_meter_instance = Mock()
        mock_meter.return_value = mock_meter_instance
        mock_meter_instance.integrated_loudness.return_value = -18.0
        
        # Mock audio sample array (stereo)
        mock_samples = np.array([1000, 1000, 2000, 2000, 3000, 3000], dtype=np.int16)
        mock_array.return_value = mock_samples
        
        # Setup get_array_of_samples to return our mock samples
        self.mock_audio.get_array_of_samples.return_value = mock_samples
        
        # Mock np.max and np.abs to avoid the empty array issue
        with patch('numpy.max', return_value=3000), \
             patch('numpy.abs', return_value=mock_samples):
            # Test with target -23.0 LUFS (5dB reduction from -18.0)
            result = adjust_loudness(self.mock_audio, target_lufs=-23.0)
            
            # Verify the meter was created with correct sample rate
            mock_meter.assert_called_once_with(44100)
            
            # Verify loudness was checked and gain was applied
            mock_meter_instance.integrated_loudness.assert_called_once()
            self.mock_audio.apply_gain.assert_called_once_with(-5.0)  # -23.0 - (-18.0)
            
            # Verify the result is returned
            self.assertEqual(result, self.mock_audio.apply_gain.return_value)
        
    @patch('numpy.array')
    @patch('pyloudnorm.Meter')
    def test_adjust_loudness_mono(self, mock_meter, mock_array):
        """Test loudness normalization for mono audio."""
        # Setup mocks
        mock_meter_instance = Mock()
        mock_meter.return_value = mock_meter_instance
        mock_meter_instance.integrated_loudness.return_value = -25.0
        
        # Mock audio sample array (mono)
        mock_samples = np.array([1000, 2000, 3000], dtype=np.int16)
        mock_array.return_value = mock_samples
        
        # Configure as mono audio
        self.mock_audio.channels = 1
        self.mock_audio.get_array_of_samples.return_value = mock_samples
        
        # Mock np.max and np.abs to avoid the empty array issue
        with patch('numpy.max', return_value=3000), \
             patch('numpy.abs', return_value=mock_samples):
            # Test with target -23.0 LUFS (2dB boost from -25.0)
            result = adjust_loudness(self.mock_audio, target_lufs=-23.0)
            
            # Verify the meter was created with correct sample rate
            mock_meter.assert_called_once_with(44100)
            
            # Verify loudness was checked and gain was applied
            mock_meter_instance.integrated_loudness.assert_called_once()
            self.mock_audio.apply_gain.assert_called_once_with(2.0)  # -23.0 - (-25.0)
        
    @patch('numpy.array')
    def test_adjust_loudness_silent_audio(self, mock_array):
        """Test loudness normalization with silent audio."""
        # Setup silent audio (all zeros)
        mock_samples = np.zeros(1000, dtype=np.int16)
        mock_array.return_value = mock_samples
        self.mock_audio.get_array_of_samples.return_value = mock_samples
        
        # Mock np.max to return 0 for silent audio
        with patch('numpy.max', return_value=0), \
             patch('numpy.abs', return_value=mock_samples):
            # Test with silent audio
            result = adjust_loudness(self.mock_audio)
            
            # Verify no gain was applied (original audio is returned)
            self.mock_audio.apply_gain.assert_not_called()
            self.assertEqual(result, self.mock_audio)
        
    @patch('numpy.array')
    @patch('pyloudnorm.Meter')
    @patch('logging.warning')
    def test_adjust_loudness_exception(self, mock_warning, mock_meter, mock_array):
        """Test error handling when loudness adjustment fails."""
        # Setup mocks to raise an exception
        mock_meter_instance = Mock()
        mock_meter.return_value = mock_meter_instance
        mock_meter_instance.integrated_loudness.side_effect = Exception("Test exception")
        
        # Mock audio sample array
        mock_samples = np.array([1000, 2000, 3000], dtype=np.int16)
        mock_array.return_value = mock_samples
        self.mock_audio.get_array_of_samples.return_value = mock_samples
        
        # Mock np.max and np.abs to avoid the empty array issue
        with patch('numpy.max', return_value=3000), \
             patch('numpy.abs', return_value=mock_samples):
            # Test exception handling
            result = adjust_loudness(self.mock_audio)
            
            # Verify error was logged and original audio was returned
            mock_warning.assert_called_once()
            self.assertEqual(result, self.mock_audio)


class TestCountdownAudio(unittest.TestCase):
    """Test case for verifying the countdown audio feature."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock audio segments
        self.mock_audio = MagicMock(spec=AudioSegment)
        self.mock_audio.__add__.return_value = self.mock_audio
        self.mock_audio.set_frame_rate.return_value = self.mock_audio
        self.mock_audio.set_channels.return_value = self.mock_audio
        self.mock_audio.set_sample_width.return_value = self.mock_audio
        
        # Set required attributes to avoid issues
        self.mock_audio.channels = 2
        self.mock_audio.frame_rate = 44100
        self.mock_audio.sample_width = 2
        self.mock_audio.duration_seconds = 5
        
    @patch('audio_instruction.core.tts.generate_tts_audio')
    @patch('audio_instruction.core.tts.AudioSegment.empty')
    @patch('audio_instruction.core.tts.AudioSegment.silent')
    def test_create_countdown_audio(self, mock_silent, mock_empty, mock_generate_tts):
        """Test the countdown audio generation function."""
        # Setup mocks
        mock_generate_tts.return_value = self.mock_audio
        mock_empty.return_value = self.mock_audio
        mock_silent.return_value = self.mock_audio
        
        # Call the function
        countdown_audio = create_countdown_audio(start=3, end=1, lang="en")
        
        # Verify generate_tts_audio was called for each count
        self.assertEqual(mock_generate_tts.call_count, 3)
        
        # Verify the correct countdown values were used (in any order)
        mock_generate_tts.assert_any_call("3", "en")
        mock_generate_tts.assert_any_call("2", "en")
        mock_generate_tts.assert_any_call("1", "en")
        
    @patch('audio_instruction.core.tts.create_countdown_audio')
    @patch('audio_instruction.core.tts.generate_tts_audio')
    @patch('audio_instruction.core.tts.AudioSegment.silent')
    def test_build_instruction_audio_with_countdown(self, mock_silent, mock_generate_tts, mock_create_countdown):
        """Test that instructions include countdown."""
        # Setup mocks
        mock_generate_tts.return_value = self.mock_audio
        mock_create_countdown.return_value = self.mock_audio
        mock_silent.return_value = self.mock_audio
        
        instruction_text = "Run for 30 seconds"
        instruction_duration = 30
        
        # Call the function
        instruction_audio = build_instruction_audio(
            instruction_text, instruction_duration, "en"
        )
        
        # Verify create_countdown_audio was called
        mock_create_countdown.assert_called_once_with(lang="en")
        
        # Verify the instruction audio was created
        mock_generate_tts.assert_called_once_with(instruction_text, "en")


class TestWorkoutAudioMerging(unittest.TestCase):
    """Test case for verifying workout audio merging functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock AudioSegments
        self.mock_segment1 = MagicMock(spec=AudioSegment)
        self.mock_segment2 = MagicMock(spec=AudioSegment)
        
        # Configure mock segments
        self.mock_segment1.__add__.return_value = MagicMock(spec=AudioSegment)
        self.mock_segment1.overlay.return_value = MagicMock(spec=AudioSegment)
        
        # Set required attributes to avoid type errors
        for segment in [self.mock_segment1, self.mock_segment2]:
            segment.channels = 2
            segment.get_array_of_samples.return_value = []
    
    @patch('audio_instruction.core.workout.assemble_workout_audio')
    @patch('audio_instruction.core.workout.integrate_continuous_background')
    def test_generate_workout_guide_audio_with_background(self, mock_integrate, mock_assemble):
        """Test generating complete workout guide with background music."""
        # Setup mocks
        mock_guide_audio = MagicMock(spec=AudioSegment)
        mock_assemble.return_value = mock_guide_audio
        
        mock_integrated = MagicMock(spec=AudioSegment)
        mock_integrate.return_value = mock_integrated
        
        # Create a real BytesIO instance instead of a mock
        real_buffer = io.BytesIO()
        
        # Mock export to return the real buffer
        mock_integrated.export = MagicMock(return_value=real_buffer)
        
        # Test instructions and parameters
        instructions = [("Test instruction", 30)]
        background_urls = ["https://example.com/music"]
        
        # Use patch to replace BytesIO with a function that returns our buffer
        with patch('io.BytesIO', return_value=real_buffer):
            from audio_instruction.core.workout import generate_workout_guide_audio
            result = generate_workout_guide_audio(
                instructions=instructions,
                lang="en",
                background_urls=background_urls,
                output_path="test_output.mp3"
            )
            
            # Verify result
            mock_assemble.assert_called_once_with(instructions, "en")
            mock_integrate.assert_called_once_with(mock_guide_audio, background_urls)
            self.assertEqual(mock_integrated.export.call_count, 2)
            self.assertEqual(result, real_buffer)
    
    @patch('audio_instruction.core.workout.assemble_workout_audio')
    def test_generate_workout_guide_audio_without_background(self, mock_assemble):
        """Test generating workout guide without background music."""
        # Setup mocks
        mock_guide_audio = MagicMock(spec=AudioSegment)
        mock_assemble.return_value = mock_guide_audio
        
        # Create a real BytesIO instance
        real_buffer = io.BytesIO()
        
        # Mock export to return the real buffer
        mock_guide_audio.export = MagicMock(return_value=real_buffer)
        
        # Test without background_urls
        instructions = [("Test instruction", 30)]
        
        # Use patch to replace BytesIO with a function that returns our buffer
        with patch('io.BytesIO', return_value=real_buffer):
            from audio_instruction.core.workout import generate_workout_guide_audio
            result = generate_workout_guide_audio(
                instructions=instructions,
                lang="en",
                background_urls=None,
                output_path="test_output.mp3"
            )
            
            # Verify result
            mock_assemble.assert_called_once_with(instructions, "en")
            self.assertEqual(mock_guide_audio.export.call_count, 2)
            self.assertEqual(result, real_buffer)


if __name__ == "__main__":
    unittest.main() 