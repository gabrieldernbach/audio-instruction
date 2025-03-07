FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    wget \
    curl \
    gnupg \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install yt-dlp - use the latest version
RUN pip install --no-cache-dir --upgrade yt-dlp

# Create tmp directory for YouTube downloads
RUN mkdir -p /app/tmp && chmod 777 /app/tmp

# Copy only necessary files (exclude tmp directory)
COPY audio_instruction/ /app/audio_instruction/
COPY examples/ /app/examples/
COPY pyproject.toml setup.py README.md /app/

# Install the package and dependencies from pyproject.toml
RUN pip install --no-cache-dir -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create a simple entrypoint script
RUN echo '#!/bin/bash\n\
if [[ "$1" == "--api" ]]; then\n\
  # Start the API server\n\
  shift\n\
  exec uvicorn audio_instruction.api.app:app --host 0.0.0.0 --port 8000 "$@"\n\
else\n\
  # If first argument is a path, process it as a config file\n\
  if [[ -f "$1" ]]; then\n\
    # Get the directory of the input file\n\
    input_dir=$(dirname "$1")\n\
    # Get just the filename without path\n\
    input_file=$(basename "$1")\n\
    # Get filename without extension\n\
    filename_base="${input_file%.*}"\n\
    # Create a symlink to the input file in our /app directory\n\
    ln -sf "$1" "/app/$input_file"\n\
    # Run the CLI tool with the input file (let it auto-name the output)\n\
    cd /app\n\
    audio-instruction "/app/$input_file"\n\
    # Copy the output back to the same directory as the input\n\
    cp "/app/${filename_base}.mp3" "$input_dir/${filename_base}.mp3"\n\
    # Show success message\n\
    echo "Generated audio saved to $input_dir/${filename_base}.mp3"\n\
  else\n\
    # Use as normal CLI\n\
    exec audio-instruction "$@"\n\
  fi\n\
fi' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Make sure the entrypoint script is using Unix line endings
RUN sed -i 's/\r$//' /app/entrypoint.sh

# Expose the port for API mode
EXPOSE 8000

# Set the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command (for API mode)
CMD ["--api"] 