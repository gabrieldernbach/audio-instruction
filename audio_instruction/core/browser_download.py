"""Alternative methods for downloading audio from YouTube."""
import json
import logging
import os
import random
import subprocess
import time
import uuid
from typing import Any, Dict, List, Optional

from pydub import AudioSegment

# Common browser user agents
BROWSER_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

# Define a flag to check if requests is installed
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logging.warning("Requests library not available. Alternative download methods will be disabled.")

# Check for pytube availability as another fallback
try:
    import pytube
    PYTUBE_AVAILABLE = True
except ImportError:
    PYTUBE_AVAILABLE = False
    logging.warning("Pytube library not available. Pytube download method will be disabled.")

# Flag for selenium availability (for compatibility)
SELENIUM_AVAILABLE = False


def download_with_requests(url: str, max_attempts: int = 3) -> Optional[str]:
    """Download YouTube audio using requests.
    
    This is a more lightweight approach than browser automation.
    
    Args:
        url: YouTube URL to download from
        max_attempts: Maximum number of retry attempts
        
    Returns:
        Path to downloaded file or None if failed
    """
    if not REQUESTS_AVAILABLE:
        logging.error("Requests library not available. Cannot use this download method.")
        return None
    
    logging.info(f"Attempting to download {url} using requests library")
    
    # Create tmp directory
    tmp_dir = os.path.join(os.getcwd(), "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    
    # Create a unique filename
    output_file = os.path.join(tmp_dir, f"{uuid.uuid4()}.mp3")
    
    # Here we're using yt-dlp but with enhanced options to bypass restrictions
    for attempt in range(max_attempts):
        try:
            # Select a random user agent
            user_agent = random.choice(BROWSER_USER_AGENTS)
            
            # Define headers to mimic a browser
            headers = [
                "--user-agent", user_agent,
                "--referer", "https://www.youtube.com/",
            ]
            
            # Fix headers to avoid whitespace issues
            headers_without_spaces = [
                "--add-header", "Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "--add-header", "Accept-Language:en-US,en;q=0.5",
                "--add-header", "DNT:1",
                "--add-header", "Connection:keep-alive",
                "--add-header", "Upgrade-Insecure-Requests:1",
                "--add-header", "Sec-Fetch-Dest:document",
                "--add-header", "Sec-Fetch-Mode:navigate",
                "--add-header", "Sec-Fetch-Site:none",
                "--add-header", "Sec-Fetch-User:?1",
                "--add-header", "Cache-Control:max-age=0",
            ]
            
            # Enhanced options to bypass YouTube's anti-scraping measures
            options = [
                "--geo-bypass",
                "--prefer-insecure",
                "--socket-timeout", "30",  # Longer socket timeout
                "--format", "bestaudio",  # Get best audio quality
                "--sleep-interval", str(random.randint(3, 7)),  # Longer random delay between requests
                "--max-sleep-interval", "10",
                # Use specific extractor settings for YouTube
                "--extractor-args", "youtube:player_client=android",
            ]
            
            # Run yt-dlp with all our enhanced settings - more minimal approach
            cmd = ["yt-dlp"] + headers + headers_without_spaces + options + ["-x", "--audio-format", "mp3", "--audio-quality", "192K", "-o", output_file, url]
            
            logging.info(f"Running download command with attempt {attempt+1}/{max_attempts}")
            
            process = subprocess.run(
                cmd, check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                logging.info(f"Successfully downloaded to {output_file} with size {os.path.getsize(output_file)}")
                return output_file
            else:
                logging.warning(f"Output file doesn't exist or is empty after download attempt {attempt+1}")
                
        except subprocess.CalledProcessError as e:
            logging.error(f"Download attempt {attempt+1} failed: {e}")
            logging.error(f"STDOUT: {e.stdout}")
            logging.error(f"STDERR: {e.stderr}")
            
            # If we have more attempts, wait before retrying
            if attempt < max_attempts - 1:
                wait_time = random.uniform(5, 10) * (attempt + 1)  # Increasing delay for each retry
                logging.info(f"Waiting {wait_time:.2f} seconds before next attempt")
                time.sleep(wait_time)
        except Exception as e:
            logging.error(f"Unexpected error in download attempt {attempt+1}: {e}")
            
            # If we have more attempts, wait before retrying
            if attempt < max_attempts - 1:
                wait_time = random.uniform(5, 10) * (attempt + 1)
                logging.info(f"Waiting {wait_time:.2f} seconds before next attempt")
                time.sleep(wait_time)
    
    logging.error(f"All {max_attempts} download attempts failed")
    return None


def download_with_pytube(url: str, max_attempts: int = 3) -> Optional[str]:
    """Download YouTube audio using pytube.
    
    This is a lightweight alternative that doesn't rely on external tools.
    
    Args:
        url: YouTube URL to download from
        max_attempts: Maximum number of retry attempts
        
    Returns:
        Path to downloaded file or None if failed
    """
    if not PYTUBE_AVAILABLE:
        logging.error("Pytube library not available. Cannot use this download method.")
        return None
    
    logging.info(f"Attempting to download {url} using pytube library")
    
    # Create tmp directory
    tmp_dir = os.path.join(os.getcwd(), "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    
    # Create a unique filename
    output_file = os.path.join(tmp_dir, f"{uuid.uuid4()}.mp3")
    
    for attempt in range(max_attempts):
        try:
            # Create YouTube object
            # Note: pytube uses its own user-agent logic, we don't need to set it manually
            yt = pytube.YouTube(url)
            
            # Get audio stream
            audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            
            if not audio_stream:
                logging.error("No audio stream found")
                if attempt < max_attempts - 1:
                    wait_time = random.uniform(5, 10)
                    logging.info(f"Waiting {wait_time:.2f} seconds before next attempt")
                    time.sleep(wait_time)
                continue
            
            # Download to a temporary file
            temp_file = audio_stream.download(output_path=tmp_dir, filename=f"temp_{uuid.uuid4()}")
            
            logging.info(f"Downloaded temp file to {temp_file}")
            
            # Convert to MP3 using ffmpeg
            subprocess.run([
                "ffmpeg", "-y", "-i", temp_file, "-vn", "-ar", "44100", "-ac", "2", 
                "-b:a", "192k", output_file
            ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            logging.info(f"Converted to MP3 at {output_file}")
            
            # Clean up the temporary file
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            # Check if the output file exists and has content
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                logging.info(f"Successfully downloaded to {output_file} with size {os.path.getsize(output_file)}")
                return output_file
            else:
                logging.warning(f"Output file doesn't exist or is empty after download attempt {attempt+1}")
        
        except Exception as e:
            logging.error(f"Pytube download attempt {attempt+1} failed: {e}")
            
            # If we have more attempts, wait before retrying
            if attempt < max_attempts - 1:
                wait_time = random.uniform(5, 10) * (attempt + 1)
                logging.info(f"Waiting {wait_time:.2f} seconds before next attempt")
                time.sleep(wait_time)
                
                # Clean up any partial files
                if os.path.exists(output_file):
                    os.remove(output_file)
    
    logging.error(f"All {max_attempts} pytube download attempts failed")
    return None


def browser_download_audio(url: str) -> Optional[AudioSegment]:
    """Download audio from YouTube using alternate download methods.
    
    This is a fallback when regular yt-dlp fails.
    
    Args:
        url: YouTube URL to download audio from
        
    Returns:
        AudioSegment containing the downloaded audio or None if download failed
    """
    # First try with requests method
    file_path = download_with_requests(url)
    
    # If requests method fails, try pytube as another fallback
    if (not file_path or not os.path.exists(file_path)) and PYTUBE_AVAILABLE:
        logging.info("Requests method failed, trying pytube method")
        file_path = download_with_pytube(url)
    
    if not file_path or not os.path.exists(file_path):
        logging.error(f"Failed to download audio or file doesn't exist: {file_path}")
        return None
    
    try:
        # Load the downloaded audio file
        audio = AudioSegment.from_file(file_path, format="mp3")
        
        # Clean up the file
        if os.path.exists(file_path):
            os.remove(file_path)
            
        return audio
    except Exception as e:
        logging.error(f"Error processing downloaded audio: {e}")
        # Clean up in case of error
        if os.path.exists(file_path):
            os.remove(file_path)
        return None


def fetch_background_tracks_browser(urls: List[str]) -> List[AudioSegment]:
    """Fetch background tracks using alternative download methods.
    
    Args:
        urls: List of YouTube URLs to download audio from
        
    Returns:
        List of successfully downloaded AudioSegment objects
    """
    if not REQUESTS_AVAILABLE:
        logging.error("Required libraries not available. Cannot use alternative download methods.")
        return []
    
    logging.info(f"Attempting to download {len(urls)} background tracks using alternative methods")
    
    tracks = []
    for i, url in enumerate(urls):
        # Add delays between downloads
        if i > 0:
            delay = random.uniform(5, 10) + (i * 2)  # Increasing delay for each download
            logging.info(f"Waiting {delay:.2f} seconds before downloading next track")
            time.sleep(delay)
        
        # Try to download the track
        track = browser_download_audio(url)
        if track:
            tracks.append(track)
            logging.info(f"Successfully downloaded track {i+1}/{len(urls)} using alternative method")
        else:
            logging.warning(f"Failed to download track {i+1}/{len(urls)} using alternative method")
    
    logging.info(f"Downloaded {len(tracks)}/{len(urls)} tracks successfully using alternative methods")
    return tracks 