import unittest
from unittest.mock import MagicMock, Mock, patch

import numpy as np
from pydub import AudioSegment

from audio_instruction.core.audio import adjust_loudness


class TestAudioNormalization(unittest.TestCase):
    
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


if __name__ == '__main__':
    unittest.main() 