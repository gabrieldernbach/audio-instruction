"""Audio Instruction Test Suite."""

from tests.test_audio_processing import (
    TestAudioNormalization,
    TestCountdownAudio,
    TestWorkoutAudioMerging,
)
from tests.test_interfaces import TestAPI, TestCLIFileFormats
from tests.test_media_download import (
    TestBackgroundTracks,
    TestDownloadFallback,
    TestYouTubeDownload,
)
from tests.test_workout_generation import TestMultipleBackgrounds, TestValidation
