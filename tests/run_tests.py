#!/usr/bin/env python3
"""Test runner for the audio-instruction package."""

import argparse
import logging
import os
import sys
import unittest
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_tests(verbosity=2, pattern=None):
    """Run the test suite with the specified verbosity and pattern."""
    logger.info("Running audio-instruction test suite")
    
    if pattern:
        logger.info(f"Using test pattern: {pattern}")
    
    # Get the tests directory
    tests_dir = Path(__file__).parent
    
    # Discover and run tests
    loader = unittest.TestLoader()
    
    if pattern:
        suite = loader.discover(str(tests_dir), pattern=pattern)
    else:
        suite = loader.discover(str(tests_dir))
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # Return appropriate exit code
    return 0 if result.wasSuccessful() else 1


def main():
    """Parse arguments and run tests."""
    parser = argparse.ArgumentParser(description="Run audio-instruction tests")
    parser.add_argument('-v', '--verbose', action='store_true', help='Increase output verbosity')
    parser.add_argument('-p', '--pattern', type=str, help='Pattern to match test files (e.g., "test_*.py")')
    args = parser.parse_args()
    
    verbosity = 3 if args.verbose else 2
    
    sys.exit(run_tests(verbosity=verbosity, pattern=args.pattern))


if __name__ == "__main__":
    main() 