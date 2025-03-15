"""Audio processing utilities for workout instruction generation."""
import logging
import os
import random
import subprocess
import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Optional, Tuple

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

# Strategy registry for download methods
DOWNLOAD_STRATEGIES = {}

def download_strategy(fn: Callable) -> Callable:
    """Decorator to register download strategies."""
    DOWNLOAD_STRATEGIES[fn.__name__] = fn
    return fn

@download_strategy
def download_youtube_audio(url: str) -> Optional[AudioSegment]:
    """Download audio from YouTube URL using yt-dlp.
    
    Args:
        url: YouTube URL to download audio from
        
    Returns:
        AudioSegment if download successful, None otherwise
    """
    logging.info(f"Downloading audio from YouTube: {url}")
    tmp_filename = f"/tmp/{uuid.uuid4()}.%(ext)s"
    
    try:
        # More reliable options for yt-dlp
        cmd = [
            "yt-dlp",
            "--no-playlist",
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "128K",
            "--output", tmp_filename,
            "--force-ipv4",  # Force IPv4 to avoid some connectivity issues
            "--socket-timeout", "30",  # Increase timeout
            "--retries", "3",  # Retry 3 times
            "--user-agent", random.choice(BROWSER_USER_AGENTS),  # Random user-agent
            "--quiet",  # Don't show output
            url
        ]
        
        subprocess.run(cmd, check=True)
        
        # Find the downloaded file
        mp3_file = tmp_filename.replace("%(ext)s", "mp3")
        if os.path.exists(mp3_file):
            audio = AudioSegment.from_mp3(mp3_file)
            os.remove(mp3_file)  # Clean up
            return audio
            
    except Exception as e:
        logging.warning(f"Error downloading with yt-dlp: {e}")
    
    return None

@download_strategy
def download_with_requests(url: str, max_attempts: int = 3) -> Optional[AudioSegment]:
    """Download YouTube audio using requests.
    
    This is a more lightweight approach than browser automation.
    
    Args:
        url: YouTube URL to download from
        max_attempts: Maximum number of retry attempts
        
    Returns:
        AudioSegment if download successful, None otherwise
    """
    try:
        from urllib.parse import parse_qs, urlparse

        import requests
        
        attempts = 0
        while attempts < max_attempts:
            try:
                # Extract video ID
                parsed_url = urlparse(url)
                video_id = None
                
                if 'youtube.com' in parsed_url.netloc:
                    video_id = parse_qs(parsed_url.query).get('v', [None])[0]
                elif 'youtu.be' in parsed_url.netloc:
                    video_id = parsed_url.path.lstrip('/')
                
                if not video_id:
                    logging.error(f"Could not extract video ID from {url}")
                    return None
                
                # Use invidious API to get audio-only stream
                api_endpoints = [
                    "https://invidious.protokolla.fi/api/v1/videos/",
                    "https://invidious.slipfox.xyz/api/v1/videos/",
                    "https://invidio.xamh.de/api/v1/videos/",
                ]
                
                user_agent = random.choice(BROWSER_USER_AGENTS)
                headers = {
                    'User-Agent': user_agent,
                    'Accept': 'application/json',
                    'Referer': 'https://www.google.com/'
                }
                
                # Try each endpoint
                for endpoint in api_endpoints:
                    try:
                        api_url = f"{endpoint}{video_id}"
                        response = requests.get(api_url, headers=headers, timeout=10)
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            # Find audio stream (prefer lower quality for faster download)
                            audio_formats = [f for f in data.get('adaptiveFormats', []) 
                                            if f.get('type', '').startswith('audio/')]
                            
                            if audio_formats:
                                # Sort by bitrate (ascending)
                                audio_formats.sort(key=lambda x: x.get('bitrate', 0))
                                audio_url = audio_formats[0].get('url')
                                
                                if audio_url:
                                    # Download the audio
                                    audio_response = requests.get(audio_url, headers=headers, timeout=30)
                                    
                                    if audio_response.status_code == 200:
                                        # Save to temporary file
                                        tmp_file = f"/tmp/{uuid.uuid4()}.mp3"
                                        with open(tmp_file, 'wb') as f:
                                            f.write(audio_response.content)
                                            
                                        # Load with pydub
                                        audio = AudioSegment.from_mp3(tmp_file)
                                        os.remove(tmp_file)  # Clean up
                                        return audio
                    
                    except Exception as e:
                        logging.warning(f"Error with endpoint {endpoint}: {e}")
                        continue
                            
            except Exception as e:
                logging.warning(f"Attempt {attempts + 1} failed: {e}")
                
            attempts += 1
            time.sleep(2)  # Wait before retrying
                
    except ImportError:
        logging.warning("Requests library not available. Install with 'pip install requests'")
    except Exception as e:
        logging.warning(f"Error in download_with_requests: {e}")
        
    return None

