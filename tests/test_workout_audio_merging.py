import io
import unittest
from unittest.mock import MagicMock, call, patch

import pytest
from pydub import AudioSegment

from audio_instruction.core.workout import (
    assemble_workout_audio,
    generate_workout_guide_audio,
    integrate_continuous_background,
)


class TestWorkoutAudioMerging(unittest.TestCase):
    
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
    
    @pytest.mark.skip(reason="Needs deeper mocking of AudioSegment internals")    
    @patch('audio_instruction.core.tts.build_instruction_audio')
    @patch('audio_instruction.core.audio.adjust_loudness')
    @patch('numpy.max')
    @patch('numpy.abs')
    @patch('numpy.array')
    @patch('pydub.AudioSegment.empty')
    def test_assemble_workout_audio(self, mock_empty, mock_array, mock_abs, mock_max, 
                                    mock_adjust_loudness, mock_build_instruction_audio):
        """Test assembling workout audio from instructions."""
        # Setup mocks
        mock_build_instruction_audio.side_effect = [self.mock_segment1, self.mock_segment2]
        mock_adjust_loudness.return_value = MagicMock(spec=AudioSegment)
        
        # Set up for adjust_loudness
        mock_max.return_value = 1  # Non-zero max value
        mock_abs.return_value = [1, 2, 3]  # Non-empty array for abs
        mock_array.return_value = [1, 2, 3]  # Sample array
        
        # Create a simple combined audio segment manually instead of mocking __iadd__
        combined_audio = MagicMock(spec=AudioSegment)
        combined_audio.channels = 2  # Required for adjust_loudness
        combined_audio.get_array_of_samples.return_value = [1, 2, 3]
        mock_empty.return_value = combined_audio
        
        # Define test instructions
        instructions = [
            ("First instruction", 10),
            ("Second instruction", 20)
        ]
        
        # Test the function
        result = assemble_workout_audio(instructions, lang="en")
        
        # Verify the correct functions were called
        self.assertEqual(mock_build_instruction_audio.call_count, 2)
        mock_build_instruction_audio.assert_has_calls([
            call("First instruction", 10, "en"),
            call("Second instruction", 20, "en")
        ])
        
        # Verify loudness was adjusted
        mock_adjust_loudness.assert_called_once()
        self.assertEqual(result, mock_adjust_loudness.return_value)
    
    @pytest.mark.skip(reason="Needs deeper mocking of fetch_background_tracks")
    @patch('audio_instruction.core.audio.fetch_background_tracks')
    @patch('audio_instruction.core.audio.adjust_loudness')
    @patch('audio_instruction.core.audio.merge_background_tracks')
    def test_integrate_continuous_background(self, mock_merge, mock_adjust, mock_fetch):
        """Test integrating background music with guide audio."""
        # Mock guide audio
        mock_guide = MagicMock(spec=AudioSegment)
        mock_guide.__len__ = MagicMock(return_value=60000)  # 1 minute
        mock_guide.overlay.return_value = MagicMock(spec=AudioSegment)
        
        # Create mock tracks with required attributes
        mock_track1 = MagicMock(spec=AudioSegment)
        mock_track2 = MagicMock(spec=AudioSegment)
        
        # Set required attributes
        for track in [mock_track1, mock_track2]:
            track.channels = 2
            track.get_array_of_samples.return_value = []
            track.apply_gain.return_value = MagicMock(spec=AudioSegment)
        
        # Set up mock return values
        mock_fetch.return_value = [mock_track1, mock_track2]
        mock_adjust.return_value = MagicMock(spec=AudioSegment)
        mock_merge.return_value = MagicMock(spec=AudioSegment)
        
        # Test the function
        urls = ["https://example.com/track1", "https://example.com/track2"]
        result = integrate_continuous_background(mock_guide, urls)
        
        # Verify fetching and integration
        mock_fetch.assert_called_once_with(urls)
        mock_guide.overlay.assert_called_once()
        self.assertEqual(result, mock_guide.overlay.return_value)
        
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


if __name__ == '__main__':
    unittest.main() 