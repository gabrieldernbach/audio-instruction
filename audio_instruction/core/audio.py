"""Audio processing utilities for workout instruction generation."""
import logging
import os
import random
import subprocess
import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

import numpy as np
import pyloudnorm as pyln
from pydub import AudioSegment

# Common browser user agents for better mimicking real browsers
BROWSER_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]


def download_youtube_audio(url: str) -> Optional[AudioSegment]:
    """Download audio from YouTube URL.
    
    Args:
        url: YouTube URL to download audio from
        
    Returns:
        AudioSegment containing the downloaded audio or None if download failed
    """
    try:
        # Ensure tmp directory exists
        os.makedirs("tmp", exist_ok=True)
        
        # Use /app/tmp if in Docker, otherwise use local tmp directory
        is_docker = os.path.exists("/app")
        tmp_dir = "/app/tmp" if is_docker else "tmp"
        tmp_filename = os.path.join(tmp_dir, f"{uuid.uuid4()}.mp3")
        
        # Select a random user agent
        user_agent = random.choice(BROWSER_USER_AGENTS)
        
        logging.info(f"Downloading audio from {url} to {tmp_filename}")
        logging.info(f"Using user agent: {user_agent}")
        
        # Detect possible browser cookie locations based on OS
        # Skip browser cookies if we're in Docker as they won't exist
        browser_cookies_args = []
        if not is_docker:
            browser_cookies = "chrome"
            if os.name == "posix":  # Linux/macOS
                if not os.path.exists(os.path.expanduser("~/.config/google-chrome")):
                    if os.path.exists(os.path.expanduser("~/.mozilla/firefox")):
                        browser_cookies = "firefox"
                    elif os.path.exists(os.path.expanduser("~/.config/chromium")):
                        browser_cookies = "chromium"
            browser_cookies_args = ['--cookies-from-browser', browser_cookies]
        
        # Enhanced options to better handle YouTube's anti-scraping measures
        yt_dlp_args = [
            "yt-dlp", 
            "-v", 
            "--user-agent", user_agent,
            "--referer", "https://www.youtube.com/",
            "--geo-bypass",  # Try to bypass geo-restrictions
            "--no-check-certificates",  # Skip HTTPS certificate validation
            "--prefer-insecure",  # Use HTTP instead of HTTPS when available
            "--extractor-args", "youtube:player_client=android,web",  # Try different client types
            "--mark-watched",  # Mark video as watched (more natural behavior)
            "--socket-timeout", "60",  # Increase timeouts to handle slow connections
            "--retries", "10",  # Increase retries
            "--force-ipv4",  # Force IPv4 to avoid IPv6 issues
            "--extract-audio", 
            "--audio-format", "mp3", 
            "--audio-quality", "192K", 
            "-o", tmp_filename, 
            url
        ]
        
        # Only add browser cookies if not in Docker
        if browser_cookies_args and not is_docker:
            yt_dlp_args[7:7] = browser_cookies_args
        
        process = subprocess.run(yt_dlp_args, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Log the output for debugging
        logging.info(f"yt-dlp stdout: {process.stdout}")
        if process.stderr:
            logging.warning(f"yt-dlp stderr: {process.stderr}")
        
        # Check if the process was successful
        if process.returncode != 0:
            logging.error(f"yt-dlp failed with return code {process.returncode}")
            # Try a fallback with different options if the primary approach fails
            return _try_fallback_download(url, tmp_filename)
        
        # Check if the file exists
        if not os.path.exists(tmp_filename):
            logging.error(f"Output file {tmp_filename} was not created")
            return _try_fallback_download(url, tmp_filename)
        
        # Check if the file has content
        if os.path.getsize(tmp_filename) == 0:
            logging.error(f"Output file {tmp_filename} is empty")
            os.remove(tmp_filename)
            return _try_fallback_download(url, tmp_filename)
        
        logging.info(f"Successfully downloaded audio to {tmp_filename} (size: {os.path.getsize(tmp_filename)} bytes)")
        
        # Load the audio file
        audio = AudioSegment.from_file(tmp_filename, format="mp3")
        os.remove(tmp_filename)
        return audio
    except Exception as e:
        logging.error(f"Failed to download audio from {url}. Error: {e}")
        return _try_fallback_download(url, None)


def _try_fallback_download(url: str, tmp_filename: Optional[str] = None) -> Optional[AudioSegment]:
    """Try alternative download methods when the primary method fails.
    
    Args:
        url: YouTube URL to download audio from
        tmp_filename: Existing temp filename to use, or None to generate a new one
        
    Returns:
        AudioSegment containing the downloaded audio or None if all download attempts fail
    """
    logging.info(f"Trying fallback download methods for {url}")
    
    # Use /app/tmp if in Docker, otherwise use local tmp directory
    is_docker = os.path.exists("/app")
    tmp_dir = "/app/tmp" if is_docker else "tmp"
    
    if tmp_filename is None:
        tmp_filename = os.path.join(tmp_dir, f"{uuid.uuid4()}.mp3")
    
    try:
        # Fallback Method 1: Try with different format settings
        fallback_args = [
            "yt-dlp",
            "--user-agent", random.choice(BROWSER_USER_AGENTS),
            "--format", "bestaudio",  # Just get the best audio format available
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "128K",  # Lower quality may be more reliable
            "--force-ipv4",
            "--quiet",
            "--no-warnings",
            "--no-check-certificates",
            "--ignore-errors",
            "-o", tmp_filename,
            url
        ]
        
        # In Docker, use optimized settings known to work in containerized environments
        if is_docker:
            fallback_args = [
                "yt-dlp",
                "--format", "bestaudio",
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", "128K",
                "--force-ipv4",
                "--no-check-certificates",
                "--ignore-errors",
                "--no-warnings",
                "-o", tmp_filename,
                url
            ]
        
        process = subprocess.run(fallback_args, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if process.returncode == 0 and os.path.exists(tmp_filename) and os.path.getsize(tmp_filename) > 0:
            logging.info(f"Fallback method 1 succeeded. File size: {os.path.getsize(tmp_filename)} bytes")
            audio = AudioSegment.from_file(tmp_filename, format="mp3")
            os.remove(tmp_filename)
            return audio
            
        # Fallback Method 2: Simple method with minimal options
        logging.info("Trying simple download as second fallback")
        simple_cmd = [
            "yt-dlp",
            "--format", "bestaudio",
            "--extract-audio",
            "--audio-format", "mp3",
            "--ignore-errors",
            "--no-warnings",
            "--no-check-certificates",
            "--force-ipv4",
            "-o", tmp_filename,
            url
        ]
        
        process = subprocess.run(simple_cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if process.returncode == 0 and os.path.exists(tmp_filename) and os.path.getsize(tmp_filename) > 0:
            logging.info(f"Simple fallback succeeded. File size: {os.path.getsize(tmp_filename)} bytes")
            audio = AudioSegment.from_file(tmp_filename, format="mp3")
            os.remove(tmp_filename)
            return audio
        
        # Final fallback: Try different yt-dlp flags
        logging.info("Trying last resort download method")
        last_resort = [
            "yt-dlp",
            "-f", "worstaudio/worst",  # Try the worst quality (more likely to work)
            "--extract-audio",
            "--audio-format", "mp3",
            "--ignore-errors",
            "--no-check-certificates",
            "--force-ipv4",
            "-o", tmp_filename,
            url
        ]
        
        process = subprocess.run(last_resort, check=False)
        
        if os.path.exists(tmp_filename) and os.path.getsize(tmp_filename) > 0:
            logging.info(f"Last resort download succeeded. File size: {os.path.getsize(tmp_filename)} bytes")
            audio = AudioSegment.from_file(tmp_filename, format="mp3")
            os.remove(tmp_filename)
            return audio
            
    except Exception as e:
        logging.error(f"All fallback methods failed: {e}")
        if os.path.exists(tmp_filename):
            try:
                os.remove(tmp_filename)
            except:
                pass
    
    # If we reach here, all download methods have failed
    logging.error("All download methods failed for URL: " + url)
    return None


def fetch_background_tracks(urls: List[str]) -> List[AudioSegment]:
    """Fetch background tracks with rate limiting and random delays.
    
    Args:
        urls: List of YouTube URLs to download audio from
        
    Returns:
        List of successfully downloaded AudioSegment objects
    """
    logging.info(f"Attempting to download {len(urls)} background tracks")
    
    tracks = []
    for i, url in enumerate(urls):
        # Add a random delay between 2-7 seconds to appear more human-like
        if i > 0:  # Don't delay before the first download
            delay = random.uniform(2, 7)
            logging.info(f"Waiting {delay:.2f} seconds before downloading next track")
            time.sleep(delay)
        
        try:
            # Try to download the track
            track = download_youtube_audio(url)
            if track:
                tracks.append(track)
                logging.info(f"Successfully downloaded track {i+1}/{len(urls)}")
            else:
                logging.warning(f"Failed to download track {i+1}/{len(urls)}")
        except Exception as e:
            logging.error(f"Error downloading track {i+1}/{len(urls)}: {e}")
    
    logging.info(f"Downloaded {len(tracks)}/{len(urls)} tracks successfully")
    return tracks


def adjust_loudness(audio: AudioSegment, target_lufs: float = -23.0) -> AudioSegment:
    """Normalize audio to target LUFS (Loudness Units relative to Full Scale).
    
    Args:
        audio: The audio segment to adjust
        target_lufs: Target loudness in LUFS (default: -23.0, EBU R128 standard)
        
    Returns:
        Loudness-adjusted AudioSegment
    """
    samples = np.array(audio.get_array_of_samples())
    if audio.channels > 1:
        samples = samples.reshape((-1, audio.channels))
    
    if np.max(np.abs(samples)) == 0:
        # Empty or silent audio, return as is
        return audio
        
    float_samples = samples.astype(np.float32) / float(2 ** (8 * audio.sample_width - 1))
    
    try:
        meter = pyln.Meter(audio.frame_rate)
        current_lufs = meter.integrated_loudness(float_samples)
        return audio.apply_gain(target_lufs - current_lufs)
    except Exception as e:
        logging.warning(f"Loudness adjustment failed: {e}")
        return audio


def loop_audio_continuous(audio: AudioSegment, target_duration_ms: int, crossfade_ms: int = 1000) -> AudioSegment:
    """Loop audio with crossfade until target duration is reached.
    
    Args:
        audio: The audio segment to loop
        target_duration_ms: Target duration in milliseconds
        crossfade_ms: Duration of crossfade in milliseconds
        
    Returns:
        Looped AudioSegment with the specified duration
    """
    if len(audio) >= target_duration_ms:
        return audio[:target_duration_ms]
        
    result = audio
    while len(result) < target_duration_ms:
        result = result.append(audio, crossfade=crossfade_ms)
    return result[:target_duration_ms]


def merge_background_tracks(tracks: List[AudioSegment], duration_ms: int, crossfade_ms: int = 1000) -> AudioSegment:
    """Merge and loop background tracks to create a seamless background.
    
    Args:
        tracks: List of audio segments to merge
        duration_ms: Target duration in milliseconds
        crossfade_ms: Duration of crossfade between tracks in milliseconds
        
    Returns:
        Merged and looped AudioSegment with the specified duration
    """
    if not tracks:
        return AudioSegment.silent(duration=duration_ms)
        
    merged = tracks[0]
    for track in tracks[1:]:
        merged = merged.append(track, crossfade=crossfade_ms)
        
    return loop_audio_continuous(merged, duration_ms, crossfade_ms) 