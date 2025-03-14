#!/bin/bash

# Default URL if none provided
URL=${1:-"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}

# Check if the Docker image exists or if Dockerfile.test has changed
if [[ "$(docker images -q audio-instruction-test 2> /dev/null)" == "" ]] || [[ "$(find Dockerfile.test -newer .docker_test_image_built 2> /dev/null)" != "" ]]; then
    echo "Building Docker test image..."
    docker build -t audio-instruction-test -f Dockerfile.test .
    touch .docker_test_image_built
fi

echo "Running YouTube download test in Docker with URL: $URL"
docker run --rm -v "$(pwd):/app" audio-instruction-test --yt-test "$URL" 