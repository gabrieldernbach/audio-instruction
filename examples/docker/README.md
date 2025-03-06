# Docker CLI Examples

This directory contains examples for running audio-instruction using Docker.

## Prerequisites

- Docker installed on your system
- A workout configuration file in JSON, YAML, or plain text format

## Building the Docker Image

```bash
cd /path/to/audio-instruction
docker build -t workout-audio-generator .
```

## Basic Usage

The Docker image is designed to be simple to use:

```bash
# Process a workout file and automatically generate an MP3 with the same name
docker run -v $(pwd):/data workout-audio-generator /data/my_workout.json
```

This will:
1. Read `/data/my_workout.json` from your local directory
2. Process it to create a workout audio guide
3. Save the output as `/data/my_workout.mp3` in the same directory

You can use any of these formats:
- JSON: `docker run -v $(pwd):/data workout-audio-generator /data/workout.json`
- YAML: `docker run -v $(pwd):/data workout-audio-generator /data/workout.yml`
- TXT: `docker run -v $(pwd):/data workout-audio-generator /data/workout.txt`

## Example Workout File Formats

### JSON Format
```json
{
  "language": "en",
  "background_urls": ["https://www.youtube.com/watch?v=xAP8CSMEwZ8"],
  "instructions": [
    {"text": "Warm-up", "duration_seconds": 60},
    {"text": "Exercise 1", "duration_seconds": 30},
    {"text": "Rest", "duration_seconds": 15},
    {"text": "Cool-down", "duration_seconds": 60}
  ]
}
```

### YAML Format (easier to write)
```yaml
language: en
background_urls: https://www.youtube.com/watch?v=xAP8CSMEwZ8
instructions:
  - Warm-up  # Uses default 30 seconds
  - text: Exercise 1
    duration_seconds: 30
  - text: Rest
    duration_seconds: 15
  - text: Cool-down
    duration_seconds: 60
```

### Plain Text Format (simplest)
```
# Simple workout
# Comments start with # and are ignored

Warm-up | 60
Exercise 1 | 30
Rest | 15
Cool-down | 60
Great job!  # Default 30 seconds
```

## Running the API Server

The Docker image can also run the FastAPI server:

```bash
# API mode is the default if no file is specified
docker run -p 8000:8000 workout-audio-generator
```

## Quick Docker Workflow Examples

### Create a Simple Workout

1. Create a file named `quick.txt` with the following content:
```
Warm up | 60
Push-ups | 30
Rest | 15
Squats | 30
Rest | 15
Cool down | 60
```

2. Run the Docker container:
```bash
docker run -v $(pwd):/data workout-audio-generator /data/quick.txt
```

3. Play the resulting `quick.mp3` file

### Using with Multiple Files

Process several workout files in one go:

```bash
# Create a directory for your workouts
mkdir -p my_workouts
# Create several workout files in that directory

# Process them all with a bash loop
for file in my_workouts/*.txt; do
  docker run -v $(pwd):/data workout-audio-generator /data/$file
done
```

## Publishing the Docker Image

To push the image to a container registry:

```bash
# Login to Docker Hub
docker login

# Tag the image
docker tag workout-audio-generator username/workout-audio-generator:latest

# Push to Docker Hub
docker push username/workout-audio-generator:latest
```

## Using the Published Image

Once published, you can use the image directly without building:

```bash
docker run -v $(pwd):/data username/workout-audio-generator /data/my_workout.json
```

## Troubleshooting

If you encounter any issues:

1. Make sure your configuration file is valid
2. Check that the volume mount paths are correct
3. Ensure you have internet access for downloading YouTube audio
4. Verify that you have permission to write to the current directory 