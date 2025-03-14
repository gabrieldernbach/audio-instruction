#!/usr/bin/env python3
"""
Test script for YouTube download functionality specifically in Docker environments.
This script tests yt-dlp's ability to download without browser cookies.
"""

import argparse
import logging
import os
import subprocess
import sys
import time
import uuid
from typing import Optional

from pydub import AudioSegment

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Make sure we can import the package
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from audio_instruction.core.audio import (
        BROWSER_USER_AGENTS,
        _try_fallback_download,
        download_youtube_audio,
    )
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    sys.exit(1)

def test_direct_yt_dlp(url: str) -> bool:
    """Test yt-dlp directly without any cookies."""
    logger.info(f"Testing yt-dlp without cookies for URL: {url}")
    
    # Ensure we're in Docker or a similar environment without browser cookies
    if os.path.exists(os.path.expanduser("~/.config/google-chrome")) or \
       os.path.exists(os.path.expanduser("~/.mozilla/firefox")):
        logger.warning("This test should be run in Docker where browser cookies aren't available")
    
    # Test primary download method
    start_time = time.time()
    audio = download_youtube_audio(url)
    end_time = time.time()
    
    if audio:
        logger.info("✅ Primary download method SUCCESS!")
        logger.info(f"Audio length: {len(audio)/1000:.2f} seconds")
        logger.info(f"Download time: {end_time - start_time:.2f} seconds")
    else:
        logger.error("❌ Primary download method FAILED")
    
    # Test fallback method directly
    logger.info("\n--- Testing fallback methods directly ---")
    start_time = time.time()
    audio = _try_fallback_download(url)
    end_time = time.time()
    
    if audio:
        logger.info("✅ Fallback method SUCCESS!")
        logger.info(f"Audio length: {len(audio)/1000:.2f} seconds")
        logger.info(f"Download time: {end_time - start_time:.2f} seconds")
    else:
        logger.error("❌ Fallback method FAILED")
    
    # Check Docker environment
    logger.info("\n--- Docker Environment Information ---")
    if os.path.exists("/app"):
        logger.info("✅ Running in Docker container (/app exists)")
    else:
        logger.info("❌ Not running in Docker container (/app doesn't exist)")
    
    # Check if browser cookie paths exist
    cookie_paths = [
        "~/.config/google-chrome",
        "~/.mozilla/firefox",
        "~/.config/microsoft-edge"
    ]
    
    for path in cookie_paths:
        if os.path.exists(os.path.expanduser(path)):
            logger.warning(f"⚠️ Browser cookie path exists: {path}")
        else:
            logger.info(f"✅ No browser cookies at: {path}")
    
    return audio is not None

def test_direct_download_method(url: str, use_format: str = "bestaudio", quality: str = "128K") -> Optional[AudioSegment]:
    """Test a specific yt-dlp download configuration.
    
    Args:
        url: YouTube URL to download from
        use_format: Format string for yt-dlp
        quality: Audio quality to use
        
    Returns:
        AudioSegment if successful, None otherwise
    """
    # Ensure tmp directory exists
    os.makedirs("tmp", exist_ok=True)
    
    # Use /app/tmp if in Docker, otherwise use local tmp directory
    tmp_dir = "/app/tmp" if os.path.exists("/app") else "tmp"
    tmp_filename = os.path.join(tmp_dir, f"{uuid.uuid4()}.mp3")
    
    # Select a random user agent
    user_agent = BROWSER_USER_AGENTS[0]
    
    start_time = time.time()
    logger.info(f"Testing direct download with format={use_format}, quality={quality}")
    
    try:
        cmd = [
            "yt-dlp",
            "--user-agent", user_agent,
            "--format", use_format,
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", quality,
            "--force-ipv4",
            "--no-check-certificates",
            "--ignore-errors",
            "--no-warnings",
            "-o", tmp_filename,
            url
        ]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        process = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Log the output and error
        logger.debug(f"STDOUT: {process.stdout}")
        if process.stderr:
            logger.debug(f"STDERR: {process.stderr}")
        
        if process.returncode != 0:
            logger.error(f"Command failed with return code {process.returncode}")
            if os.path.exists(tmp_filename):
                os.remove(tmp_filename)
            return None
        
        # Check if the file exists and has content
        if not os.path.exists(tmp_filename) or os.path.getsize(tmp_filename) == 0:
            logger.error(f"Output file {tmp_filename} was not created or is empty")
            if os.path.exists(tmp_filename):
                os.remove(tmp_filename)
            return None
        
        # Log success
        end_time = time.time()
        file_size = os.path.getsize(tmp_filename)
        logger.info(f"✅ Download succeeded! File size: {file_size} bytes, Time: {end_time - start_time:.2f}s")
        
        # Load and return the audio
        audio = AudioSegment.from_file(tmp_filename, format="mp3")
        os.remove(tmp_filename)
        return audio
        
    except Exception as e:
        logger.error(f"Error during direct download: {e}")
        if os.path.exists(tmp_filename):
            try:
                os.remove(tmp_filename)
            except:
                pass
        return None

