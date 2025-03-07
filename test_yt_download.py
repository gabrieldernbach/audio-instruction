#!/usr/bin/env python3
"""Test script for YouTube download functionality using yt-dlp."""

import glob
import os
import subprocess
import sys
import time
from pathlib import Path


def test_download(url, output_path):
    """Test downloading a YouTube video and converting to MP3.
    
    Args:
        url: YouTube URL to download
        output_path: Path to save the output file
    
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"Testing download from {url}")
    print(f"Output will be saved to {output_path}")
    
    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Run yt-dlp with verbose output to see what's happening
        cmd = [
            "yt-dlp", 
            "-v",  # Verbose output
            "-x",  # Extract audio
            "--audio-format", "mp3", 
            "--audio-quality", "192K", 
            "-o", output_path, 
            url
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Print output for debugging
        print("=== STDOUT ===")
        print(result.stdout)
        print("=== STDERR ===")
        print(result.stderr)
        
        # Handle template in output path
        if "%(ext)s" in output_path:
            # Replace with actual extension
            actual_path = output_path.replace("%(ext)s", "mp3")
            print(f"Looking for file at {actual_path}")
        else:
            actual_path = output_path
        
        # Check if file exists and has size > 0
        if os.path.exists(actual_path) and os.path.getsize(actual_path) > 0:
            print(f"Success! File downloaded to {actual_path} (size: {os.path.getsize(actual_path)} bytes)")
            return True
        else:
            print(f"File not found at {actual_path}, checking directory...")
            # Try to find any MP3 files in the directory
            mp3_files = glob.glob(os.path.join(output_dir, "*.mp3"))
            if mp3_files:
                print(f"Found MP3 files: {mp3_files}")
                return True
            else:
                print(f"Error: No MP3 files found in {output_dir}")
                return False
            
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        print("=== STDOUT ===")
        print(e.stdout)
        print("=== STDERR ===")
        print(e.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def main():
    """Main entry point for the script."""
    # Default values
    url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # "Me at the zoo" - first YouTube video (short)
    output_path = "tmp/downloaded_audio.%(ext)s"
    
    # Allow overriding from command line
    if len(sys.argv) > 1:
        url = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    
    # Run the test
    success = test_download(url, output_path)
    
    # Wait a moment to ensure all output is printed
    time.sleep(1)
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 