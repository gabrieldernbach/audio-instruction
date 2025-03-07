import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from pydub import AudioSegment

from audio_instruction.core.audio import download_youtube_audio, fetch_background_tracks


class TestYouTubeDownload(unittest.TestCase):
    
    @patch('subprocess.run')
    @patch('os.makedirs')
    @patch('os.remove')
    @patch('audio_instruction.core.audio.AudioSegment.from_file')
    def test_download_youtube_audio(self, mock_from_file, mock_remove, mock_makedirs, mock_run):
        """Test that YouTube audio is downloaded correctly."""
        # Setup mocks
        mock_audio = MagicMock(spec=AudioSegment)
        mock_from_file.return_value = mock_audio
        mock_run.return_value = MagicMock()
        
        # Test the function
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = download_youtube_audio(url)
        
        # Verify the function calls
        mock_makedirs.assert_called_once_with("tmp", exist_ok=True)
        mock_run.assert_called_once()
        self.assertTrue(mock_run.call_args[0][0][0] == "yt-dlp")
        self.assertTrue(url in mock_run.call_args[0][0])
        mock_from_file.assert_called_once()
        mock_remove.assert_called_once()
        self.assertEqual(result, mock_audio)
    
    @patch('audio_instruction.core.audio.download_youtube_audio')
    def test_fetch_background_tracks(self, mock_download_youtube_audio):
        """Test that multiple YouTube tracks are downloaded concurrently."""
        # Setup mocks
        mock_audio1 = MagicMock(spec=AudioSegment)
        mock_audio2 = MagicMock(spec=AudioSegment)
        
        # Configure the mock to return different values for different calls
        mock_download_youtube_audio.side_effect = [mock_audio1, mock_audio2]
        
        # Test the function
        urls = [
            "https://www.youtube.com/watch?v=video1",
            "https://www.youtube.com/watch?v=video2"
        ]
        result = fetch_background_tracks(urls)
        
        # Verify results
        self.assertEqual(len(result), 2)
        self.assertIn(mock_audio1, result)
        self.assertIn(mock_audio2, result)
        self.assertEqual(mock_download_youtube_audio.call_count, 2)
        
    @patch('subprocess.run')
    def test_download_youtube_audio_real_url(self, mock_run):
        """Test with a real URL but mock the subprocess call."""
        # Configure the mock to simulate successful download
        mock_run.return_value = MagicMock()
        
        # Create a temporary mock audio file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        # Replace the actual file creation with our temporary file
        def side_effect(*args, **kwargs):
            with open(args[0][8], 'w') as f:
                f.write("mock mp3 content")
            return MagicMock()
            
        mock_run.side_effect = side_effect
        
        # Patch the from_file method to return a mock AudioSegment
        with patch('audio_instruction.core.audio.AudioSegment.from_file') as mock_from_file:
            mock_audio = MagicMock(spec=AudioSegment)
            mock_from_file.return_value = mock_audio
            
            # Test the function with a real URL from the example
            url = "https://www.youtube.com/watch?v=NWEHKTyaVc0"
            result = download_youtube_audio(url)
            
            # Verify the YouTube URL is correctly passed to yt-dlp
            self.assertTrue(any(url in str(call) for call in mock_run.call_args_list))
            self.assertEqual(result, mock_audio)
        
        # Clean up (if the file exists)
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


if __name__ == '__main__':
    unittest.main() 