#!/usr/bin/env python3
"""
Basic example of generating a workout audio guide.

This script demonstrates how to use the audio_instruction package to create
a custom workout audio guide with text-to-speech instructions and background music.
"""
import json
import os
import sys
from typing import List, Tuple

# Make sure we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from audio_instruction import (
    ValidationError,
    generate_workout_guide_audio,
    validate_workout_instructions,
)


def create_tabata_workout(rounds: int = 8) -> List[Tuple[str, int]]:
    """Create a Tabata workout with the specified number of rounds.
    
    Tabata is a form of HIIT that consists of:
    - 20 seconds of high intensity exercise
    - 10 seconds of rest
    - Repeated for several rounds
    
    Args:
        rounds: Number of Tabata rounds
        
    Returns:
        List of (instruction_text, duration_in_seconds) tuples
    """
    instructions = [
        ("Get ready for a Tabata workout", 10),
        ("Warm up with light movement for 60 seconds", 60)
    ]
    
    for i in range(1, rounds + 1):
        instructions.extend([
            (f"Round {i}: High intensity exercise for 20 seconds", 20),
            (f"Round {i}: Rest for 10 seconds", 10)
        ])
    
    instructions.append(("Cool down with light stretching", 30))
    instructions.append(("Workout complete, great job!", 10))
    
    return instructions


def main():
    """Main function to demonstrate workout audio generation."""
    print("Generating a Tabata workout audio guide...")
    
    # Create workout instructions
    instructions = create_tabata_workout(rounds=8)
    
    # Display the workout structure
    print("\nWorkout structure:")
    for i, (text, duration) in enumerate(instructions, 1):
        print(f"{i}. {text} ({duration}s)")
    
    total_duration = sum(duration for _, duration in instructions)
    print(f"\nTotal workout duration: {total_duration // 60}m {total_duration % 60}s")
    
    try:
        # Validate instructions
        validate_workout_instructions(instructions)
        
        # Define background music
        background_urls = [
            "https://www.youtube.com/watch?v=eaFhB6E6JKo"  # Example URL, replace with your own
        ]
        
        # Generate the workout audio
        output_path = "tabata_workout.mp3"
        print(f"\nGenerating audio to {output_path}...")
        
        generate_workout_guide_audio(
            instructions=instructions,
            lang="en",
            background_urls=background_urls,
            output_path=output_path
        )
        
        print(f"Done! Workout audio saved to: {os.path.abspath(output_path)}")
        print("You can play it with any media player that supports MP3 files.")
        
    except ValidationError as e:
        print(f"Error validating workout instructions: {e}")
    except Exception as e:
        print(f"Error generating workout audio: {e}")
    

if __name__ == "__main__":
    main()