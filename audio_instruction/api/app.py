"""FastAPI application for audio instruction generation."""
import io
import logging
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from audio_instruction.api.models import (
    ErrorResponse,
    WorkoutGuideRequest,
    convert_request_to_core_format,
)
from audio_instruction.core.validation import ValidationError
from audio_instruction.core.workout import generate_workout_guide_audio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Audio Instruction API",
    description="API for generating workout audio guides with text-to-speech instructions",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle validation errors from the core library."""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."},
    )

# API routes
@app.post(
    "/workout", 
    summary="Generate workout audio guide",
    description="Generate a workout audio guide with text-to-speech instructions and optional background music",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "Workout audio guide in MP3 format",
            "content": {"audio/mpeg": {}}
        },
        400: {
            "model": ErrorResponse,
            "description": "Validation error"
        },
        500: {
            "model": ErrorResponse,
            "description": "Server error"
        }
    }
)
async def generate_workout_guide(request: WorkoutGuideRequest):
    """Generate a workout audio guide."""
    try:
        # Convert request model to core parameters
        instructions, language, background_urls = convert_request_to_core_format(request)
        
        # Generate audio
        logger.info(f"Generating workout guide with {len(instructions)} instructions")
        audio_buffer = generate_workout_guide_audio(
            instructions=instructions,
            lang=language,
            background_urls=background_urls
        )
        
        # Return audio as streaming response
        return StreamingResponse(
            audio_buffer,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=workout_guide.mp3"
            }
        )
    except ValidationError as e:
        # This would be caught by the validation_exception_handler
        raise
    except Exception as e:
        # Unexpected errors
        logger.error(f"Error generating workout guide: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating workout guide: {str(e)}"
        )

@app.get("/health", summary="Health check endpoint")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok"} 