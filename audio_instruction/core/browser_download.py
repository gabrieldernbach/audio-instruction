"""Alternative methods for downloading audio from YouTube."""
import logging
import os
import random
import subprocess
import time
import uuid
from typing import List, Optional

from pydub import AudioSegment

# Common browser user agents
BROWSER_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]


def download_with_requests(url: str, max_attempts: int = 3) -> Optional[AudioSegment]:
    """Download YouTube audio using requests.
    
    This is a more lightweight approach than browser automation.
    
    Args:
        url: YouTube URL to download from
        max_attempts: Maximum number of retry attempts
        
    Returns:
        AudioSegment object if download successful, None otherwise
    """
    logging.info(f"Attempting to download {url} using requests library")
    
    # Make temporary file
    os.makedirs("tmp", exist_ok=True)
    output_path = os.path.join("/app/tmp" if os.path.exists("/app") else "tmp", f"{uuid.uuid4()}.mp3")
    
    for attempt in range(max_attempts):
        try:
            # Randomize sleep duration between attempts for less predictable behavior
            sleep_duration = random.uniform(3, 5) if attempt > 0 else 0
            if sleep_duration > 0:
                logging.info(f"Waiting {sleep_duration:.2f} seconds before next attempt")
                time.sleep(sleep_duration)
            
            # Select a random user agent
            user_agent = random.choice(BROWSER_USER_AGENTS)
            
            # Setup headers to look like a real browser
            headers = {
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
            }
            
            # Vary the sleep intervals to appear more human-like
            sleep_interval = random.uniform(3, 5)
            max_sleep_interval = random.uniform(8, 15)
            
            logging.info(f"Running download command with attempt {attempt+1}/{max_attempts}")
            
            # Use yt-dlp with the requests headers to appear more like a browser request
            cmd = [
                "yt-dlp",
                "--user-agent", user_agent,
                "--referer", "https://www.youtube.com/",
                "--add-header", f"Accept:{headers['Accept']}",
                "--add-header", f"Accept-Language:{headers['Accept-Language']}",
                "--add-header", f"DNT:{headers['DNT']}",
                "--add-header", f"Connection:{headers['Connection']}",
                "--add-header", f"Upgrade-Insecure-Requests:{headers['Upgrade-Insecure-Requests']}",
                "--add-header", f"Sec-Fetch-Dest:{headers['Sec-Fetch-Dest']}",
                "--add-header", f"Sec-Fetch-Mode:{headers['Sec-Fetch-Mode']}",
                "--add-header", f"Sec-Fetch-Site:{headers['Sec-Fetch-Site']}",
                "--add-header", f"Sec-Fetch-User:{headers['Sec-Fetch-User']}",
                "--add-header", f"Cache-Control:{headers['Cache-Control']}",
                "--geo-bypass",
                "--prefer-insecure",
                "--no-check-certificates",
                "--socket-timeout", "30",
                "--format", "bestaudio[ext=m4a]/bestaudio",
                "--extract-audio",
                "--audio-format", "mp3",
                "--force-ipv4",
                "--sleep-interval", f"{sleep_interval}",
                "--max-sleep-interval", f"{max_sleep_interval}",
                "--extractor-args", "youtube:player_client=android,web",
                "--mark-watched",
                "--no-warnings",
                "--cookies-from-browser", "chrome" if os.path.exists(os.path.expanduser("~/.config/google-chrome")) else "firefox" if os.path.exists(os.path.expanduser("~/.mozilla/firefox")) else "edge",
                "-o", output_path,
                url
            ]
            
            # Execute the command
            process = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if process.returncode != 0:
                logging.error(f"Download attempt {attempt+1} failed: {process}")
                logging.error(f"STDOUT: {process.stdout}")
                logging.error(f"STDERR: {process.stderr}")
                
                # Wait longer between retries
                wait_time = random.uniform(5, 15) * (attempt + 1)
                logging.info(f"Waiting {wait_time:.2f} seconds before next attempt")
                time.sleep(wait_time)
                continue
            
            # Check if file exists and has content
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logging.info(f"Download successful! File saved to {output_path}")
                audio = AudioSegment.from_file(output_path, format="mp3")
                os.remove(output_path)  # Clean up the temporary file
                return audio
        
        except Exception as e:
            logging.error(f"Download attempt {attempt+1} failed with exception: {e}")
            
            # Wait before retry
            wait_time = random.uniform(5, 15) * (attempt + 1)
            logging.info(f"Waiting {wait_time:.2f} seconds before next attempt")
            time.sleep(wait_time)
    
    logging.error(f"All {max_attempts} download attempts failed")
    return None

def fetch_background_tracks_browser(urls: List[str]) -> List[AudioSegment]:
    """Fetch background tracks using alternative download methods.
    
    Args:
        urls: List of YouTube URLs to download audio from
        
    Returns:
        List of successfully downloaded AudioSegment objects
    """
    
    logging.info(f"Attempting to download {len(urls)} background tracks using alternative methods")
    
    tracks = []
    for i, url in enumerate(urls):
        # Add delays between downloads
        if i > 0:
            delay = random.uniform(5, 10) + (i * 2)  # Increasing delay for each download
            logging.info(f"Waiting {delay:.2f} seconds before downloading next track")
            time.sleep(delay)
        
        # Try to download the track
        track = download_with_requests(url)
        if track:
            tracks.append(track)
            logging.info(f"Successfully downloaded track {i+1}/{len(urls)} using alternative method")
        else:
            logging.warning(f"Failed to download track {i+1}/{len(urls)} using alternative method")
    
    logging.info(f"Downloaded {len(tracks)}/{len(urls)} tracks successfully using alternative methods")
    return tracks 