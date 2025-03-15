#!/usr/bin/env python3
"""Script to clean up original test files after consolidation."""

import argparse
import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# List of original test files that have been consolidated
ORIGINAL_TEST_FILES = [
    "test_api.py",
    "test_audio_download.py",
    "test_audio_normalization.py",
    "test_cli_file_formats.py",
    "test_countdown_audio.py",
    "test_download_fallback.py",
    "test_multiple_backgrounds.py",
    "test_workout_audio_merging.py",
    "test_yt_download.py",
    "test_validation.py",
]

# List of new consolidated test files
CONSOLIDATED_TEST_FILES = [
    "test_audio_processing.py",
    "test_media_download.py",
    "test_workout_generation.py",
    "test_interfaces.py",
    "run_tests.py",
    "__init__.py",
]


def cleanup_files(dry_run=True):
    """Remove original test files that have been consolidated.
    
    Args:
        dry_run: If True, only print files that would be removed without actually removing them.
    
    Returns:
        int: Number of files removed or that would be removed.
    """
    tests_dir = Path(__file__).parent
    count = 0
    
    # Check that all consolidated files exist
    for filename in CONSOLIDATED_TEST_FILES:
        file_path = tests_dir / filename
        if not file_path.exists():
            logger.error(f"Consolidated file {filename} does not exist. Aborting cleanup.")
            return 0
    
    # Remove original files
    for filename in ORIGINAL_TEST_FILES:
        file_path = tests_dir / filename
        if file_path.exists():
            if dry_run:
                logger.info(f"Would remove: {file_path}")
            else:
                try:
                    os.remove(file_path)
                    logger.info(f"Removed: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to remove {file_path}: {e}")
                    continue
            count += 1
    
    return count


def main():
    """Parse arguments and run cleanup."""
    parser = argparse.ArgumentParser(description="Clean up original test files after consolidation")
    parser.add_argument('--execute', action='store_true', 
                        help='Actually remove files (default is dry run)')
    args = parser.parse_args()
    
    dry_run = not args.execute
    
    if dry_run:
        logger.info("Running in dry-run mode. No files will be removed.")
        logger.info("Use --execute to actually remove files.")
    
    count = cleanup_files(dry_run=dry_run)
    
    if dry_run:
        logger.info(f"Would remove {count} files.")
    else:
        logger.info(f"Removed {count} files.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 