def fetch_background_tracks(urls: List[str]) -> List[AudioSegment]:
    """Download background music from multiple YouTube URLs.
    
    Args:
        urls: List of YouTube URLs
        
    Returns:
        List of successfully downloaded AudioSegments
    """
    logging.info(f"Fetching {len(urls)} background tracks")
    
    # Define download strategies in order of preference
    strategies = [
        download_youtube_audio,
        download_with_requests,
        # Add more strategies here if needed
    ]
    
    results = []
    
    with ThreadPoolExecutor(max_workers=min(len(urls), 3)) as executor:
        future_to_url = {}
        
        for url in urls:
            future = executor.submit(_try_with_strategies, url, strategies)
            future_to_url[future] = url
            
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                audio = future.result()
                if audio:
                    results.append(audio)
                    logging.info(f"Successfully downloaded audio from {url}")
                else:
                    logging.warning(f"Failed to download audio from {url}")
            except Exception as e:
                logging.error(f"Error downloading {url}: {e}")
                
    return results

def _try_with_strategies(url: str, strategies: List[Callable]) -> Optional[AudioSegment]:
    """Try downloading with multiple strategies in sequence."""
    for strategy in strategies:
        logging.info(f"Trying download strategy: {strategy.__name__}")
        result = strategy(url)
        if result:
            return result
    return None

def adjust_loudness(audio: AudioSegment, target_lufs: float = -23.0) -> AudioSegment:
    """Adjust audio loudness to a target LUFS level.
    
    Args:
        audio: Audio segment to adjust
        target_lufs: Target loudness in LUFS (Loudness Units Full Scale)
        
    Returns:
        Loudness-adjusted audio
    """
    # Convert pydub audio to numpy array
    samples = np.array(audio.get_array_of_samples()).astype(np.float32)
    
    if audio.channels == 2:
        # Convert stereo to mono for measurement
        samples = samples.reshape((-1, 2))
        samples_mono = samples.mean(axis=1)
    else:
        samples_mono = samples
        
    # Measure current loudness
    meter = pyln.Meter(audio.frame_rate)
    current_loudness = meter.integrated_loudness(samples_mono / np.iinfo(audio.array_type).max)
    
    # Calculate gain needed
    gain_db = target_lufs - current_loudness
    
    # Apply gain
    return audio + gain_db

def loop_audio_continuous(audio: AudioSegment, target_duration_ms: int, crossfade_ms: int = 1000) -> AudioSegment:
    """Loop audio to reach a target duration with crossfade between loops.
    
    Args:
        audio: Audio to loop
        target_duration_ms: Target duration in milliseconds
        crossfade_ms: Crossfade duration in milliseconds
        
    Returns:
        Looped audio
    """
    if len(audio) >= target_duration_ms:
        return audio[:target_duration_ms]
        
    result = audio
    while len(result) < target_duration_ms:
        result = result.append(audio, crossfade=min(crossfade_ms, len(audio) // 2))
        
    return result[:target_duration_ms]

def merge_background_tracks(tracks: List[AudioSegment], duration_ms: int, crossfade_ms: int = 1000) -> AudioSegment:
    """Merge multiple background tracks into a single audio track.
    
    Args:
        tracks: List of audio tracks
        duration_ms: Target duration in milliseconds
        crossfade_ms: Crossfade duration in milliseconds
        
    Returns:
        Merged audio track
    """
    if not tracks:
        return AudioSegment.silent(duration=duration_ms)
        
    # If only one track, just loop it
    if len(tracks) == 1:
        return loop_audio_continuous(tracks[0], duration_ms, crossfade_ms)
        
    # Normalize loudness of all tracks
    normalized_tracks = [adjust_loudness(track) for track in tracks]
    
    # Calculate how to distribute the tracks
    segment_duration = duration_ms // len(normalized_tracks)
    
    # Create silent base
    result = AudioSegment.silent(duration=duration_ms)
    
    # Add each track at its position
    position = 0
    for track in normalized_tracks:
        # Loop the track to segment duration
        looped = loop_audio_continuous(track, segment_duration + crossfade_ms, crossfade_ms)
        
        # Overlay with crossfade
        if position == 0:
            result = looped.overlay(result)
        else:
            # Apply crossfade with previous segment
            result = result[:position].append(looped, crossfade=crossfade_ms)
            
        position += segment_duration
        
        # Break if we've filled the duration
        if position >= duration_ms:
            break
            
    return result[:duration_ms] 