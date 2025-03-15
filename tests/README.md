# Audio Instruction Test Suite

This directory contains the test suite for the audio-instruction package. The tests are organized into logical groups to improve maintainability and readability.

## Test Organization

The test suite is organized into the following modules:

1. **test_audio_processing.py** - Tests for audio processing functionality
   - Audio normalization
   - Countdown audio generation
   - Workout audio merging

2. **test_media_download.py** - Tests for media download functionality
   - YouTube download
   - Download fallback mechanisms
   - Background track fetching

3. **test_workout_generation.py** - Tests for workout generation and validation
   - Instruction validation
   - Multiple background support
   - End-to-end workout generation

4. **test_interfaces.py** - Tests for API and CLI interfaces
   - FastAPI endpoints
   - CLI file format handling
   - Command-line argument processing

## Running Tests

You can run the tests using the provided `run_tests.py` script:

```bash
# Run all tests
python3 run_tests.py

# Run with verbose output
python3 run_tests.py -v

# Run tests matching a specific pattern
python3 run_tests.py -p "test_audio*.py"
```

## Test Data

Test data files are stored in the `test_data` directory.

## Cleanup

If you want to remove the original test files after consolidation, you can use the `cleanup_old_tests.py` script:

```bash
# Dry run (shows what would be removed)
python3 cleanup_old_tests.py

# Actually remove the files
python3 cleanup_old_tests.py --execute
``` 