"""Audio processing utilities for workout instruction generation."""
import logging
import os
import subprocess
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

import numpy as np
import pyloudnorm as pyln
from pydub import AudioSegment


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
        tmp_filename = os.path.join("tmp", f"{uuid.uuid4()}.mp3")
        
        subprocess.run([
            "yt-dlp", "-x", "--audio-format", "mp3", 
            "--audio-quality", "192K", "-o", tmp_filename, url
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        audio = AudioSegment.from_file(tmp_filename, format="mp3")
        os.remove(tmp_filename)
        return audio
    except Exception as e:
        logging.error(f"Failed to download audio from {url}. Error: {e}")
        return None


def fetch_background_tracks(urls: List[str]) -> List[AudioSegment]:
    """Concurrently download background tracks from YouTube URLs.
    
    Args:
        urls: List of YouTube URLs to download audio from
        
    Returns:
        List of successfully downloaded AudioSegment objects
    """
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {executor.submit(download_youtube_audio, url): url for url in urls}
        return [
            track for future in as_completed(future_map)
            if (track := future.result()) is not None
        ]


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