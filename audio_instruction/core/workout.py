"""Workout guide generation functionality."""
import io
from typing import List, Optional, Tuple

from pydub import AudioSegment

from audio_instruction.core.audio import (
    adjust_loudness,
    fetch_background_tracks,
    merge_background_tracks,
)
from audio_instruction.core.tts import build_instruction_audio


def assemble_workout_audio(instructions: List[Tuple[str, int]], lang: str = "en") -> AudioSegment:
    """Create full workout audio from instructions.
    
    Args:
        instructions: List of (instruction_text, duration_in_seconds) tuples
        lang: Language code for TTS
        
    Returns:
        AudioSegment containing the full workout guide audio
    """
    # Create a list of audio segments for each instruction
    audio_segments = [
        build_instruction_audio(text, duration, lang)
        for text, duration in instructions
    ]
    
    # Join the segments together
    combined_audio = AudioSegment.empty()
    for segment in audio_segments:
        combined_audio += segment
    
    # Adjust loudness
    return adjust_loudness(combined_audio, target_lufs=-23.0)


def integrate_continuous_background(guide_audio: AudioSegment, background_urls: List[str]) -> AudioSegment:
    """Add background music to guide audio.
    
    Args:
        guide_audio: The guide audio to add background music to
        background_urls: List of YouTube URLs for background music
        
    Returns:
        AudioSegment with guide audio and background music
    """
    bg_tracks = fetch_background_tracks(background_urls)
    if not bg_tracks:
        return guide_audio
        
    # Process background tracks and reduce volume by 10dB
    processed = [adjust_loudness(track, -23.0).apply_gain(-10) for track in bg_tracks]
    
    # Merge and adjust background music to match guide audio length
    bg_music = adjust_loudness(merge_background_tracks(processed, len(guide_audio)), -23.0)
    
    # Overlay background music with guide audio
    return guide_audio.overlay(bg_music)


def generate_workout_guide_audio(
    instructions: List[Tuple[str, int]], 
    lang: str = "en", 
    background_urls: Optional[List[str]] = None, 
    output_path: Optional[str] = None
) -> io.BytesIO:
    """Generate complete workout guide audio with optional background music.
    
    Args:
        instructions: List of (instruction_text, duration_in_seconds) tuples
        lang: Language code for TTS
        background_urls: Optional list of YouTube URLs for background music
        output_path: Optional path to save the output MP3 file
        
    Returns:
        BytesIO buffer containing the workout guide audio in MP3 format
    """
    guide_audio = assemble_workout_audio(instructions, lang)
    
    if background_urls:
        guide_audio = integrate_continuous_background(guide_audio, background_urls)
    
    # Export to buffer
    output_buffer = io.BytesIO()
    guide_audio.export(output_buffer, format="mp3", bitrate="192k")
    output_buffer.seek(0)
    
    # Export to file if path provided
    if output_path:
        guide_audio.export(output_path, format="mp3", bitrate="192k")
    
    return output_buffer 