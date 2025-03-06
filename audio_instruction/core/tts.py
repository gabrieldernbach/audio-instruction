"""Text-to-speech functionality for audio instruction generation."""
import io
from functools import lru_cache
from typing import Optional

from gtts import gTTS
from pydub import AudioSegment


@lru_cache(maxsize=None)
def generate_tts_audio(text: str, lang: str = "en") -> AudioSegment:
    """Convert text to AudioSegment using gTTS.
    
    Args:
        text: The text to convert to speech
        lang: The language code (default: "en")
        
    Returns:
        AudioSegment containing the speech
    """
    try:
        buffer = io.BytesIO()
        gTTS(text=text, lang=lang).write_to_fp(buffer)
        buffer.seek(0)
        return AudioSegment.from_file(buffer, format="mp3")
    except Exception as e:
        # Log failure but return silent segment to not break workflow
        import logging
        logging.error(f"TTS generation failed for text: {text}. Error: {e}")
        return AudioSegment.silent(duration=1000)


@lru_cache(maxsize=None)
def create_countdown_audio(start: int = 5, end: int = 1, tick_duration_ms: int = 1000, lang: str = "en") -> AudioSegment:
    """Create a countdown audio clip with spoken numbers and silence padding.
    
    Args:
        start: The number to start counting down from
        end: The number to end counting down at
        tick_duration_ms: Duration in ms for each number in the countdown
        lang: The language code for TTS
        
    Returns:
        AudioSegment containing the countdown
    """
    # Create countdown segments
    countdown_segments = []
    for number in range(start, end - 1, -1):
        # Generate speech for the number
        number_audio = generate_tts_audio(str(number), lang)
        # Add silence to reach the desired tick duration
        silence_duration = max(0, tick_duration_ms - len(number_audio))
        segment = number_audio + AudioSegment.silent(duration=silence_duration)
        countdown_segments.append(segment)
    
    # Combine all segments
    combined_audio = AudioSegment.empty()
    for segment in countdown_segments:
        combined_audio += segment
    
    return combined_audio


@lru_cache(maxsize=None)
def build_instruction_audio(instruction: str, total_duration: float, lang: str = "en") -> AudioSegment:
    """Build instruction audio with speech, pause, and countdown.
    
    Args:
        instruction: Text instruction to convert to speech
        total_duration: Total duration of the instruction segment in seconds
        lang: Language code for TTS
        
    Returns:
        AudioSegment with instruction followed by pause and countdown
    """
    speech = generate_tts_audio(instruction, lang)
    countdown = create_countdown_audio(lang=lang)
    # Calculate pause to fit the total duration
    pause_duration = int(max(0, total_duration * 1000 - len(speech) - len(countdown)))
    pause = AudioSegment.silent(duration=pause_duration)
    return speech + pause + countdown 