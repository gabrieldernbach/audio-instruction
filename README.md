# Audio Instruction

A Python package for generating workout audio guides with text-to-speech instructions and optional background music from YouTube.

## Features

- Generate workout audio guides with text-to-speech instructions
- Add countdown audio between exercises
- Include background music from YouTube URLs (with fallback to instruction-only audio if download fails)
- Normalize audio loudness for consistent volume
- Support for multiple configuration formats (JSON, YAML, plain text)
- CLI for simple usage
- FastAPI web service for integration in other applications (e.g. as a tool for a custom GPT)

## Important Note on YouTube Background Music

Due to YouTube's anti-scraping measures, downloading background music from YouTube URLs may fail. The package will gracefully fall back to instruction-only audio when this happens. For reliable background music, consider:

1. Using locally stored audio files instead of YouTube URLs
2. Using royalty-free music from sources that explicitly allow downloads
3. Running with the `--no-background` flag if you don't need background music

## Installation

### From PyPI

```bash
pip install audio-instruction
```

### From source

```bash
git clone https://github.com/yourusername/audio-instruction.git
cd audio-instruction
pip install -e .
```

### Development setup

```bash
git clone https://github.com/yourusername/audio-instruction.git
cd audio-instruction
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
# Install the package in development mode
pip install -e .
# Install development dependencies
pip install pytest mypy
```

### With Docker

```bash
# Build the Docker image
docker build -t workout-audio-generator .

# Run in API mode (default)
docker run -p 8000:8000 workout-audio-generator

# Or run in CLI mode (process a workout file)
docker run -v $(pwd):/data workout-audio-generator /data/my_workout.json
```

## Requirements

- Python 3.8+
- FFmpeg
- yt-dlp (for YouTube audio download)

## Command Line Usage

Create a workout configuration file in one of the supported formats:

### JSON Format

```json
{
  "language": "en",
  "background_urls": [
    "https://www.youtube.com/watch?v=YOUTUBE_ID"
  ],
  "instructions": [
    {
      "text": "Warm-up for 2 minutes",
      "duration_seconds": 120
    },
    {
      "text": "Run for 30 seconds",
      "duration_seconds": 30
    },
    {
      "text": "Walk for 1 minute",
      "duration_seconds": 60
    },
    {
      "text": "Cool-down for 2 minutes",
      "duration_seconds": 120
    }
  ]
}
```

### YAML Format (easier to write)

```yaml
language: en
background_urls: https://www.youtube.com/watch?v=YOUTUBE_ID
instructions:
  - Get ready for a workout  # Simple string uses default 30 seconds
  - text: Warm-up for 2 minutes
    duration_seconds: 120
  - text: Run for 30 seconds
    duration_seconds: 30
  - text: Walk for 1 minute
    duration_seconds: 60
  - Cool-down for 2 minutes  # Simple string uses default 30 seconds
```

### Plain Text Format (simplest)

```
# My Workout
# Comments start with # and are ignored
# Default duration is 30 seconds if not specified

Get ready for a workout
Warm-up for 2 minutes | 120
Run for 30 seconds | 30
Walk for 1 minute | 60
Cool-down for 2 minutes | 120
Great job!
```

Then run the CLI:

```bash
audio-instruction workout.json
# Or with YAML
audio-instruction workout.yml
# Or with text
audio-instruction workout.txt
```

By default, the output file will be saved with the same name as the input file but with a `.mp3` extension. You can also specify a custom output path:

```bash
audio-instruction workout.json -o custom_name.mp3
```

Command-line options:
- `-o, --output`: Output MP3 file path (default: same as input file with .mp3 extension)

### Using the CLI with Docker

The Docker image provides a streamlined workflow:

```bash
# Process a workout file (will output to the same directory)
docker run -v $(pwd):/data workout-audio-generator /data/my_workout.json
# This will create my_workout.mp3 in the current directory
```

You can also use it to start the API server:

```bash
docker run -p 8000:8000 workout-audio-generator
# No need for --api flag as it's the default mode
```

## API Usage

Start the API server:

```bash
uvicorn audio_instruction.api.app:app --reload
```

Or using Docker:

```bash
docker run -p 8000:8000 workout-audio-generator
```

Then make requests to the API:

```python
import requests

response = requests.post(
    "http://localhost:8000/workout",
    json={
        "instructions": [
            {"text": "Warm-up for 2 minutes", "duration_seconds": 120},
            {"text": "Run for 30 seconds", "duration_seconds": 30},
            {"text": "Walk for 1 minute", "duration_seconds": 60},
            {"text": "Cool-down for 2 minutes", "duration_seconds": 120}
        ],
        "language": "en",
        "background_urls": ["https://www.youtube.com/watch?v=YOUTUBE_ID"]
    },
    stream=True
)

with open("workout_guide.mp3", "wb") as f:
    for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)
```

## Python Library Usage

```python
from audio_instruction import generate_workout_guide_audio, validate_workout_instructions

# Define workout instructions
instructions = [
    ("Warm-up for 2 minutes", 120),
    ("Run for 30 seconds", 30),
    ("Walk for 1 minute", 60),
    ("Cool-down for 2 minutes", 120)
]

# Validate instructions
validate_workout_instructions(instructions)

# Generate audio with background music
output_buffer = generate_workout_guide_audio(
    instructions=instructions,
    lang="en",
    background_urls=["https://www.youtube.com/watch?v=YOUTUBE_ID"],
    output_path="workout_guide.mp3"
)
```

## Validation Rules

- Instructions must have at least 10 seconds duration
- Instruction text cannot exceed 256 characters
- Total workout duration cannot exceed 4 hours

## Examples

Check the `examples/` directory for more usage examples:
- `examples/sample_workouts/hiit.json`: JSON workout configuration
- `examples/sample_workouts/hiit.yml`: YAML workout configuration (easier to write)
- `examples/sample_workouts/hiit.txt`: Plain text workout (simplest format)
- `examples/basic/generate_workout.py`: Python script to create a Tabata workout

## Testing in Docker

This project supports running tests in Docker to ensure a consistent testing environment.
For details on how to run tests in Docker and how to configure VSCode/Cursor to use Docker for testing, see [TESTING_IN_DOCKER.md](TESTING_IN_DOCKER.md).

## Deployment to Google Cloud Run

See `examples/deployment/cloud_run_tutorial.md` for detailed deployment instructions.

## Publishing the Docker Image

To publish the Docker image to a container registry:

```bash
# Tag the image with your registry
docker tag workout-audio-generator username/workout-audio-generator:latest

# Push to Docker Hub
docker push username/workout-audio-generator:latest

# Or push to Google Container Registry
docker tag workout-audio-generator gcr.io/project-id/workout-audio-generator:latest
docker push gcr.io/project-id/workout-audio-generator:latest
```

## License

MIT License 