def test_download_variations(url: str) -> bool:
    """Test different variations of download parameters."""
    logger.info("\n=== Testing Different Download Configurations ===")
    
    # Test configurations
    configs = [
        {"name": "Best audio quality", "format": "bestaudio", "quality": "192K"},
        {"name": "Medium audio quality", "format": "bestaudio", "quality": "128K"},
        {"name": "Lower audio quality", "format": "worstaudio", "quality": "64K"},
        {"name": "Video (with audio)", "format": "18", "quality": "128K"},
        {"name": "Specific format", "format": "bestaudio[ext=m4a]/bestaudio", "quality": "128K"},
    ]
    
    success_count = 0
    total_count = len(configs)
    
    for config in configs:
        logger.info(f"\n--- Testing: {config['name']} ---")
        audio = test_direct_download_method(url, config["format"], config["quality"])
        
        if audio:
            success_count += 1
            logger.info(f"✅ {config['name']} SUCCESS! Audio length: {len(audio)/1000:.2f} seconds")
        else:
            logger.error(f"❌ {config['name']} FAILED")
    
    # Test simplified command with minimal options
    logger.info("\n--- Testing: Minimal options ---")
    
    try:
        # Use /app/tmp if in Docker, otherwise use local tmp directory
        tmp_dir = "/app/tmp" if os.path.exists("/app") else "tmp"
        tmp_filename = os.path.join(tmp_dir, f"{uuid.uuid4()}.mp3")
        
        cmd = [
            "yt-dlp",
            "-x",  # Extract audio
            "--audio-format", "mp3",
            "-o", tmp_filename,
            url
        ]
        
        logger.info(f"Running minimal command: {' '.join(cmd)}")
        process = subprocess.run(cmd, check=False)
        
        if process.returncode == 0 and os.path.exists(tmp_filename) and os.path.getsize(tmp_filename) > 0:
            audio = AudioSegment.from_file(tmp_filename, format="mp3")
            logger.info(f"✅ Minimal options SUCCESS! Audio length: {len(audio)/1000:.2f} seconds")
            os.remove(tmp_filename)
            success_count += 1
        else:
            logger.error("❌ Minimal options FAILED")
        
    except Exception as e:
        logger.error(f"Error during minimal options test: {e}")
    
    # Add minimal options to total count
    total_count += 1
    
    logger.info(f"\n=== Download Configuration Test Results ===")
    logger.info(f"Success rate: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    return success_count > 0

def main():
    """Main function to run the test."""
    parser = argparse.ArgumentParser(description="Test YouTube download without cookies")
    parser.add_argument("url", type=str, help="YouTube URL to test")
    parser.add_argument("--repeat", type=int, default=1, help="Number of times to repeat the test")
    parser.add_argument("--variations", action="store_true", help="Test different download configurations")
    args = parser.parse_args()
    
    success_count = 0
    total_tests = args.repeat
    
    for i in range(args.repeat):
        if args.repeat > 1:
            logger.info(f"\n=== Test run {i+1}/{args.repeat} ===")
        
        if args.variations:
            if test_download_variations(args.url):
                success_count += 1
        else:
            if test_direct_yt_dlp(args.url):
                success_count += 1
    
    logger.info(f"\n=== Final Results ===")
    logger.info(f"Success rate: {success_count}/{total_tests} ({success_count/total_tests*100:.1f}%)")
    
    if success_count == 0:
        logger.error("All tests failed! The yt-dlp configuration may need adjustment.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 