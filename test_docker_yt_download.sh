#!/bin/bash

# Default YouTube URL if none provided
DEFAULT_URL="https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Process arguments
VARIATIONS=""
URL=""
OTHER_ARGS=""

for arg in "$@"; do
    if [[ "$arg" == "--variations" ]]; then
        VARIATIONS="--variations"
    elif [[ "$arg" == http* ]]; then
        URL="$arg"
    else
        OTHER_ARGS="$OTHER_ARGS $arg"
    fi
done

# If no URL was provided, use the default
if [ -z "$URL" ]; then
    URL="$DEFAULT_URL"
fi

# Check if Docker image exists or Dockerfile.test has changed
if [[ ! "$(docker images -q audio-instruction-test 2> /dev/null)" || \
      "$(stat -c %Y Dockerfile.test 2>/dev/null || stat -f %m Dockerfile.test 2>/dev/null)" > \
      "$(docker inspect -f '{{.Created}}' audio-instruction-test 2>/dev/null | date -f - +%s 2>/dev/null || echo 0)" ]]; then
    echo "Building Docker test image..."
    docker build -t audio-instruction-test -f Dockerfile.test .
fi

echo "Testing yt-dlp in Docker without local cookies"
echo "URL: $URL"
echo "Options: $VARIATIONS $OTHER_ARGS"
echo "=============================================="

# Run the test in Docker
docker run --rm -v "$(pwd):/app" audio-instruction-test python3 /app/test_docker_yt_download.py "$URL" $VARIATIONS $OTHER_ARGS

exit_code=$?
echo "=============================================="
if [ $exit_code -eq 0 ]; then
    echo "✅ Test completed successfully!"
else
    echo "❌ Test failed with exit code $exit_code"
fi 