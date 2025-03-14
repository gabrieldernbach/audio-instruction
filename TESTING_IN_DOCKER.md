# Running Tests in Docker

This project supports running tests in Docker to ensure a consistent testing environment regardless of the local setup. This guide explains how to run the tests in Docker and how to configure VSCode/Cursor to always use Docker for testing.

## Quick Start

### Running the YouTube Download Test

To quickly test the YouTube download functionality in Docker:

```bash
./run_yt_test_docker.sh
```

This script accepts an optional YouTube URL argument:

```bash
./run_yt_test_docker.sh "https://www.youtube.com/watch?v=your_video_id"
```

### Running All Tests

To run all tests in Docker:

```bash
./.vscode/docker_test.sh
```

### Running Specific Tests

To run specific test files or directories:

```bash
./.vscode/docker_test.sh tests/test_audio_download.py
```

You can also pass pytest arguments:

```bash
./.vscode/docker_test.sh -v tests/test_audio_download.py::TestYouTubeDownload::test_fetch_background_tracks
```

## VSCode/Cursor Configuration

This project includes VSCode/Cursor configuration to make running tests in Docker seamless:

1. **Run Tests Using VSCode Test Explorer**:
   - The project is configured to run pytest in Docker when you use the VSCode Test Explorer.
   - Open the Test Explorer sidebar in VSCode and click the play button next to any test.

2. **Run Tasks**:
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac) and select "Tasks: Run Task"
   - Choose from one of the following tasks:
     - "Run All Tests in Docker"
     - "Run YouTube Download Test in Docker"
     - "Run Specific Test in Docker" (will prompt for test path)

## How It Works

The Docker configuration works through the following components:

1. **Dockerfile.test**: Defines the Docker image for testing with all necessary dependencies and optimized yt-dlp configuration.

2. **entrypoint.sh**: A script that handles different test execution modes within the container.

3. **docker_test.sh**: A script that builds the Docker image if needed and runs pytest within the container.

4. **run_yt_test_docker.sh**: A script specifically for running the YouTube download test in Docker.

5. **test_yt_download.py**: A script that tests different methods of downloading audio from YouTube.

6. **VSCode Settings**:
   - `.vscode/settings.json`: Configures pytest to use the Docker script
   - `.vscode/tasks.json`: Defines custom tasks for running tests in Docker

## Optimizations for YouTube Downloads

The Docker testing environment has been optimized for better YouTube download success:

1. **Latest yt-dlp**: The Dockerfile installs the latest version of yt-dlp directly from GitHub releases.

2. **Improved Cache**: A dedicated cache directory improves yt-dlp performance.

3. **Multiple Fallback Methods**: The code includes several fallback methods for downloading YouTube audio if the primary method fails.

4. **Browser Cookie Handling**: The Docker container intelligently handles the lack of browser cookies.

5. **Removal of Pytube**: Due to frequent failures with YouTube's anti-scraping measures, the pytube dependency has been removed in favor of optimized yt-dlp methods.

## Expected Test Behavior

When running the YouTube download tests in Docker, you'll notice:

1. **Missing Chrome Cookies**: The Docker container doesn't have access to your local Chrome cookies, so you'll see warnings about this. The tests are designed to use methods that don't require cookies.

2. **Fallback Methods**: The test will try multiple download methods:
   - Standard yt-dlp method
   - Browser-emulating download with custom headers
   - Direct requests method with simplified parameters
   - Last resort method with minimal quality settings

3. **Some Methods May Fail**: Due to YouTube's anti-scraping measures, some methods may fail. This is expected behavior, and the tests are designed to handle these failures gracefully.

## Troubleshooting

- **Docker Networking**: If you experience network issues in the Docker container, try restarting Docker or ensuring your firewall allows Docker to access the internet.

- **Volume Mounting**: If you're running on Windows, ensure that Docker has permission to mount volumes from your file system.

- **Test Failures**: If tests fail due to YouTube download issues, this may be due to YouTube's anti-scraping measures. The code includes fallback mechanisms to handle these failures in production, but tests may still fail if all download methods are blocked. Try running the test with a different YouTube URL. 