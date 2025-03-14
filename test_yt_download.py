#!/usr/bin/env python3
"""
Test script for YouTube download functionality.
This script tests different methods of downloading audio from YouTube URLs.
"""

import argparse
import logging
import os
import sys

from pydub import AudioSegment

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Make sure we can import the package
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from audio_instruction.core.audio import download_youtube_audio
    from audio_instruction.core.browser_download import (
        REQUESTS_AVAILABLE,
        browser_download_audio,
        download_with_requests,
    )
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    sys.exit(1)


def test_download_methods(url):
    """Test different download methods with the given URL."""
    logger.info(f"Testing YouTube download methods with URL: {url}")
    
    # Method 1: Standard yt-dlp
    logger.info("\n--- Testing standard yt-dlp method ---")
    audio1 = download_youtube_audio(url)
    if audio1:
        logger.info("Standard yt-dlp method SUCCESS")
        logger.info(f"Audio length: {len(audio1)/1000:.2f} seconds")
    else:
        logger.error("Standard yt-dlp method FAILED")
    
    # Method 2: Browser download (which uses requests)
    logger.info("\n--- Testing browser download method ---")
    audio2 = browser_download_audio(url)
    if audio2:
        logger.info("Browser download method SUCCESS")
        logger.info(f"Audio length: {len(audio2)/1000:.2f} seconds")
    else:
        logger.error("Browser download method FAILED")
    
    # Method 3: Direct requests
    if REQUESTS_AVAILABLE:
        logger.info("\n--- Testing direct requests method ---")
        file_path = download_with_requests(url)
        if file_path and os.path.exists(file_path):
            logger.info(f"Direct requests method SUCCESS: {file_path}")
            logger.info(f"File size: {os.path.getsize(file_path)} bytes")
            
            # Clean up
            try:
                audio = AudioSegment.from_file(file_path, format="mp3")
                logger.info(f"Audio length: {len(audio)/1000:.2f} seconds")
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Error processing file: {e}")
        else:
            logger.error("Direct requests method FAILED")
    else:
        logger.warning("Requests library not available. Skipping direct requests test.")


def main():
    """Main function to run the tests."""
    parser = argparse.ArgumentParser(description="Test YouTube download functionality")
    parser.add_argument("url", type=str, 
                      help="YouTube URL to test (e.g., https://www.youtube.com/watch?v=YOUTUBE_ID)")
    args = parser.parse_args()
    
    test_download_methods(args.url)


if __name__ == "__main__":
    main() 